"""HTTP local real; parámetros ficticios y sin montar URLs globales."""

from dataclasses import replace
import html
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import include, path, resolve, reverse

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, progress_queries, stat_allocation, views
from .forms import StatAllocationForm
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, Specialization,
    STAT_ATTRIBUTES, StatAllocationEvent, UserSpecializationProgress, XPEvent,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


urlpatterns = [path("test-ecomotor/", include("apps.ecomotor.urls"))]


@override_settings(ROOT_URLCONF=__name__)
class StatAllocationViewTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s8-test-own")
        self.other = create_xp_profile(username="s8-test-other")
        self.config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        self.config.start()
        self.addCleanup(self.config.stop)
        grant_historical_xp(self.profile, 102, "s8-reach-actual")
        grant_historical_xp(self.other, 102, "s8-other-actual")
        UserProfileBank.objects.create(user=self.profile.user)
        self.client.force_login(self.profile.user)
        self.url = reverse("ecomotor:allocate-points")

    def snapshot(self):
        return [list(m.objects.order_by("pk").values()) for m in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            StatAllocationEvent, XPEvent, EvolutionEvent, UserSpecializationProgress,
            Specialization, EvolutionStage, LevelThreshold,
        )]

    def post(self, **changes):
        return self.client.post(self.url, {"attribute": "atk", "points": "3", "operation_key": "s8-test-key"} | changes)

    def test_authenticated_get_template_stats_and_links(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecomotor/allocate_points.html")
        for label, value in (("ATK", 2), ("DEF", 3), ("LOG", 4), ("SPE", 6), ("VEL", 7), ("INT", 8),
                             ("Puntos disponibles", 14)):
            self.assertContains(response, f'<tr><th scope="row">{label}</th><td>{value}</td></tr>', html=True)
        self.assertContains(response, reverse("ecomotor:progress"))

    def test_anonymous_redirect_with_standard_next(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).path, urlsplit(settings.LOGIN_URL).path)
        self.assertEqual(parse_qs(urlsplit(response.url).query)["next"], [self.url])

    @override_settings(LOGIN_URL="/future-core-login/")
    def test_configurable_login_url(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).url, "/future-core-login/?next=" + self.url)

    def test_missing_profile_404_without_initialization(self):
        user = get_user_model().objects.create(username="s8-no-profile")
        self.client.force_login(user)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.post().status_code, 404)
        self.assertEqual(before, self.snapshot())

    def test_foreign_identifiers_ignored_for_get_and_post(self):
        response = self.client.get(self.url, {"profile_id": self.other.pk, "user_id": self.other.user_id})
        self.assertEqual(response.context["overview"].profile_id, self.profile.pk)
        other_before = list(CharacterStats.objects.filter(profile=self.other).values())
        self.assertEqual(self.post(profile_id=self.other.pk, user_id=self.other.user_id).status_code, 302)
        self.assertEqual(other_before, list(CharacterStats.objects.filter(profile=self.other).values()))
        self.assertEqual(StatAllocationEvent.objects.get().profile_id, self.profile.pk)
        self.assertNotContains(response, "s8-test-other")

    def test_csrf_required_and_real_token_succeeds(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.profile.user)
        page = client.get(self.url)
        self.assertContains(page, 'name="csrfmiddlewaretoken"')
        key = page.context["form"].initial["operation_key"]
        data = {"attribute": "atk", "points": "3", "operation_key": key}
        before = self.snapshot()
        self.assertEqual(client.post(self.url, data).status_code, 403)
        self.assertEqual(before, self.snapshot())
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.url, data | {"csrfmiddlewaretoken": "bad"}).status_code, 403)
        self.assertEqual(client.post(self.url, data | {"csrfmiddlewaretoken": token}).status_code, 302)
        self.assertEqual(StatAllocationEvent.objects.count(), 1)

    def test_unsupported_methods_405(self):
        for method in ("put", "patch", "delete", "head"):
            self.assertEqual(getattr(self.client, method)(self.url).status_code, 405)

    def test_only_six_exact_attributes_allowed(self):
        self.assertEqual(tuple(value for value, _ in StatAllocationForm().fields["attribute"].choices), STAT_ATTRIBUTES)
        for value in ("ATK", "DEF", "available_points", "profile_id", "atk__x", ""):
            with self.subTest(value=value):
                self.assertEqual(self.post(attribute=value).status_code, 400)
        self.assertFalse(StatAllocationEvent.objects.exists())

    def test_decimal_integer_representation_is_strict(self):
        before = self.snapshot()
        for value in ("0", "-1", "1.0", "1.5", "1e2", "NaN", "abc", "+1", " 1", "1 ", "١", "", "9" * 5000,
                      str(2**80)):
            with self.subTest(value=value[:25]):
                self.assertEqual(self.post(points=value).status_code, 400)
        self.assertEqual(before, self.snapshot())

    def test_form_technical_upper_bound_without_functional_limit(self):
        upper = connection.ops.integer_field_range("PositiveIntegerField")[1]
        data = {"attribute": "atk", "operation_key": "test-boundary", "points": str(upper)}
        form = StatAllocationForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["points"], upper)
        self.assertFalse(StatAllocationForm(data | {"points": str(upper + 1)}).is_valid())

    def test_key_missing_empty_or_excessive_is_400_not_repaired(self):
        with patch.object(views.secrets, "token_urlsafe", side_effect=AssertionError("No generar en POST")):
            for data in ({"attribute": "atk", "points": "3"},
                         {"attribute": "atk", "points": "3", "operation_key": ""},
                         {"attribute": "atk", "points": "3", "operation_key": "x" * 256}):
                self.assertEqual(self.client.post(self.url, data).status_code, 400)

    def test_bound_key_preserved_on_form_error(self):
        response = self.post(points="1.0", operation_key=" original key ")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.context["form"]["operation_key"].value(), " original key ")
        self.assertContains(response, 'value=" original key "', status_code=400)

    def test_new_gets_have_unpredictable_distinct_hidden_keys(self):
        first = self.client.get(self.url)
        second = self.client.get(self.url)
        one = first.context["form"].initial["operation_key"]
        two = second.context["form"].initial["operation_key"]
        self.assertNotEqual(one, two)
        self.assertRegex(one, r"^[A-Za-z0-9_-]{43}$")
        self.assertContains(first, 'type="hidden" name="operation_key"')
        with patch.object(views.secrets, "token_urlsafe", return_value="test-controlled-key") as generate:
            self.client.get(self.url)
        generate.assert_called_once_with(32)

    def test_first_post_exact_spend_prg_and_fresh_get(self):
        response = self.post()
        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        stats = CharacterStats.objects.get(profile=self.profile)
        self.assertEqual((stats.atk, stats.available_points), (5, 11))
        self.assertEqual((stats.def_stat, stats.log_stat, stats.spe, stats.vel, stats.int_stat), (3, 4, 6, 7, 8))
        page = self.client.get(response.url)
        self.assertEqual((page.context["overview"].atk, page.context["overview"].available_points), (5, 11))
        self.assertContains(page, "Asignación de puntos aplicada.")

    def test_each_attribute_can_be_submitted(self):
        for attribute in STAT_ATTRIBUTES:
            self.assertEqual(self.post(attribute=attribute, points="1", operation_key="s8-" + attribute).status_code, 302)
        self.assertEqual(StatAllocationEvent.objects.count(), 6)

    def test_view_delegates_exactly_once_to_real_service_own_profile(self):
        with patch.object(views, "allocate_stat_points", wraps=stat_allocation.allocate_stat_points) as service:
            response = self.post(profile_id=self.other.pk)
        self.assertEqual(response.status_code, 302)
        service.assert_called_once()
        self.assertEqual(service.call_args.args[0].pk, self.profile.pk)
        self.assertEqual(service.call_args.kwargs, {"attribute": "atk", "points": 3, "operation_key": "s8-test-key"})

    def test_insufficient_points_409_and_key_preserved(self):
        response = self.post(points="15")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.context["form"]["operation_key"].value(), "s8-test-key")
        self.assertFalse(StatAllocationEvent.objects.exists())

    def test_previous_stage_get_available_but_post_409(self):
        self.client.force_login(create_xp_profile(username="s8-prior").user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.post().status_code, 409)

    def test_new_operation_without_valid_configuration_503_but_get_200(self):
        for config in (None, replace(XP_CONFIGURATION, ordered_stage_codes=("wrong",))):
            with patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
                self.assertEqual(self.client.get(self.url).status_code, 200)
                self.assertEqual(self.post().status_code, 503)

    def test_partial_and_inconsistent_state_409(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.assertEqual(self.post().status_code, 409)

    def test_structurally_invalid_profile_is_not_repaired(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x" * 33)
        before = self.snapshot()
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(before, self.snapshot())

    def test_real_overflow_409_without_writes(self):
        CharacterStats.objects.filter(profile=self.profile).update(atk=connection.ops.integer_field_range("IntegerField")[1])
        before = self.snapshot()
        self.assertEqual(self.post().status_code, 409)
        self.assertEqual(before, self.snapshot())

    def test_double_post_one_event_replay_message_and_no_second_spend(self):
        self.assertEqual(self.post().status_code, 302)
        before = self.snapshot()
        response = self.post()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(StatAllocationEvent.objects.count(), 1)
        page = self.client.get(response.url)
        self.assertContains(page, "La operación ya estaba registrada.")
        self.assertContains(page, "No se ha realizado un segundo gasto.")

    def test_same_key_different_attribute_or_quantity_conflicts(self):
        self.post()
        before = self.snapshot()
        self.assertEqual(self.post(attribute="def_stat").status_code, 409)
        self.assertEqual(self.post(points="4").status_code, 409)
        self.assertEqual(before, self.snapshot())

    def test_historical_replay_after_other_allocation_and_s3(self):
        self.post()
        self.post(points="2", operation_key="s8-later")
        grant_historical_xp(self.profile, 17, "s8-later-xp")
        before = self.snapshot()
        self.assertEqual(self.post().status_code, 302)
        self.assertEqual(before, self.snapshot())

    def test_replay_without_or_with_changed_configuration_and_no_overview_precheck(self):
        self.post()
        for config in (None, replace(XP_CONFIGURATION, ordered_stage_codes=tuple(f"changed-{n}" for n in range(7)))):
            with patch.object(initialization_config, "INITIAL_CONFIGURATION", config), \
                    patch.object(views, "get_progress_overview", side_effect=AssertionError("No GET en POST")):
                before = self.snapshot()
                self.assertEqual(self.post().status_code, 302)
                self.assertEqual(before, self.snapshot())

    def test_successful_and_replay_posts_never_generate_keys(self):
        with patch.object(views.secrets, "token_urlsafe", side_effect=AssertionError("No regenerar")):
            self.assertEqual(self.post(operation_key=" exact key ").status_code, 302)
            self.assertEqual(self.post(operation_key=" exact key ").status_code, 302)
        self.assertEqual(StatAllocationEvent.objects.get().operation_key, " exact key ")

    def test_errors_safe_and_exact_exception_mapping(self):
        cases = ((stat_allocation.InvalidAttributeError, 400), (stat_allocation.InvalidPointsError, 400),
                 (stat_allocation.InvalidAllocationKeyError, 400), (stat_allocation.InvalidAllocationProfileError, 404),
                 (stat_allocation.IneligibleStageError, 409), (stat_allocation.InsufficientPointsError, 409),
                 (stat_allocation.AllocationConflictError, 409), (stat_allocation.InconsistentAllocationStateError, 409),
                 (stat_allocation.AllocationOverflowError, 409), (stat_allocation.InvalidAllocationConfigurationError, 503),
                 (stat_allocation.AllocationDatabaseError, 503))
        for error, status in cases:
            with self.subTest(error=error), patch.object(views, "allocate_stat_points", side_effect=error("private SQL secret")):
                response = self.post()
                self.assertEqual(response.status_code, status)
                self.assertNotContains(response, "secret", status_code=status)
                self.assertNotContains(response, "Asignación de puntos aplicada.", status_code=status)

    def test_s4_get_errors_and_profile_lookup_failure(self):
        for error, status in ((progress_queries.InvalidQueryProfileError, 404),
                              (progress_queries.InconsistentQueryStateError, 409),
                              (progress_queries.ProgressQueryDatabaseError, 503)):
            with patch.object(views, "get_progress_overview", side_effect=error("private")):
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, status)
                self.assertNotContains(response, "private", status_code=status)
        with patch.object(UserProfileEcomotor.objects, "get", side_effect=DatabaseError("private SQL")):
            self.assertEqual(self.post().status_code, 503)

    def test_programming_error_not_hidden(self):
        with patch.object(views, "allocate_stat_points", side_effect=RuntimeError("test programming error")):
            with self.assertRaises(RuntimeError):
                self.post()

    def test_get_read_only_and_does_not_call_initializers(self):
        before = self.snapshot()
        with patch("apps.ecomotor.initialization.ensure_ecomotor_initialized", side_effect=AssertionError), \
                patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(before, self.snapshot())
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT") for row in queries))

    def test_post_changes_only_service_owned_stats_and_event(self):
        before = self.snapshot()
        self.post()
        after = self.snapshot()
        for i in range(len(before)):
            if i not in (3, 4):
                self.assertEqual(before[i], after[i])

    def test_template_escapes_persisted_bound_key(self):
        value = '<img src=x onerror="alert(1)">'
        response = self.post(points="bad", operation_key=value)
        self.assertContains(response, html.escape(value, quote=True), status_code=400)
        self.assertNotContains(response, "<img", status_code=400)

    def test_progress_link_namespace_and_no_global_mount(self):
        self.assertEqual(self.url, "/test-ecomotor/allocate-points/")
        self.assertEqual(resolve(self.url).view_name, "ecomotor:allocate-points")
        self.assertEqual(resolve(self.url).kwargs, {})
        response = self.client.get(reverse("ecomotor:progress"))
        self.assertContains(response, f'href="{self.url}"')
        self.assertContains(response, "Historial reciente")
        self.assertContains(response, "XP concedida")
        from config.urls import urlpatterns as production
        self.assertFalse(any(getattr(p, "namespace", None) == "ecomotor" for p in production))
