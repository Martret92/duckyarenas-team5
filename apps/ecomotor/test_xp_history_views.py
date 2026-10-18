"""S10-A: HTTP real sobre S4-A, sin configuración ni datos de producción."""

from dataclasses import replace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, OperationalError, connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, include, path, resolve, reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, views
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold,
    Specialization, StatAllocationEvent, UserSpecializationProgress, XPEvent,
)
from .progress_queries import (
    InvalidHistoryParametersError, InvalidQueryProfileError, ProgressQueryDatabaseError,
    list_progress_history,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


urlpatterns = [path("test-ecomotor/", include("apps.ecomotor.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class XPHistoryViewTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s10-web-owner")
        self.other = create_xp_profile(username="s10-other-private")
        UserProfileBank.objects.create(user=self.profile.user)
        self.client.force_login(self.profile.user)
        self.url = reverse("ecomotor:xp-history")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def grant(self, amount=1, key="s10-private-key", profile=None):
        return grant_historical_xp(self.profile if profile is None else profile, amount, key)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, StatAllocationEvent, UserSpecializationProgress,
            Specialization, LevelThreshold, EvolutionStage,
        )]

    def test_authenticated_200_correct_template_and_empty_state(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecomotor/xp_history.html")
        self.assertTemplateUsed(response, "ecomotor/base.html")
        self.assertContains(response, "Historial de XP y evoluciones")
        self.assertContains(response, "Todavía no tienes concesiones de XP registradas.")
        self.assertNotContains(response, "Ver concesiones anteriores")
        self.assertContains(response, reverse("ecomotor:progress"))

    def test_anonymous_standard_login_with_next(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).path, urlsplit(settings.LOGIN_URL).path)
        self.assertEqual(parse_qs(urlsplit(response.url).query)["next"], [self.url])

    @override_settings(LOGIN_URL="/s10-configured-login/")
    def test_login_destination_is_configurable(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).url, "/s10-configured-login/?next=" + self.url)

    def test_user_without_profile_404_without_initialization(self):
        user = get_user_model().objects.create(username="s10-no-profile")
        self.client.force_login(user)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.snapshot(), before)

    def test_head_has_get_status_without_body(self):
        self.grant(17)
        response = self.client.head(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(self.client.head(self.url, {"before_id": "0"}).status_code, 400)

    def test_unsafe_methods_405_and_no_changes(self):
        before = self.snapshot()
        for method in ("post", "put", "patch", "delete", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["Allow"], "GET, HEAD")
        self.assertEqual(self.snapshot(), before)

    def test_client_identifiers_cannot_choose_owner_or_reveal_other_events(self):
        own = self.grant(17)
        other = self.grant(102, "other-private-operation", self.other)
        params = {"profile_id": self.other.pk, "user_id": self.other.user_id,
                  "username": self.other.user.username, "recipient_id": self.other.user_id}
        response = self.client.get(self.url, params)
        self.assertEqual([e.id for e in response.context["history"].entries], [own.xp_event_id])
        self.assertNotContains(response, f"Concesión #{other.xp_event_id}<")
        for evolution in EvolutionEvent.objects.filter(profile=self.other):
            self.assertNotContains(response, f"Evolución #{evolution.pk};")
        self.assertNotContains(response, self.other.user.username)
        self.client.force_login(self.other.user)
        response = self.client.get(self.url, {"profile_id": self.profile.pk})
        self.assertEqual([e.id for e in response.context["history"].entries], [other.xp_event_id])

    def test_real_s3_grant_displays_exact_snapshots(self):
        result = self.grant(23)
        event = XPEvent.objects.get(pk=result.xp_event_id)
        response = self.client.get(self.url)
        entry = response.context["history"].entries[0]
        self.assertEqual((entry.amount, entry.xp_before, entry.xp_after, entry.created_at),
                         (event.amount, event.xp_before, event.xp_after, event.created_at))
        self.assertContains(response, f"Concesión #{event.pk}")
        self.assertContains(response, '<dt>XP concedida</dt><dd>+23</dd>', html=True)
        self.assertContains(response, '<dt>XP anterior</dt><dd>0</dd>', html=True)
        self.assertContains(response, '<dt>XP posterior</dt><dd>23</dd>', html=True)

    def test_stable_pages_ten_entries_without_duplicates_or_gaps(self):
        ids = [self.grant(1, f"s10-page-{n}").xp_event_id for n in range(23)]
        collected = []
        cursor = None
        for expected_size in (10, 10, 3):
            response = self.client.get(self.url, {} if cursor is None else {"before_id": cursor})
            page = response.context["history"]
            self.assertEqual(len(page.entries), expected_size)
            collected.extend(entry.id for entry in page.entries)
            if page.has_more:
                self.assertEqual(page.next_before_id, page.entries[-1].id)
                self.assertContains(response, f'{self.url}?before_id={page.next_before_id}')
                self.assertContains(response, "Ver concesiones anteriores")
            else:
                self.assertIsNone(page.next_before_id)
                self.assertNotContains(response, "Ver concesiones anteriores")
            self.assertContains(response, "Volver al inicio del historial")
            cursor = page.next_before_id
        self.assertEqual(collected, ids[::-1])

    def test_exact_ten_entries_do_not_advertise_another_page(self):
        for n in range(10):
            self.grant(1, f"s10-exact-{n}")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["history"].entries), 10)
        self.assertNotContains(response, "Ver concesiones anteriores")

    def test_cursor_is_exclusive_and_can_return_no_results(self):
        first = self.grant(1, "first").xp_event_id
        second = self.grant(1, "second").xp_event_id
        response = self.client.get(self.url, {"before_id": second})
        self.assertEqual([e.id for e in response.context["history"].entries], [first])
        response = self.client.get(self.url, {"before_id": first})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["history"].entries, ())

    def test_invalid_http_cursors_are_rejected_before_service(self):
        for value in ("", "0", "-1", "+1", "1.0", "1e2", " 1", "1 ", "١", "１２",
                      str(2**63), "9" * 5000):
            with self.subTest(value=value[:30]), patch.object(views, "list_progress_history") as query:
                response = self.client.get(self.url, {"before_id": value})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content.decode(), "El cursor del historial no es válido.")
                query.assert_not_called()

    def test_duplicate_cursors_even_identical_are_rejected(self):
        for query_string in ("?before_id=1&before_id=2", "?before_id=1&before_id=1"):
            with patch.object(views, "list_progress_history") as query:
                self.assertEqual(self.client.get(self.url + query_string).status_code, 400)
                query.assert_not_called()

    def test_evolutions_grouped_under_cause_in_persisted_order(self):
        first = self.grant(51, "several-evolutions")
        second = self.grant(1, "no-evolution")
        response = self.client.get(self.url)
        latest, older = response.context["history"].entries
        self.assertEqual(latest.id, second.xp_event_id)
        self.assertEqual(latest.evolutions, ())
        expected = list(EvolutionEvent.objects.filter(xp_event_id=first.xp_event_id).order_by("pk"))
        self.assertEqual([e.id for e in older.evolutions], [e.pk for e in expected])
        text = response.content.decode()
        positions = []
        for event in expected:
            reference = f"Evolución #{event.pk}; referencia de etapa {event.stage_id}; evento XP causal {event.xp_event_id}."
            positions.append(text.index(reference))
        self.assertEqual(positions, sorted(positions))

    def test_grant_without_evolution_does_not_invent_references(self):
        self.grant()
        response = self.client.get(self.url)
        self.assertNotContains(response, "Evoluciones registradas")
        self.assertNotContains(response, "referencia de etapa")

    def test_history_survives_catalog_changes_and_later_grants(self):
        self.grant(17, "historical")
        original = list_progress_history(self.profile).entries[0]
        self.grant(85, "later")
        EvolutionStage.objects.filter(ordinal=2).update(code="<script>private</script>", name="private-new-name")
        LevelThreshold.objects.all().delete()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["history"].entries[-1], original)
        self.assertNotContains(response, "private-new-name")
        self.assertNotContains(response, "private</script>")
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn('"ecomotor_evolutionstage"', sql)
        self.assertNotIn('"ecomotor_levelthreshold"', sql)

    def test_operation_keys_and_profile_fields_are_not_rendered(self):
        self.grant(17, "<script>s10-private-operation</script>")
        response = self.client.get(self.url)
        for private in ("s10-private-operation", "operation_key", "profile_id", "user_id", self.profile.user.username):
            self.assertNotContains(response, private)

    def test_template_keeps_autoescaping_for_display_values(self):
        self.grant()
        history = list_progress_history(self.profile)
        # Defensa de presentación con texto de prueba; S4-A valida los tipos persistidos.
        injected = replace(history, entries=(replace(history.entries[0], id="<script>test</script>"),))
        with patch.object(views, "list_progress_history", return_value=injected):
            response = self.client.get(self.url)
        self.assertContains(response, "&lt;script&gt;test&lt;/script&gt;")
        self.assertNotContains(response, "<script>test</script>")

    def test_partial_and_structurally_invalid_profiles_409(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertNotContains(response, "CharacterStats", status_code=409)
        self.client.force_login(self.other.user)
        UserProfileEcomotor.objects.filter(pk=self.other.pk).update(current_stage_code="x" * 33)
        self.assertEqual(self.client.get(self.url).status_code, 409)

    def test_inconsistent_historical_event_409(self):
        result = self.grant()
        XPEvent.objects.filter(pk=result.xp_event_id).update(operation_key="x" * 256)
        self.assertEqual(self.client.get(self.url).status_code, 409)

    def test_causally_incompatible_evolution_409(self):
        result = self.grant(17)
        EvolutionEvent.objects.filter(xp_event_id=result.xp_event_id).update(profile=self.other)
        for profile in (self.profile, self.other):
            self.client.force_login(profile.user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.content.decode(), "El historial no puede consultarse en su estado actual.")

    def test_profile_disappearing_during_query_404(self):
        with patch.object(views, "list_progress_history", side_effect=InvalidQueryProfileError):
            self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_service_parameter_error_maps_to_400(self):
        with patch.object(views, "list_progress_history", side_effect=InvalidHistoryParametersError):
            self.assertEqual(self.client.get(self.url).status_code, 400)

    def test_database_failures_503_safe_at_lookup_and_service(self):
        with patch.object(UserProfileEcomotor.objects, "get", side_effect=DatabaseError("private SQL")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "private SQL", status_code=503)
        for error in (DatabaseError("private SQL"), ProgressQueryDatabaseError("private SQL")):
            with patch.object(views, "list_progress_history", side_effect=error):
                self.assertEqual(self.client.get(self.url).status_code, 503)
        def broken(execute, sql, params, many, context):
            if '"ecomotor_xpevent"' in sql:
                raise OperationalError("private SQL")
            return execute(sql, params, many, context)
        with connection.execute_wrapper(broken):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "private SQL", status_code=503)

    def test_programming_errors_not_disguised(self):
        with patch.object(views, "list_progress_history", side_effect=RuntimeError("test bug")), \
                self.assertRaisesRegex(RuntimeError, "test bug"):
            self.client.get(self.url)

    def test_get_head_only_select_and_no_writers_or_overview(self):
        self.grant(51)
        before = self.snapshot()
        with patch("apps.ecomotor.initialization.ensure_ecomotor_initialized", side_effect=AssertionError), \
                patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                patch.object(views, "allocate_stat_points", side_effect=AssertionError), \
                patch("apps.ecomotor.reward_rules.evaluate_reward", side_effect=AssertionError), \
                patch.object(views, "get_progress_overview", side_effect=AssertionError), \
                CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.client.head(self.url).status_code, 200)
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
        self.assertEqual(self.snapshot(), before)

    def test_one_public_s4_call_with_own_profile_and_cursor(self):
        result = self.grant()
        with patch.object(views, "list_progress_history", wraps=list_progress_history) as query:
            self.client.get(self.url, {"before_id": result.xp_event_id, "profile_id": self.other.pk, "limit": 100})
        query.assert_called_once()
        args, kwargs = query.call_args
        self.assertEqual(args[0].pk, self.profile.pk)
        self.assertEqual(kwargs, {"limit": 10, "before_id": result.xp_event_id})

    def test_namespace_navigation_and_local_mount_only(self):
        self.assertEqual(resolve(self.url).view_name, "ecomotor:xp-history")
        self.assertEqual(resolve(self.url).func, views.xp_history_view)
        response = self.client.get(self.url)
        self.assertContains(response, f'aria-current="page" href="{self.url}"')
        for name in ("progress", "allocate-points", "allocation-history"):
            target = reverse("ecomotor:" + name)
            self.assertContains(response, target)
            self.assertContains(self.client.get(target), self.url)
        with override_settings(ROOT_URLCONF="config.urls"), self.assertRaises(NoReverseMatch):
            reverse("ecomotor:xp-history")

    def test_progress_keeps_recent_ten_and_links_to_full_history(self):
        for n in range(12):
            self.grant(1, f"recent-{n}")
        response = self.client.get(reverse("ecomotor:progress"))
        self.assertEqual(len(response.context["history"].entries), 10)
        self.assertContains(response, "Ver historial completo de XP")
        self.assertContains(response, self.url)
