"""V1 alpha in an isolated mount; all users, catalogs and grants are synthetic."""

from contextlib import ExitStack
from dataclasses import replace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import NoReverseMatch, Resolver404, include, path, resolve, reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import alpha_urls, initialization_config, progress_queries, views
from .models import CharacterStats, EvolutionEvent, EvolutionStage, StatAllocationEvent, XPEvent
from .stat_allocation import allocate_stat_points
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


urlpatterns = [path("test-alpha/", include("apps.ecomotor.alpha_urls"))]


class FullV1URLConf:
    urlpatterns = [path("full-v1/", include("apps.ecomotor.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class AlphaViewTests(TestCase):
    names = ("progress", "xp-history", "allocation-history")

    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="alpha-owner")
        self.other = create_xp_profile(username="alpha-other-private")
        self.client.force_login(self.profile.user)
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def url(self, name):
        return reverse("ecomotor:" + name)

    def snapshot(self):
        models = (*apps.get_app_config("ecomotor").get_models(),
                  get_user_model(), UserProfileEcomotor, UserProfileBank)
        return {model._meta.label: list(model.objects.order_by("pk").values()) for model in models}

    def actual(self, profile=None):
        profile = self.profile if profile is None else profile
        grant_historical_xp(profile, 102, "alpha-reach-actual")
        return allocate_stat_points(profile, "atk", 1, "alpha-allocation-private-key")

    def test_exact_three_patterns_reuse_views_and_resolve(self):
        self.assertEqual(len(alpha_urls.urlpatterns), 3)
        self.assertEqual(alpha_urls.app_name, "ecomotor")
        callbacks = (views.progress_view, views.xp_history_view, views.allocation_history_view)
        for name, callback in zip(self.names, callbacks):
            url = self.url(name)
            self.assertEqual(url, "/test-alpha/" + name + "/")
            match = resolve(url)
            self.assertEqual(match.view_name, "ecomotor:" + name)
            self.assertIs(match.func, callback)
            self.assertEqual(match.kwargs, {"alpha_mode": True})

    def test_allocation_root_and_global_mount_absent(self):
        with self.assertRaises(NoReverseMatch):
            self.url("allocate-points")
        for url in ("/test-alpha/", "/test-alpha/allocate-points/"):
            with self.assertRaises(Resolver404): resolve(url)
            self.assertEqual(self.client.get(url).status_code, 404)
        with override_settings(ROOT_URLCONF="config.urls"), self.assertRaises(NoReverseMatch):
            self.url("progress")

    @override_settings(LOGIN_URL="/core-login-pending/")
    def test_anonymous_uses_configured_login_with_next(self):
        self.client.logout()
        for name in self.names:
            response = self.client.get(self.url(name))
            self.assertEqual(response.status_code, 302)
            target = urlsplit(response.url)
            self.assertEqual(target.path, "/core-login-pending/")
            self.assertEqual(parse_qs(target.query), {"next": [self.url(name)]})

    def test_anonymous_authentication_precedes_method_decorator(self):
        self.client.logout()
        for name in self.names:
            self.assertEqual(self.client.post(self.url(name)).status_code, 302)

    def test_get_head_empty_navigation_without_allocation_reverses(self):
        templates = ("progress", "xp_history", "allocation_history")
        for name, template in zip(self.names, templates):
            response = self.client.get(self.url(name))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "ecomotor/" + template + ".html")
            self.assertTrue(response.context["ecomotor_alpha_mode"])
            for other in self.names:
                self.assertContains(response, 'href="' + self.url(other) + '"')
            for forbidden in ("allocate-points", "Asignar puntos", "<form"):
                self.assertNotContains(response, forbidden)
            self.assertContains(response, 'aria-current="page"')
            head = self.client.head(self.url(name))
            self.assertEqual((head.status_code, head.content), (200, b""))

    def test_alpha_mode_cannot_be_disabled_by_query_parameters(self):
        for name in self.names:
            response = self.client.get(self.url(name), {
                "alpha_mode": "false", "ecomotor_alpha_mode": "0", "allocate_points": "true",
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["ecomotor_alpha_mode"])
            self.assertNotContains(response, "allocate-points")

    def test_two_users_and_foreign_identifiers_only_show_own_records(self):
        own, foreign = self.actual(), self.actual(self.other)
        for profile, allocation in ((self.profile, own), (self.other, foreign)):
            self.client.force_login(profile.user)
            params = {"profile_id": self.other.pk if profile == self.profile else self.profile.pk,
                      "user_id": self.other.user_id, "username": self.other.user.username}
            response = self.client.get(self.url("progress"), params)
            self.assertEqual(response.context["overview"].profile_id, profile.pk)
            history = self.client.get(self.url("xp-history"), params).context["history"]
            self.assertEqual([e.id for e in history.entries],
                             list(XPEvent.objects.filter(profile=profile).values_list("pk", flat=True)))
            history = self.client.get(self.url("allocation-history"), params).context["history"]
            self.assertEqual([e.id for e in history.entries], [allocation.allocation_event_id])

    def test_missing_profile_404_without_provisioning(self):
        self.client.force_login(get_user_model().objects.create(username="alpha-no-profile"))
        before = self.snapshot()
        for name in self.names: self.assertEqual(self.client.get(self.url(name)).status_code, 404)
        self.assertEqual(self.snapshot(), before)

    def test_partial_profile_409_without_repair_or_details(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        before = self.snapshot()
        for name in self.names:
            response = self.client.get(self.url(name))
            self.assertEqual(response.status_code, 409)
            self.assertNotIn("CharacterStats", response.content.decode())
        self.assertEqual(self.snapshot(), before)

    def test_corrupt_xp_and_crossed_evolution_are_rejected(self):
        grant = grant_historical_xp(self.profile, 51, "alpha-xp-private-key")
        EvolutionEvent.objects.filter(xp_event_id=grant.xp_event_id).update(profile=self.other)
        for profile in (self.profile, self.other):
            self.client.force_login(profile.user)
            for name in ("progress", "xp-history"):
                response = self.client.get(self.url(name))
                self.assertEqual(response.status_code, 409)
                self.assertNotIn("alpha-xp-private-key", response.content.decode())
        EvolutionEvent.objects.filter(xp_event_id=grant.xp_event_id).update(profile=self.profile)
        XPEvent.objects.filter(pk=grant.xp_event_id).update(operation_key="x" * 256)
        self.client.force_login(self.profile.user)
        self.assertEqual(self.client.get(self.url("xp-history")).status_code, 409)

    def test_corrupt_allocation_history_is_not_repaired(self):
        self.actual()
        StatAllocationEvent.objects.filter(profile=self.profile).update(stage_code_at_allocation="x" * 33)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url("allocation-history")).status_code, 409)
        self.assertEqual(self.snapshot(), before)

    def test_database_lookup_errors_safe_503(self):
        with patch.object(UserProfileEcomotor.objects, "get", side_effect=DatabaseError("private SQL path")):
            for name in self.names:
                response = self.client.get(self.url(name))
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private SQL path", response.content.decode())

    def test_query_errors_keep_http_meaning_and_do_not_leak(self):
        queries = (("progress", "get_progress_overview"), ("progress", "list_progress_history"),
                   ("xp-history", "list_progress_history"), ("allocation-history", "list_stat_allocation_history"))
        for name, query in queries:
            for error, status in ((progress_queries.InvalidQueryProfileError, 404),
                                  (progress_queries.InconsistentQueryStateError, 409),
                                  (progress_queries.ProgressQueryDatabaseError, 503), (DatabaseError, 503)):
                with patch.object(views, query, side_effect=error("private identity SQL")):
                    response = self.client.get(self.url(name))
                    self.assertEqual(response.status_code, status)
                    self.assertNotIn("private identity SQL", response.content.decode())

    def test_history_cursors_strict_and_duplicate_rejected(self):
        for name in ("xp-history", "allocation-history"):
            for value in ("", "0", "-1", "+1", "1.0", "1e2", " 1", "١", str(2**64), "9" * 5000):
                self.assertEqual(self.client.get(self.url(name), {"before_id": value}).status_code, 400)
            self.assertEqual(self.client.get(self.url(name) + "?before_id=1&before_id=1").status_code, 400)

    def test_history_pagination_retains_snapshots_and_causal_references(self):
        self.actual()
        for n in range(12):
            grant_historical_xp(self.profile, 1, f"alpha-grant-{n}")
            allocate_stat_points(self.profile, "atk", 1, f"alpha-spend-{n}")
        for name, model in (("xp-history", XPEvent), ("allocation-history", StatAllocationEvent)):
            ids = list(model.objects.filter(profile=self.profile).order_by("-pk").values_list("pk", flat=True))
            first = self.client.get(self.url(name))
            page = first.context["history"]
            self.assertEqual([e.id for e in page.entries], ids[:10])
            self.assertContains(first, f'{self.url(name)}?before_id={page.next_before_id}')
            second = self.client.get(self.url(name), {"before_id": page.next_before_id})
            self.assertEqual([e.id for e in second.context["history"].entries], ids[10:])
            for entry in second.context["history"].entries:
                row = model.objects.get(pk=entry.id)
                if name == "xp-history":
                    self.assertEqual((entry.xp_before, entry.xp_after), (row.xp_before, row.xp_after))
                    self.assertEqual([e.id for e in entry.evolutions],
                                     list(EvolutionEvent.objects.filter(xp_event=row).order_by("pk").values_list("pk", flat=True)))
                    self.assertNotContains(second, row.operation_key)
                else:
                    self.assertEqual((entry.attribute_before, entry.attribute_after), (row.attribute_before, row.attribute_after))
                    self.assertEqual(entry.stage_code_at_allocation, row.stage_code_at_allocation)
            self.assertNotContains(second, "allocate-points")

    def test_stats_are_v1_and_missing_configuration_is_not_fabricated(self):
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            response = self.client.get(self.url("progress"))
        self.assertContains(response, "SPE")
        self.assertNotContains(response, "CUACK")
        self.assertContains(response, "La próxima etapa no está disponible para consulta.")
        self.assertContains(response, "Nivel 2. Umbral XP: 11.")

    def test_html_escaped_and_private_operation_keys_absent(self):
        grant_historical_xp(self.profile, 1, "<script>alpha-private-key</script>")
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="<script>alpha</script>")
        self.assertContains(self.client.get(self.url("progress")), "&lt;script&gt;alpha&lt;/script&gt;")
        response = self.client.get(self.url("xp-history"))
        self.assertNotContains(response, "alpha-private-key")
        history = response.context["history"]
        injected = replace(history, entries=(replace(history.entries[0], id="<script>entry</script>"),))
        with patch.object(views, "list_progress_history", return_value=injected):
            response = self.client.get(self.url("xp-history"))
        self.assertContains(response, "&lt;script&gt;entry&lt;/script&gt;")
        self.assertNotContains(response, "<script>entry</script>")

    def test_repeated_get_head_only_select_and_never_call_writers(self):
        self.actual()
        before = self.snapshot()
        writers = ("apps.ecomotor.initialization.ensure_ecomotor_initialized",
                   "apps.ecomotor.xp_service.grant_historical_xp", "apps.ecomotor.views.allocate_stat_points",
                   "apps.ecomotor.reward_rules.evaluate_reward", "apps.bank.services.credit_coins")
        with ExitStack() as stack:
            for writer in writers: stack.enter_context(patch(writer, side_effect=AssertionError(writer)))
            with CaptureQueriesContext(connection) as queries:
                for _ in range(2):
                    for name in self.names:
                        self.assertEqual(self.client.get(self.url(name)).status_code, 200)
                        self.assertEqual(self.client.head(self.url(name)).status_code, 200)
            self.assertTrue(queries)
            self.assertTrue(all(q["sql"].lstrip().upper().startswith("SELECT") for q in queries))
        self.assertEqual(self.snapshot(), before)

    def test_mutating_methods_405_without_business_effects(self):
        before = self.snapshot()
        with patch.object(views, "allocate_stat_points", side_effect=AssertionError):
            for name in self.names:
                for method in ("post", "put", "patch", "delete", "options", "trace"):
                    response = getattr(self.client, method)(self.url(name), {"alpha_mode": False})
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.headers["Allow"], "GET, HEAD")
        self.assertEqual(self.snapshot(), before)

    def test_queries_delegate_to_existing_public_services(self):
        with patch.object(views, "get_progress_overview", wraps=views.get_progress_overview) as overview, \
             patch.object(views, "list_progress_history", wraps=views.list_progress_history) as xp_history, \
             patch.object(views, "list_stat_allocation_history", wraps=views.list_stat_allocation_history) as allocation_history:
            for name in self.names: self.assertEqual(self.client.get(self.url(name)).status_code, 200)
        self.assertEqual((overview.call_count, xp_history.call_count, allocation_history.call_count), (1, 2, 1))
        for query in (overview, xp_history, allocation_history):
            self.assertTrue(all(call.args[0].pk == self.profile.pk for call in query.call_args_list))

    def test_programming_errors_are_not_disguised(self):
        with patch.object(views, "get_progress_overview", side_effect=RuntimeError("test bug")):
            with self.assertRaisesRegex(RuntimeError, "test bug"): self.client.get(self.url("progress"))

    @override_settings(ROOT_URLCONF=FullV1URLConf)
    def test_full_v1_navigation_default_and_query_flags_unchanged(self):
        from .urls import urlpatterns as full_patterns
        self.assertEqual(len(full_patterns), 4)
        allocation_url = self.url("allocate-points")
        for name in (*self.names, "allocate-points"):
            response = self.client.get(self.url(name), {"alpha_mode": "true", "ecomotor_alpha_mode": "1"})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context.get("ecomotor_alpha_mode", False))
            self.assertContains(response, allocation_url)
            self.assertContains(response, "Asignar puntos")

    @override_settings(ROOT_URLCONF=FullV1URLConf)
    def test_full_v1_assignment_real_csrf_post_and_replay_preserved(self):
        grant_historical_xp(self.profile, 102, "alpha-full-v1-setup")
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.profile.user)
        url = self.url("allocate-points")
        page = client.get(url)
        data = {"attribute": "atk", "points": "1", "operation_key": page.context["form"].initial["operation_key"]}
        self.assertEqual(client.post(url, data).status_code, 403)
        self.assertFalse(StatAllocationEvent.objects.exists())
        data["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
        self.assertEqual(client.post(url, data).status_code, 302)
        after = self.snapshot()
        self.assertEqual(client.post(url, data).status_code, 302)
        self.assertEqual(self.snapshot(), after)
        self.assertEqual(StatAllocationEvent.objects.count(), 1)
