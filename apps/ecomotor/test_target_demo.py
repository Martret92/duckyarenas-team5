"""Synthetic fixtures only; every database here is a disposable isolated file."""

from html import unescape
from hashlib import sha256
from io import StringIO
from pathlib import Path
import os
import re
from shutil import copyfile
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import Resolver404, resolve
from django.utils import timezone

from . import target_demo_views as views, target_stats_validation, target_xp_preview
from .models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from .target_demo_data import (CATALOG_ID, CATALOG_VERSION, EPOCH_CODES, OPTIONS,
                               THRESHOLDS, demo_database)
from .target_stats_validation import TARGET_STAT_CODES

URL = "/demo/objetivo/"


class TargetDemoTests(TestCase):
    def setUp(self):
        super().setUp()
        temporary = TemporaryDirectory(prefix="ducky-target-demo-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "instance").mkdir()
        self.path = self.root / "instance" / "target_demo.sqlite3"
        self.alias = "target_web_demo_tests"
        config = {**connections["default"].settings_dict, "NAME": self.path,
                  "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5}}
        connections.databases[self.alias] = config
        self.db = connections[self.alias]
        self.addCleanup(self.close_db)
        executor = MigrationExecutor(self.db)
        executor.migrate(executor.loader.graph.leaf_nodes())
        context = override_settings(
            BASE_DIR=self.root, TARGET_DEMO_ENVIRONMENT="A3-TARGET-DEMO-01",
            TARGET_DEMO_DATABASE_ALIAS=self.alias, ROOT_URLCONF="apps.ecomotor.target_demo_urls")
        context.enable()
        self.addCleanup(context.disable)
        self.client = Client()
        self.seed()

    def close_db(self):
        self.db.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def seed(self):
        output = StringIO()
        call_command("seed_target_demo_catalog", stdout=output)
        return output.getvalue()

    def token(self, xp=0, option="", outfit=""):
        return signing.dumps({"xp": xp, "option": option, "outfit": outfit}, salt=views.SALT)

    def post(self, action="xp", xp=0, option="", **fields):
        return self.client.post(URL, {"action": action, "state": self.token(xp, option), **fields})

    def text(self, response):
        return response.content.decode()

    def state_from(self, response):
        return unescape(re.search(r'name="state" value="([^"]+)"', self.text(response)).group(1))

    def rows(self):
        with self.db.cursor() as cursor:
            result = {}
            for table in self.db.introspection.table_names():
                cursor.execute("SELECT * FROM " + self.db.ops.quote_name(table) + " ORDER BY 1")
                result[table] = cursor.fetchall()
            return result

    def test_settings_database_and_routes_are_independent(self):
        from . import target_demo_settings, demo_settings
        self.assertEqual(target_demo_settings.DATABASES["default"]["NAME"].name, "target_demo.sqlite3")
        self.assertEqual(target_demo_settings.DATABASES["default"]["NAME"].parent.name, "instance")
        self.assertNotEqual(target_demo_settings.DATABASES["default"]["NAME"], demo_settings.DATABASES["default"]["NAME"])
        self.assertEqual(demo_settings.ROOT_URLCONF, "apps.ecomotor.demo_urls")
        self.assertEqual(resolve(URL).func, views.target_demo)
        for urlconf in ("config.urls", "apps.ecomotor.demo_urls"):
            with self.subTest(urlconf=urlconf), self.assertRaises(Resolver404): resolve(URL, urlconf=urlconf)
        for url in ("/admin/", "/demo/ecomotor/"):
            with self.subTest(url=url), self.assertRaises(Resolver404): resolve(url)

    def test_seed_idempotent_and_exact_synthetic_rows(self):
        before = self.rows()
        self.assertIn("SINTÉTICO", self.seed())
        self.assertEqual(self.rows(), before)
        version = TargetCatalogVersion.objects.using(self.alias).get()
        self.assertEqual((version.catalog_id, version.version, version.frozen_at), (CATALOG_ID, CATALOG_VERSION, None))
        self.assertEqual(TargetLevelThreshold.objects.using(self.alias).count(), 9)
        self.assertEqual(TargetEpoch.objects.using(self.alias).count(), 7)
        pk, catalog = views._catalog(self.alias)
        self.assertEqual(pk, version.pk)
        self.assertEqual(tuple(r.minimum_xp for r in catalog.levels[:7]), tuple(r.minimum_xp for r in catalog.epochs))

    def test_seed_rejects_incompatible_existing_data_without_repair(self):
        TargetLevelThreshold.objects.using(self.alias).filter(level=2).update(minimum_xp=101)
        before = self.rows()
        with self.assertRaises(CommandError): self.seed()
        self.assertEqual(self.rows(), before)

    def test_seed_rejects_extra_version(self):
        TargetCatalogVersion.objects.using(self.alias).create(catalog_id="demo-other", version="synthetic")
        before = self.rows()
        with self.assertRaises(CommandError): self.seed()
        self.assertEqual(self.rows(), before)

    def test_seed_rejects_frozen_even_identical_version(self):
        with transaction.atomic(using=self.alias):
            TargetCatalogVersion.objects.using(self.alias).update(frozen_at=timezone.now())
            with self.assertRaises(CommandError): self.seed()
            transaction.set_rollback(True, using=self.alias)

    def test_seed_rolls_back_on_a1_validation_failure(self):
        TargetEpoch.objects.using(self.alias).all().delete()
        TargetLevelThreshold.objects.using(self.alias).all().delete()
        TargetCatalogVersion.objects.using(self.alias).all().delete()
        before = self.rows()
        from .target_catalog_validation import InvalidTargetCatalogError
        with patch("apps.ecomotor.management.commands.seed_target_demo_catalog.validate_target_catalog_version",
                   side_effect=InvalidTargetCatalogError("synthetic")):
            with self.assertRaises(CommandError): self.seed()
        self.assertEqual(self.rows(), before)

    def test_environment_rejected_outside_demo(self):
        with override_settings(TARGET_DEMO_ENVIRONMENT=None):
            self.assertEqual(self.client.get(URL).status_code, 404)
            with self.assertRaises(CommandError): self.seed()

    def test_normal_database_path_and_options_override_are_rejected(self):
        for changes in ({"NAME": self.root / "db.sqlite3"},
                        {"OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5, "database": self.root / "db.sqlite3"}},
                        {"NAME": ":memory:"}):
            with self.subTest(changes=changes), patch.dict(self.db.settings_dict, changes):
                self.assertEqual(self.client.get(URL).status_code, 404)
                with self.assertRaises(CommandError): self.seed()
        self.assertFalse((self.root / "db.sqlite3").exists())

    def test_missing_demo_file_is_not_created_by_request_or_seed(self):
        with override_settings(BASE_DIR=self.root / "missing-root"):
            self.assertEqual(self.client.get(URL).status_code, 404)
            with self.assertRaises(CommandError): self.seed()
        self.assertFalse((self.root / "missing-root").exists())

    def assert_isolation_rejected(self):
        configuration = self.db.settings_dict
        options = configuration["OPTIONS"]
        original_name = configuration["NAME"]
        with patch.object(self.db, "get_new_connection", wraps=self.db.get_new_connection) as opener:
            self.assertEqual(self.client.get(URL).status_code, 404)
            self.assertEqual(self.post(amount="1").status_code, 404)
            with self.assertRaises(CommandError): self.seed()
            opener.assert_not_called()
        self.assertIs(self.db.settings_dict, configuration)
        self.assertIs(configuration["OPTIONS"], options)
        self.assertEqual(configuration["NAME"], original_name)
        self.assertIs(connections.databases[self.alias], configuration)

    def test_file_symlink_to_habitual_database_is_rejected_without_changes(self):
        self.db.close()
        habitual = self.root / "db.sqlite3"
        self.path.rename(habitual)
        before = sha256(habitual.read_bytes()).hexdigest()
        try:
            self.path.symlink_to(habitual)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"La plataforma no permite crear symlinks de prueba: {error}")
        self.assert_isolation_rejected()
        self.assertTrue(self.path.is_symlink())
        self.assertEqual(self.path.readlink(), habitual)
        self.assertEqual(sha256(habitual.read_bytes()).hexdigest(), before)

    def test_directory_symlink_cannot_hide_shared_database(self):
        self.db.close()
        store = self.root / "synthetic-store"
        self.path.parent.rename(store)
        try:
            (self.root / "instance").symlink_to(store, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"La plataforma no permite crear symlinks de prueba: {error}")
        before = sha256((store / "target_demo.sqlite3").read_bytes()).hexdigest()
        self.assert_isolation_rejected()
        self.assertTrue((self.root / "instance").is_symlink())
        self.assertEqual(sha256((store / "target_demo.sqlite3").read_bytes()).hexdigest(), before)

    def test_hardlink_to_habitual_database_is_rejected_without_changes(self):
        self.db.close()
        habitual = self.root / "db.sqlite3"
        self.path.rename(habitual)
        before = sha256(habitual.read_bytes()).hexdigest()
        try:
            self.path.hardlink_to(habitual)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"La plataforma no permite crear hardlinks de prueba: {error}")
        self.assertTrue(self.path.samefile(habitual))
        self.assert_isolation_rejected()
        self.assertTrue(self.path.samefile(habitual))
        self.assertEqual(sha256(habitual.read_bytes()).hexdigest(), before)

    def test_symlink_detection_rejects_before_open_without_platform_privileges(self):
        # Complements the real symlink tests when Windows denies their creation.
        self.db.close()
        before = sha256(self.path.read_bytes()).hexdigest()
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path == self.path or original(path)):
            self.assert_isolation_rejected()
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_windows_directory_junction_is_rejected_without_changes(self):
        if os.name != "nt":
            self.skipTest("Las junctions solo corresponden a Windows.")
        self.db.close()
        store = self.root / "synthetic-store"
        instance = self.root / "instance"
        instance.rename(store)
        # Only disposable paths under TemporaryDirectory; no production shell
        # commands, configuration changes or administrator privileges required.
        result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(instance), str(store)],
                                capture_output=True, check=False)
        if result.returncode:
            self.skipTest("Este entorno no permite crear junctions temporales.")
        self.assertTrue(instance.is_junction())
        before = sha256((store / "target_demo.sqlite3").read_bytes()).hexdigest()
        self.assert_isolation_rejected()
        self.assertTrue(instance.is_junction())
        self.assertEqual(sha256((store / "target_demo.sqlite3").read_bytes()).hexdigest(), before)

    def test_disappearing_file_not_recreated_by_get_post_or_seed(self):
        self.db.close()
        backup = self.root / "synthetic-backup.sqlite3"
        copyfile(self.path, backup)
        configuration = self.db.settings_dict
        options = configuration["OPTIONS"]
        original = self.db.get_new_connection

        def disappear(params):
            self.assertTrue(str(params["database"]).endswith("?mode=rw"))
            self.path.unlink()  # Race after inspection, immediately before SQLite opens.
            return original(params)

        for operation in ("GET", "POST", "seed"):
            with self.subTest(operation=operation):
                if not self.path.exists(): copyfile(backup, self.path)
                with patch.object(self.db, "get_new_connection", side_effect=disappear):
                    if operation == "seed":
                        with self.assertRaises(CommandError): self.seed()
                    else:
                        response = self.client.get(URL) if operation == "GET" else self.post(amount="1")
                        self.assertEqual(response.status_code, 503)
                        self.assertNotIn("Reparto válido", self.text(response))
                self.assertFalse(self.path.exists())
                self.assertIsNone(self.db.connection)
                self.assertIs(self.db.settings_dict, configuration)
                self.assertIs(configuration["OPTIONS"], options)
                self.assertEqual(configuration["NAME"], self.path)
                self.assertNotIn("database", options)
                self.assertIs(connections.databases[self.alias], configuration)

    def test_existing_isolated_file_opens_rw_without_mutating_configuration(self):
        before = self.rows()
        self.db.close()
        configuration = self.db.settings_dict
        options = configuration["OPTIONS"]
        with patch.object(self.db, "get_new_connection", wraps=self.db.get_new_connection) as opener:
            response = self.client.get(URL)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(opener.call_count, 1)
            self.assertEqual(opener.call_args.args[0]["database"], self.path.as_uri() + "?mode=rw")
        self.assertEqual(self.post(amount="700").status_code, 200)
        self.seed()
        self.assertIs(self.db.settings_dict, configuration)
        self.assertIs(configuration["OPTIONS"], options)
        self.assertEqual(configuration["NAME"], self.path)
        self.assertNotIn("database", options)
        self.assertEqual(self.rows(), before)

    def test_unrelated_open_connection_cannot_be_relabelled_as_demo(self):
        self.db.close()
        other = self.root / "unrelated-synthetic.sqlite3"
        copyfile(self.path, other)
        with patch.dict(self.db.settings_dict, NAME=other):
            self.db.ensure_connection()
        self.assert_isolation_rejected()

    def test_get_initial_screen_seven_epochs_twelve_options_and_warnings(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        text = self.text(response)
        self.assertIn('id="xp-total">0<', text)
        self.assertIn('id="level">1<', text)
        self.assertIn("BLOQUEADAS HASTA NIVEL 8", text)
        self.assertEqual(text.count('name="option"'), 12)
        self.assertIn("45 puntos es un presupuesto provisional del Equipo 5", text)
        self.assertIn("Las estadísticas base y la selección definitiva todavía no están disponibles", text)
        self.assertIn("no es un diseño final de Duckies", text)
        self.assertNotIn("Guardar Ducky", text)

    def test_xp_delegates_to_preview_and_crosses_all_epochs(self):
        with patch.object(target_xp_preview, "preview_target_xp", wraps=target_xp_preview.preview_target_xp) as spy:
            response = self.post(amount="700")
        self.assertEqual(response.status_code, 200)
        spy.assert_called_once()
        self.assertEqual(spy.call_args.kwargs, {"using": self.alias, "xp_before": 0, "amount": 700})
        self.assertIn('id="level">8<', self.text(response))
        self.assertIn("12 OPCIONES DESBLOQUEADAS", self.text(response))
        self.assertIn("2, 3, 4, 5, 6, 7, 8", self.text(response))
        self.assertEqual(views._state(self.state_from(response))["xp"], 700)

    def test_no_crossing_and_level_nine_remains_seventh_epoch(self):
        for before, amount, level in ((0, "1", 1), (699, "1", 8), (700, "200", 9), (900, "1000", 9)):
            with self.subTest(before=before):
                response = self.post(xp=before, amount=amount)
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'id="level">{level}<', self.text(response))
                if level >= 8:
                    self.assertIn('class="epoch-title">Siglo XX<', self.text(response))
                    self.assertNotIn("demo-epoch-8", self.text(response))

    def test_next_post_uses_updated_signed_xp_not_previous_interval(self):
        first = self.post(amount="100")
        second = self.client.post(URL, {"action": "xp", "state": self.state_from(first), "amount": "100"})
        self.assertEqual(views._state(self.state_from(second))["xp"], 200)

    def test_choice_blocked_before_level_eight(self):
        response = self.post("choose", chosen="demo-gamer")
        self.assertEqual(response.status_code, 400)
        response = self.client.post(URL, {"action": "choose", "state": self.token(600), "option": "demo-gamer"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("se desbloquean en el nivel 8", self.text(response))

    def test_all_twelve_choices_are_visual_and_nonpersistent(self):
        before = self.rows()
        for code, name in OPTIONS:
            with self.subTest(code=code):
                response = self.client.post(URL, {"action": "choose", "state": self.token(700), "option": code})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(views._state(self.state_from(response))["option"], code)
                self.assertIn(name, self.text(response))
        self.assertEqual(self.rows(), before)

    def test_wardrobe_only_after_technology_choice(self):
        for option, status in (("", 400), ("demo-epoch-2", 400), ("demo-gamer", 200)):
            with self.subTest(option=option):
                response = self.post("outfit", xp=700, option=option, outfit="demo-epoch-1")
                self.assertEqual(response.status_code, status)
                if status == 200:
                    self.assertEqual(views._state(self.state_from(response))["outfit"], "demo-epoch-1")

    def test_stats_valid_full_partial_and_zero_and_delegation(self):
        for amount, used, remaining in (("7", 42, 3), ("0", 0, 45)):
            with patch.object(target_stats_validation, "validate_target_stats", wraps=target_stats_validation.validate_target_stats) as spy:
                response = self.post("stats", xp=700, option="demo-gamer", **{c: amount for c in TARGET_STAT_CODES})
            self.assertEqual(response.status_code, 200)
            self.assertIn(f"<b>{used}</b> puntos gastados", self.text(response))
            self.assertIn(f"<b>{remaining}</b> puntos restantes", self.text(response))
            self.assertEqual(spy.call_args.args[0], tuple((c, 0) for c in TARGET_STAT_CODES))
            self.assertEqual(spy.call_args.kwargs, {"budget": 45})
        values = {c: "0" for c in TARGET_STAT_CODES}
        values["ATK"] = "45"
        response = self.post("stats", xp=700, option="demo-developer", **values)
        self.assertIn("<b>45</b> puntos gastados", self.text(response))

    def test_stats_excess_or_before_choice_rejected(self):
        for xp, option, amount in ((700, "demo-gamer", "8"), (0, "", "0"), (700, "", "0")):
            with self.subTest(xp=xp, amount=amount):
                self.assertEqual(self.post("stats", xp=xp, option=option,
                                          **{c: amount for c in TARGET_STAT_CODES}).status_code, 400)

    def test_strict_numbers_in_xp_and_stats(self):
        for value in ("", "-1", "+1", "1.0", "1.5", " 1", "1 ", "1e3", "１２", "١", "a", "0" * 21):
            with self.subTest(value=value):
                self.assertEqual(self.post(amount=value).status_code, 400)
                self.assertEqual(self.post("stats", xp=700, option="demo-gamer",
                                          **{c: value for c in TARGET_STAT_CODES}).status_code, 400)
        self.assertEqual(self.post(amount="0").status_code, 400)

    def test_unexpected_authority_fields_rejected(self):
        for key in ("budget", "bases", "profile", "user_id", "level", "catalog_version", "authorized", "SPE", "epoch", "choice_unlocked"):
            with self.subTest(key=key):
                self.assertEqual(self.post(amount="1", **{key: "1"}).status_code, 400)

    def test_duplicate_fields_rejected(self):
        original = [("action", "stats"), ("state", self.token(700, "demo-gamer")),
                    *((c, "0") for c in TARGET_STAT_CODES)]
        for key, value in original + [("csrfmiddlewaretoken", "x")]:
            with self.subTest(key=key):
                pairs = original + [(key, value)]
                if key == "csrfmiddlewaretoken": pairs.append((key, value))
                self.assertEqual(self.client.post(URL, urlencode(pairs), content_type="application/x-www-form-urlencoded").status_code, 400)
        pairs = [("action", "choose"), ("state", self.token(700)),
                 ("option", "demo-gamer"), ("option", "demo-ciber")]
        self.assertEqual(self.client.post(URL, urlencode(pairs), content_type="application/x-www-form-urlencoded").status_code, 400)

    def test_missing_fields_unknown_actions_and_option_rejected(self):
        for data in ({}, {"action": "delete", "state": self.token()},
                     {"action": "xp", "state": self.token()},
                     {"action": "choose", "state": self.token(700), "option": "official-gamer"}):
            with self.subTest(data=data): self.assertEqual(self.client.post(URL, data).status_code, 400)
        fields = {c: "0" for c in TARGET_STAT_CODES if c != "CUACK"}
        self.assertEqual(self.post("stats", xp=700, option="demo-gamer", **fields).status_code, 400)

    def test_forged_expired_or_malformed_signed_state_rejected(self):
        for token in ("fake", self.token() + "x", signing.dumps({"xp": True, "option": "", "outfit": ""}, salt=views.SALT)):
            with self.subTest(token=token):
                self.assertEqual(self.client.post(URL, {"action": "xp", "state": token, "amount": "1"}).status_code, 400)
        self.assertEqual(self.client.post(URL, {"action": "xp", "state": "x" * 3000, "amount": "1"}).status_code, 400)
        with patch("django.core.signing.time.time", return_value=1): old = self.token()
        self.assertEqual(self.client.post(URL, {"action": "xp", "state": old, "amount": "1"}).status_code, 400)

    def test_errors_preserve_and_escape_original_input(self):
        attack = '<script>alert("x")</script>'
        response = self.post(amount=attack)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(attack, self.text(response))
        self.assertIn("&lt;script&gt;", self.text(response))

    def test_csrf_real_missing_rejected_valid_accepted(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get(URL)
        data = {"action": "xp", "state": self.state_from(response), "amount": "1"}
        self.assertEqual(client.post(URL, data).status_code, 403)
        data["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
        self.assertEqual(client.post(URL, data).status_code, 200)

    def test_only_get_post_supported_and_query_authority_rejected(self):
        for method in ("put", "patch", "delete", "head", "options", "trace"):
            with self.subTest(method=method): self.assertEqual(getattr(self.client, method)(URL).status_code, 405)
        self.assertEqual(self.client.get(URL, {"xp": "700"}).status_code, 400)

    def test_reset_restores_zero_without_deleting_data(self):
        before = self.rows()
        response = self.post("reset", xp=900, option="demo-gamer")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(views._state(self.state_from(response)), {"xp": 0, "option": "", "outfit": ""})
        self.assertEqual(self.rows(), before)

    def test_get_post_never_write_nor_call_v1_freeze_or_resolver(self):
        before = self.rows()
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError("V1")), \
                patch("apps.ecomotor.target_catalog_freeze.freeze_target_catalog_version", side_effect=AssertionError("freeze")), \
                patch("apps.ecomotor.target_stats_resolution.resolve_target_stats_configuration", side_effect=AssertionError("resolution")), \
                CaptureQueriesContext(self.db) as queries:
            self.assertEqual(self.client.get(URL).status_code, 200)
            self.assertEqual(self.post(amount="700").status_code, 200)
            self.assertEqual(self.post("stats", xp=700, option="demo-gamer", **{c: "1" for c in TARGET_STAT_CODES}).status_code, 200)
        forbidden = ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(forbidden) for q in queries))
        self.assertEqual(self.rows(), before)
        self.assertNotIn("sessionid", self.client.cookies)

    def test_no_automatic_catalog_installation_on_missing_or_invalid_catalog(self):
        TargetEpoch.objects.using(self.alias).all().delete()
        before = self.rows()
        self.assertEqual(self.client.get(URL).status_code, 503)
        self.assertEqual(self.post(amount="1").status_code, 503)
        self.assertEqual(self.rows(), before)

    def test_database_failure_produces_controlled_unavailable_page(self):
        from django.db import OperationalError
        with patch.object(views, "_catalog", side_effect=OperationalError("sensitive SQL")):
            response = self.client.get(URL)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive SQL", self.text(response))
