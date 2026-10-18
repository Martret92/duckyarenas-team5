"""HTTP real de S9-A, URLconf local y fixtures exclusivamente ficticios."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import include, path, resolve, reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, views
from .models import CharacterStats, StatAllocationEvent, XPEvent, EvolutionEvent, EvolutionStage
from .progress_queries import InconsistentQueryStateError, InvalidQueryProfileError, ProgressQueryDatabaseError
from .stat_allocation import allocate_stat_points
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


urlpatterns = [path("test-ecomotor/", include("apps.ecomotor.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class StatAllocationHistoryViewTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s9-web-a")
        self.other = create_xp_profile(username="s9-web-b-private")
        UserProfileBank.objects.create(user=self.profile.user)
        self.client.force_login(self.profile.user)
        self.url = reverse("ecomotor:allocation-history")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "web-s9-actual")

    def allocate(self, key="s9-secret-key-not-for-html", profile=None):
        return allocate_stat_points(self.profile if profile is None else profile, "atk", 1, key)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, StatAllocationEvent, EvolutionStage,
        )]

    def test_authenticated_template_and_empty_state(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecomotor/allocation_history.html")
        self.assertContains(response, "Todavía no has realizado asignaciones de puntos.")
        self.assertContains(response, reverse("ecomotor:allocate-points"))

    def test_anonymous_uses_standard_login_and_next(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).path, urlsplit(settings.LOGIN_URL).path)
        self.assertEqual(parse_qs(urlsplit(response.url).query)["next"], [self.url])

    @override_settings(LOGIN_URL="/s9-test-login/")
    def test_login_url_is_configurable(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).url, "/s9-test-login/?next=" + self.url)

    def test_user_without_profile_404_no_initialization(self):
        user = get_user_model().objects.create(username="s9-no-profile")
        self.client.force_login(user)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.snapshot(), before)

    def test_partial_profile_409_safe_message(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 409)
        self.assertNotContains(response, "CharacterStats", status_code=409)
        self.assertNotContains(response, self.other.user.username, status_code=409)

    def test_inconsistent_persisted_event_409(self):
        self.allocate()
        StatAllocationEvent.objects.update(stage_code_at_allocation="x" * 33)
        self.assertEqual(self.client.get(self.url).status_code, 409)

    def test_invalid_http_cursors_are_controlled(self):
        for value in ("", "0", "-1", "1.0", "1e2", " 1", "+1", "١", str(2**64), "9" * 5000):
            with self.subTest(value=value[:30]):
                response = self.client.get(self.url, {"before_id": value})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.content.decode(), "El cursor del historial no es válido.")

    def test_duplicate_cursors_rejected(self):
        for query in ("?before_id=1&before_id=2", "?before_id=1&before_id=1"):
            self.assertEqual(self.client.get(self.url + query).status_code, 400)

    def test_database_failures_503_without_details(self):
        for error in (DatabaseError("SQL private payload"), ProgressQueryDatabaseError("SQL private payload")):
            with patch.object(views, "list_stat_allocation_history", side_effect=error):
                response = self.client.get(self.url)
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(b"SQL private payload", response.content)

    def test_disappeared_profile_404(self):
        with patch.object(views, "list_stat_allocation_history", side_effect=InvalidQueryProfileError):
            self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_programming_error_is_not_swallowed(self):
        with patch.object(views, "list_stat_allocation_history", side_effect=RuntimeError), \
                self.assertRaises(RuntimeError):
            self.client.get(self.url)

    def test_only_safe_methods_and_head_without_body(self):
        self.assertEqual(self.client.head(self.url).status_code, 200)
        self.assertEqual(self.client.head(self.url).content, b"")
        for method in ("post", "put", "patch", "delete", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["Allow"], "GET, HEAD")

    def test_foreign_ids_cannot_change_owner_and_private_keys_are_absent(self):
        own = self.allocate()
        grant_historical_xp(self.other, 102, "other-web-actual")
        other = self.allocate("other-web-secret-key", self.other)
        for params in ({"profile_id": self.other.pk}, {"user_id": self.other.user_id}, {}):
            response = self.client.get(self.url, params)
            self.assertEqual([e.id for e in response.context["history"].entries], [own.allocation_event_id])
            self.assertNotContains(response, "s9-secret-key-not-for-html")
            self.assertNotContains(response, "other-web-secret-key")
            self.assertNotContains(response, self.other.user.username)
        self.client.force_login(self.other.user)
        response = self.client.get(self.url, {"profile_id": self.profile.pk})
        self.assertEqual([e.id for e in response.context["history"].entries], [other.allocation_event_id])

    def test_snapshots_rendered_after_later_operations(self):
        first = self.allocate()
        self.allocate("later-web-allocation")
        grant_historical_xp(self.profile, 5, "later-web-xp")
        response = self.client.get(self.url)
        entry = response.context["history"].entries[-1]
        self.assertEqual(entry.available_points_before, first.available_points_before)
        self.assertContains(response, f"{first.attribute_before} → {first.attribute_after}")
        self.assertContains(response, f"{first.available_points_before} → {first.available_points_after}")
        self.assertContains(response, "Código histórico de etapa persistido")

    def test_ten_per_page_with_correct_cursor_and_no_duplicates(self):
        ids = [self.allocate(f"web-page-{n}").allocation_event_id for n in range(12)]
        first = self.client.get(self.url)
        page = first.context["history"]
        self.assertEqual([e.id for e in page.entries], ids[::-1][:10])
        self.assertContains(first, f'{self.url}?before_id={page.next_before_id}')
        self.assertContains(first, "Ver asignaciones anteriores")
        second = self.client.get(self.url, {"before_id": page.next_before_id})
        self.assertEqual([e.id for e in second.context["history"].entries], ids[::-1][10:])
        self.assertNotContains(second, "Ver asignaciones anteriores")
        self.assertContains(second, "Volver al inicio del historial")

    def test_namespace_navigation_and_global_urlconf_unchanged(self):
        self.assertEqual(resolve(self.url).view_name, "ecomotor:allocation-history")
        response = self.client.get(self.url)
        self.assertContains(response, f'aria-current="page" href="{self.url}"')
        for name in ("progress", "allocate-points"):
            self.assertContains(response, reverse("ecomotor:" + name))
            self.assertContains(self.client.get(reverse("ecomotor:" + name)), self.url)
        with override_settings(ROOT_URLCONF="config.urls"):
            from django.urls import NoReverseMatch
            with self.assertRaises(NoReverseMatch):
                reverse("ecomotor:allocation-history")

    def test_historical_code_is_escaped_not_reconstructed(self):
        self.allocate()
        StatAllocationEvent.objects.update(stage_code_at_allocation="<script>x</script>")
        response = self.client.get(self.url)
        self.assertContains(response, "&lt;script&gt;x&lt;/script&gt;")
        self.assertNotContains(response, "<script>x</script>")

    def test_replay_is_single_visible_entry_without_configuration(self):
        self.allocate()
        self.allocate()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            response = self.client.get(self.url)
        self.assertEqual(len(response.context["history"].entries), 1)
        self.assertEqual(response.status_code, 200)

    def test_get_and_head_only_read_and_never_invoke_writers(self):
        self.allocate()
        before = self.snapshot()
        with patch("apps.ecomotor.initialization.ensure_ecomotor_initialized", side_effect=AssertionError), \
                patch.object(views, "allocate_stat_points", side_effect=AssertionError), \
                patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.client.head(self.url).status_code, 200)
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT ") for row in queries))
        self.assertEqual(self.snapshot(), before)

    def test_public_query_called_once_for_authenticated_profile(self):
        with patch.object(views, "list_stat_allocation_history", wraps=views.list_stat_allocation_history) as query:
            self.client.get(self.url, {"profile_id": self.other.pk})
        query.assert_called_once()
        args, kwargs = query.call_args
        self.assertEqual(args[0].pk, self.profile.pk)
        self.assertEqual(kwargs, {"limit": 10, "before_id": None})
