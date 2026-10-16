"""HTTP real con URLconf local y parámetros exclusivamente ficticios."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import include, path, resolve, reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, progress_queries, views
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold,
    Specialization, UserSpecializationProgress, XPEvent,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


urlpatterns = [path("test-ecomotor/", include("apps.ecomotor.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class ProgressViewTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="web-test-a")
        self.other = create_xp_profile(username="web-test-b")
        UserProfileBank.objects.create(user=self.profile.user)
        self.client.force_login(self.profile.user)
        self.url = reverse("ecomotor:progress")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, UserSpecializationProgress, LevelThreshold,
            EvolutionStage, Specialization,
        )]

    def grant(self, amount, key="web-test-grant", profile=None):
        return grant_historical_xp(self.profile if profile is None else profile, amount, key)

    def test_authenticated_valid_profile_200_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecomotor/progress.html")

    def test_anonymous_redirect_uses_configured_login_and_next(self):
        self.client.logout()
        response = self.client.get(self.url)
        target = urlsplit(response.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(target.path, urlsplit(settings.LOGIN_URL).path)
        self.assertEqual(parse_qs(target.query)["next"], [self.url])

    @override_settings(LOGIN_URL="/core-login-pending/")
    def test_login_destination_is_not_hardcoded(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.url, "/core-login-pending/?next=" + self.url)

    def test_no_profile_404_without_creation(self):
        user = get_user_model().objects.create(username="web-test-no-profile")
        self.client.force_login(user)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(before, self.snapshot())

    def test_missing_stats_409_without_repair(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        before = self.snapshot()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(before, self.snapshot())
        self.assertNotContains(response, "CharacterStats", status_code=409)

    def test_structurally_invalid_profile_409(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x" * 33)
        self.assertEqual(self.client.get(self.url).status_code, 409)

    def test_state_error_does_not_reveal_details(self):
        with patch.object(views, "get_progress_overview", side_effect=
                          progress_queries.InconsistentQueryStateError("private-user-999 secret")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertNotContains(response, "secret", status_code=409)
        self.assertNotContains(response, "999", status_code=409)

    def test_foreign_get_identifiers_are_ignored(self):
        self.grant(51, profile=self.other)
        response = self.client.get(self.url, {"profile_id": self.other.pk, "user_id": self.other.user_id})
        self.assertEqual(response.context["overview"].profile_id, self.profile.pk)
        self.assertEqual(response.context["overview"].historical_xp_total, 0)
        self.assertEqual(response.context["history"].entries, ())

    def test_each_user_only_sees_own_history(self):
        first = self.grant(11)
        second = self.grant(51, profile=self.other)
        response = self.client.get(self.url)
        self.assertEqual([e.id for e in response.context["history"].entries], [first.xp_event_id])
        self.client.force_login(self.other.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["overview"].profile_id, self.other.pk)
        self.assertEqual([e.id for e in response.context["history"].entries], [second.xp_event_id])

    def test_post_rejected_without_changes(self):
        before = self.snapshot()
        response = self.client.post(self.url, {"profile_id": self.other.pk, "amount": 999})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["Allow"], "GET, HEAD")
        self.assertEqual(before, self.snapshot())

    def test_other_mutating_methods_rejected(self):
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                self.assertEqual(getattr(self.client, method)(self.url).status_code, 405)

    def test_head_is_supported_without_body(self):
        response = self.client.head(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_current_summary_values(self):
        response = self.client.get(self.url)
        self.assertContains(response, "<dt>XP histórica acumulada</dt><dd>0</dd>", html=True)
        self.assertContains(response, "<dt>Nivel actual</dt><dd>1</dd>", html=True)
        self.assertContains(response, XP_CONFIGURATION.ordered_stage_codes[0])

    def test_six_base_stats_render_real_values(self):
        response = self.client.get(self.url)
        for label, value in (("ATK", 2), ("DEF", 3), ("LOG", 4), ("SPE", 6), ("VEL", 7), ("INT", 8)):
            self.assertContains(response, f'<tr><th scope="row">{label}</th><td>{value}</td></tr>', html=True)

    def test_available_points_render(self):
        self.assertContains(self.client.get(self.url),
                            '<tr><th scope="row">Puntos disponibles</th><td>7</td></tr>', html=True)

    def test_render_after_s3_grant(self):
        self.grant(51)
        response = self.client.get(self.url)
        overview = response.context["overview"]
        self.assertEqual((overview.historical_xp_total, overview.current_level, overview.available_points), (51, 4, 14))
        self.assertContains(response, "<dt>XP histórica acumulada</dt><dd>51</dd>", html=True)

    def test_next_level_calculable(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Nivel 2. Umbral XP: 11.")
        self.assertContains(response, "XP restante: 11.")

    def test_next_stage_calculable(self):
        response = self.client.get(self.url)
        self.assertContains(response, f"Etapa {XP_CONFIGURATION.ordered_stage_codes[1]}. Umbral XP: 17.")

    def test_last_level_completed(self):
        self.grant(51)
        self.assertContains(self.client.get(self.url), "último nivel del catálogo actualmente configurado")

    def test_last_stage_completed(self):
        self.grant(102)
        self.assertContains(self.client.get(self.url), "última etapa del catálogo actualmente configurado")

    def test_no_configuration_preserves_basic_and_level(self):
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            response = self.client.get(self.url)
        self.assertContains(response, "La próxima etapa no está disponible para consulta.")
        self.assertContains(response, "Nivel 2. Umbral XP: 11.")
        self.assertContains(response, "<dt>XP histórica acumulada</dt><dd>0</dd>", html=True)
        self.assertNotContains(response, "STAGE_CONFIGURATION_UNAVAILABLE")

    def test_invalid_catalog_unavailable_without_approximation(self):
        LevelThreshold.objects.all().delete()
        response = self.client.get(self.url)
        self.assertContains(response, "El próximo nivel no está disponible para consulta.")
        self.assertNotContains(response, "INVALID_LEVEL_CATALOG")
        self.assertNotContains(response, "Umbral XP: 11")

    def test_empty_history_message(self):
        self.assertContains(self.client.get(self.url), "Aún no hay concesiones de XP registradas.")

    def test_history_newest_first(self):
        first = self.grant(1, "first")
        second = self.grant(2, "second")
        response = self.client.get(self.url)
        self.assertEqual([e.id for e in response.context["history"].entries], [second.xp_event_id, first.xp_event_id])
        text = response.content.decode()
        self.assertLess(text.index(f"Concesión {second.xp_event_id}"), text.index(f"Concesión {first.xp_event_id}"))

    def test_history_maximum_ten_no_web_pagination(self):
        results = [self.grant(1, f"web-{n}") for n in range(12)]
        response = self.client.get(self.url, {"limit": 100, "before_id": results[0].xp_event_id})
        self.assertEqual(len(response.context["history"].entries), 10)
        self.assertEqual(response.context["history"].entries[-1].id, results[2].xp_event_id)
        self.assertEqual(response.content.decode().count("<article>"), 10)
        self.assertNotContains(response, "before_id")

    def test_multiple_evolutions_use_only_persisted_references(self):
        result = self.grant(51)
        response = self.client.get(self.url)
        events = EvolutionEvent.objects.filter(xp_event_id=result.xp_event_id).order_by("pk")
        self.assertEqual(events.count(), 3)
        for event in events:
            self.assertContains(response, f"Referencia de etapa {event.stage_id}; evento XP causal {result.xp_event_id}.")

    def test_original_snapshots_without_historical_reconstruction(self):
        first = self.grant(17, "old")
        self.grant(34, "new")
        EvolutionStage.objects.update(name="not-a-historical-name")
        response = self.client.get(self.url)
        old = next(e for e in response.context["history"].entries if e.id == first.xp_event_id)
        self.assertEqual((old.xp_before, old.xp_after), (0, 17))
        self.assertContains(response, "<dt>XP posterior</dt><dd>17</dd>", html=True)
        self.assertNotContains(response, "not-a-historical-name")
        self.assertNotContains(response, "Nivel anterior")
        self.assertNotContains(response, "Puntos concedidos")

    def test_persisted_stage_html_is_escaped(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="<script>alert(1)</script>")
        response = self.client.get(self.url)
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>")

    def test_operation_key_html_is_not_exposed(self):
        self.grant(1, "<img src=x onerror=alert(1)>")
        self.assertNotContains(self.client.get(self.url), "<img")

    def test_namespace_route_and_no_profile_id(self):
        self.assertEqual(self.url, "/test-ecomotor/progress/")
        match = resolve(self.url)
        self.assertEqual(match.view_name, "ecomotor:progress")
        self.assertEqual(match.kwargs, {})

    def test_production_urlconf_remains_unmounted(self):
        from config.urls import urlpatterns as production_patterns
        self.assertFalse(any(getattr(pattern, "namespace", None) == "ecomotor" for pattern in production_patterns))

    def test_both_real_queries_receive_own_profile_and_fixed_limit(self):
        with patch.object(views, "get_progress_overview", wraps=progress_queries.get_progress_overview) as overview, \
                patch.object(views, "list_progress_history", wraps=progress_queries.list_progress_history) as history:
            self.assertEqual(self.client.get(self.url, {"profile_id": self.other.pk}).status_code, 200)
        overview.assert_called_once()
        history.assert_called_once()
        self.assertEqual(overview.call_args.args[0].pk, self.profile.pk)
        self.assertEqual(history.call_args.args[0].pk, self.profile.pk)
        self.assertEqual(history.call_args.kwargs, {"limit": 10})

    def test_no_initialization_or_grant_calls(self):
        with patch("apps.ecomotor.initialization.ensure_ecomotor_initialized", side_effect=AssertionError), \
                patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError):
            self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_get_has_only_reads_and_preserves_all_records(self):
        self.grant(51)
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(queries)
        for query in queries:
            self.assertTrue(query["sql"].lstrip().upper().startswith("SELECT"), query["sql"])
        self.assertEqual(before, self.snapshot())

    def test_database_errors_in_each_query_are_safe_503(self):
        for function in ("get_progress_overview", "list_progress_history"):
            with self.subTest(function=function), patch.object(views, function, side_effect=
                    progress_queries.ProgressQueryDatabaseError("private database secret")):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 503)
                self.assertNotContains(response, "secret", status_code=503)

    def test_profile_lookup_database_failure_safe_503(self):
        with patch.object(UserProfileEcomotor.objects, "get", side_effect=DatabaseError("private SQL secret")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "secret", status_code=503)

    def test_profile_disappearing_during_either_query_404(self):
        for function in ("get_progress_overview", "list_progress_history"):
            with self.subTest(function=function), patch.object(views, function, side_effect=
                    progress_queries.InvalidQueryProfileError("private missing id")):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 404)
                self.assertNotContains(response, "private", status_code=404)

    def test_inconsistent_history_409(self):
        with patch.object(views, "list_progress_history", side_effect=
                          progress_queries.InconsistentQueryStateError("private causal mismatch")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertNotContains(response, "private", status_code=409)

    def test_programming_errors_are_not_hidden(self):
        with patch.object(views, "get_progress_overview", side_effect=RuntimeError("programming failure")):
            with self.assertRaisesRegex(RuntimeError, "programming failure"):
                self.client.get(self.url)
