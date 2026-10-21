"""Synthetic HTTP inputs only; SimpleTestCase forbids database access."""

from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.http import QueryDict
from django.test import Client, SimpleTestCase, override_settings
from django.urls import Resolver404, resolve

from . import demo_forms, demo_settings, demo_views, target_stats_validation
from .target_stats_validation import TARGET_STAT_CODES


@override_settings(ROOT_URLCONF="apps.ecomotor.demo_urls")
class TargetStatsDemoTests(SimpleTestCase):
    url = "/demo/ecomotor/"

    def payload(self, value="0", **changes):
        return {"option": "demo-developer", **dict.fromkeys(TARGET_STAT_CODES, value)} | changes

    def post(self, data=None, client=None):
        if data is None:
            data = self.payload()
        encoded = data.urlencode() if isinstance(data, QueryDict) else urlencode(data)
        return (client or self.client).post(self.url, encoded, content_type="application/x-www-form-urlencoded")

    def test_anonymous_get_independent_template(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ecomotor/target_stats_demo.html")
        self.assertTemplateNotUsed(response, "ecomotor/base.html")
        self.assertNotIn(settings.SESSION_COOKIE_NAME, self.client.cookies)

    def test_five_labels_six_controls_and_submit_button(self):
        response = self.client.get(self.url)
        for label in ("Developer", "Ciber", "Sistemas", "Data IA", "Gamer",
                      "Ataque", "Defensa", "Velocidad", "Inteligencia", "Lógica", "Cuak",
                      "Comprobar reparto"):
            self.assertContains(response, label)
        for code in TARGET_STAT_CODES:
            self.assertContains(response, f'name="{code}"', count=1)
        self.assertEqual(len(response.context["form"].fields), 7)

    def test_exact_warnings_and_no_confirmation_or_effective_values(self):
        response = self.client.get(self.url)
        for text in ("Demostración local: no se guardan datos",
                     "45 puntos es un presupuesto provisional del Equipo 5",
                     "Las estadísticas base y la selección definitiva todavía no están disponibles"):
            self.assertContains(response, text)
        for text in ("Guardar Ducky", "Confirmar selección", "Estadísticas efectivas", "name=\"budget\"",
                     "name=\"bases\"", "/admin/", "/ecomotor/progress/"):
            self.assertNotContains(response, text)

    def test_exact_budget(self):
        response = self.post(self.payload(ATK="45"))
        self.assertContains(response, "Reparto válido")
        self.assertEqual(response.context["result"], {
            "option_label": "Developer", "points_used": 45, "points_remaining": 0,
        })

    def test_partial_distribution(self):
        response = self.post(self.payload(ATK="7", DEF="3"))
        self.assertEqual(response.context["result"]["points_used"], 10)
        self.assertEqual(response.context["result"]["points_remaining"], 35)

    def test_zero_distribution(self):
        response = self.post()
        self.assertEqual(response.context["result"]["points_used"], 0)
        self.assertEqual(response.context["result"]["points_remaining"], 45)

    def test_arbitrary_six_attribute_distribution(self):
        response = self.post(self.payload(**dict(zip(TARGET_STAT_CODES, ("2", "4", "6", "8", "10", "12")))))
        self.assertEqual(response.context["result"]["points_used"], 42)
        self.assertEqual(response.context["result"]["points_remaining"], 3)

    def test_all_options_are_demo_labels(self):
        for code, label in demo_forms.DEMO_OPTIONS:
            with self.subTest(option=code):
                response = self.post(self.payload(option=code))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["result"]["option_label"], label)

    def test_budget_exceeded_is_form_error_without_result(self):
        for value in ("46", "9999999999"):
            with self.subTest(value=value):
                response = self.post(self.payload(ATK=value))
                self.assertContains(response, "supera los 45 puntos", status_code=400)
                self.assertIsNone(response.context["result"])

    def test_option_unknown_empty_or_absent(self):
        for option in (None, "", "Developer", "official-developer", "<script>alert(1)</script>"):
            data = self.payload(option=option)
            if option is None:
                del data["option"]
            with self.subTest(option=option):
                self.assertEqual(self.post(data).status_code, 400)

    def test_every_increment_required_and_nonempty(self):
        for code in TARGET_STAT_CODES:
            for absent in (True, False):
                data = self.payload()
                if absent:
                    del data[code]
                else:
                    data[code] = ""
                with self.subTest(code=code, absent=absent):
                    self.assertEqual(self.post(data).status_code, 400)

    def test_strict_ascii_decimal_text_before_conversion(self):
        for text in ("-1", "1.0", "1.5", "abc", "+1", "1e1", " 1", "1 ", "\t1", "1\n",
                     "١", "１", "1_0", "NaN", "True", "0x1", "9" * 11, "9" * 5000):
            with self.subTest(text=text[:30]):
                response = self.post(self.payload(ATK=text))
                self.assertEqual(response.status_code, 400)
                self.assertIsNone(response.context["result"])

    def test_leading_zeroes_are_valid_ascii_representation(self):
        response = self.post(self.payload(ATK="0000000001"))
        self.assertEqual(response.context["result"]["points_used"], 1)

    def test_duplicates_including_identical_values_rejected(self):
        for name in ("option", *TARGET_STAT_CODES, "csrfmiddlewaretoken"):
            data = QueryDict("", mutable=True)
            data.update(self.payload())
            value = data.get(name, "synthetic-token")
            data.setlist(name, [value, value])
            with self.subTest(name=name):
                response = self.post(data)
                self.assertContains(response, "una sola vez", status_code=400)

    def test_all_additional_authority_fields_rejected(self):
        for name in ("budget", "bases", "level", "profile", "profile_id", "user_id", "username",
                     "catalog_id", "catalog_version", "definition_version", "authorized", "SPE", "atk"):
            with self.subTest(name=name):
                response = self.post(self.payload(**{name: "synthetic"}))
                self.assertContains(response, "campos no permitidos", status_code=400)

    def test_code_replacement_is_not_normalized(self):
        for code in ("SPE", "atk", " ATK", "ATK "):
            data = self.payload()
            data[code] = data.pop("ATK")
            with self.subTest(code=code):
                self.assertEqual(self.post(data).status_code, 400)

    def test_values_preserved_and_html_escaped_after_error(self):
        response = self.post(self.payload(ATK='<script>alert("synthetic")</script>', DEF="12"))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "&lt;script&gt;", status_code=400)
        self.assertNotContains(response, "<script>", status_code=400)
        self.assertContains(response, 'value="12"', status_code=400)

    def test_calls_public_a41_with_zero_bases_and_server_budget(self):
        with patch.object(target_stats_validation, "validate_target_stats",
                          wraps=target_stats_validation.validate_target_stats) as validate:
            response = self.post(self.payload("1"))
        self.assertEqual(response.status_code, 200)
        validate.assert_called_once_with(tuple((code, 0) for code in TARGET_STAT_CODES),
                                         tuple((code, 1) for code in TARGET_STAT_CODES), budget=45)

    def test_displayed_totals_come_from_a41_only(self):
        with patch.object(target_stats_validation, "validate_target_stats",
                          return_value=SimpleNamespace(points_used=42, points_remaining=3)):
            response = self.post()
        self.assertEqual(response.context["result"]["points_used"], 42)
        self.assertEqual(response.context["result"]["points_remaining"], 3)
        self.assertEqual(set(response.context["result"]), {"option_label", "points_used", "points_remaining"})

    def test_invalid_http_never_reaches_a41(self):
        with patch.object(target_stats_validation, "validate_target_stats", side_effect=AssertionError):
            self.assertEqual(self.post(self.payload(budget="999")).status_code, 400)
            self.assertEqual(self.post(self.payload(ATK="+1")).status_code, 400)

    def test_public_validation_errors_are_safe(self):
        for error in (target_stats_validation.InvalidTargetStatsNumericError,
                      target_stats_validation.InvalidTargetStatsStructureError,
                      target_stats_validation.TargetStatsBudgetExceededError):
            with self.subTest(error=error), patch.object(target_stats_validation, "validate_target_stats",
                                                       side_effect=error("sensitive synthetic details")):
                response = self.post()
                self.assertEqual(response.status_code, 400)
                self.assertNotContains(response, "sensitive synthetic details", status_code=400)

    def test_csrf_missing_bad_and_valid_tokens(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(client=client).status_code, 403)
        page = client.get(self.url)
        self.assertContains(page, 'name="csrfmiddlewaretoken"')
        self.assertEqual(self.post(self.payload(csrfmiddlewaretoken="bad"), client).status_code, 403)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(self.post(self.payload(csrfmiddlewaretoken=token), client).status_code, 200)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, client.cookies)

    def test_only_get_and_post_allowed(self):
        for method in ("put", "patch", "delete", "head", "options", "trace"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["Allow"], "GET, POST")

    def test_demo_route_excluded_from_global_and_v1_admin_excluded_from_demo(self):
        self.assertIs(resolve(self.url).func, demo_views.target_stats_demo)
        for url in ("/admin/", "/ecomotor/progress/", "/ecomotor/allocate-points/"):
            with self.subTest(url=url), self.assertRaises(Resolver404):
                resolve(url)
        with override_settings(ROOT_URLCONF="config.urls"), self.assertRaises(Resolver404):
            resolve(self.url)

    def test_demo_settings_only_change_urlconf(self):
        from config import settings as normal
        differences = {name for name in dir(normal) if name.isupper()
                       and getattr(normal, name) != getattr(demo_settings, name)}
        self.assertEqual(differences, {"ROOT_URLCONF"})
        self.assertEqual(demo_settings.ROOT_URLCONF, "apps.ecomotor.demo_urls")
        self.assertIn("django.middleware.csrf.CsrfViewMiddleware", demo_settings.MIDDLEWARE)

    def test_no_v1_services_initializers_or_definition_preparers(self):
        targets = ("apps.ecomotor.initialization.ensure_ecomotor_initialized",
                   "apps.ecomotor.xp_service.grant_historical_xp",
                   "apps.ecomotor.stat_allocation.allocate_stat_points",
                   "apps.ecomotor.target_stats_config_validation.validate_target_stats_definition",
                   "apps.ecomotor.target_stats_preparation.prepare_target_stats_configuration")
        from contextlib import ExitStack
        with ExitStack() as stack:
            for target in targets:
                stack.enter_context(patch(target, side_effect=AssertionError(target)))
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.post().status_code, 200)

    def test_anonymous_get_post_never_use_database_sessions_or_players(self):
        # SimpleTestCase rejects all DB queries; an authenticated session is not supplied.
        for response in (self.client.get(self.url), self.post()):
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
            with self.assertRaises(KeyError):
                response.context["profile"]
            self.assertNotIn("effective", response.context["result"] or {})
