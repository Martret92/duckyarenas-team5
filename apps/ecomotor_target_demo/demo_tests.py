"""Explicit suite: run with target_persistent_demo_settings.

Name deliberately avoids normal test*.py discovery: this app is not installed
in normal settings. All operations below use disposable file-backed databases.
"""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from importlib import import_module
from io import StringIO
from pathlib import Path
from shutil import copyfile
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier, Event
from time import monotonic
from unittest import SkipTest, TestCase
from unittest.mock import patch
from urllib.parse import urlencode

from django.apps import apps
if not apps.is_installed("apps.ecomotor_target_demo"):
    raise SkipTest("La app persistente solo se prueba con sus settings exclusivos.")

from django.conf import settings
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections, transaction, IntegrityError, OperationalError
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext

from apps.ecomotor.models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from apps.ecomotor.target_catalog_freeze import freeze_target_catalog_version
from . import services, catalog
from .data import MAX_XP, CODES, CATALOG_ID, VERSION
from .isolation import demo_connection
from .models import DemoTargetProgress, DemoTargetXPEvent, DemoTargetEvolutionEvent

URL = "/demo/objetivo-persistente/"
SECRET = "1" * 64
OTHER = "2" * 64


class PersistentTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="ducky-persistent-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "instance").mkdir()
        self.path = self.root / "instance" / "target_persistent_demo.sqlite3"
        self.alias = "persistent_fixture"
        config = {**connections["default"].settings_dict,
                  "ENGINE": "apps.ecomotor_target_demo.db_backend", "NAME": self.path,
                  "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5}}
        connections.databases[self.alias] = config
        self.db = connections[self.alias]
        self.addCleanup(self.close)
        context = override_settings(BASE_DIR=self.root, TARGET_PERSISTENT_DEMO_ALIAS=self.alias,
            ROOT_URLCONF="apps.ecomotor_target_demo.urls")
        context.enable()
        self.addCleanup(context.disable)
        self.migrate()
        self.client = Client()

    def close(self):
        self.db.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self):
        call_command("migrate", database=self.alias, verbosity=0, stdout=StringIO())

    def seed(self):
        call_command("seed_persistent_target_demo", stdout=StringIO())

    def new(self, secret=SECRET):
        self.seed()
        return services.create_demo_progress(session_token=secret)

    def operation(self, progress, secret=SECRET):
        return services.issue_demo_operation(progress, session_token=secret)

    def grant(self, progress, amount=700, token=None, secret=SECRET):
        return services.grant_demo_target_xp(progress, amount=amount,
            operation_token=token or self.operation(progress, secret), session_token=secret)

    def rows(self):
        with self.db.cursor() as cursor:
            result = {}
            for name in self.db.introspection.table_names():
                cursor.execute("SELECT * FROM " + self.db.ops.quote_name(name) + " ORDER BY 1")
                result[name] = cursor.fetchall()
            return result

    def http_start(self, client=None):
        self.seed()
        client = client or self.client
        response = client.post(URL, {"action": "start"})
        self.assertEqual(response.status_code, 302)
        return client.get(URL)

    def http_data(self, client=None, amount="700"):
        client = client or self.client
        return {"action": "grant", "operation": client.session["demo_operation"], "amount": amount}

    def test_initial_migration_only_demo_tables_and_constraints(self):
        migration = import_module("apps.ecomotor_target_demo.migrations.0001_initial").Migration
        self.assertEqual(migration.dependencies, [("ecomotor", "0007_target_catalog_freeze")])
        self.assertTrue(all(type(op).__name__ in ("CreateModel", "AddConstraint") for op in migration.operations))
        self.assertEqual(DemoTargetProgress.objects.using(self.alias).count(), 0)
        self.assertEqual(TargetCatalogVersion.objects.using(self.alias).count(), 0)
        with self.db.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'ecomotor_t%'")
            self.assertEqual(cursor.fetchone()[0], 9)

    def test_seed_exact_frozen_and_idempotent(self):
        self.seed()
        before = self.rows()
        self.seed()
        self.assertEqual(self.rows(), before)
        version = TargetCatalogVersion.objects.using(self.alias).get()
        self.assertIsNotNone(version.frozen_at)
        self.assertEqual((version.catalog_id, version.version), (CATALOG_ID, VERSION))
        self.assertEqual(TargetEpoch.objects.using(self.alias).count(), 7)

    def test_seed_freeze_failure_is_recoverable_and_blocks_xp(self):
        with patch.object(catalog.target_catalog_freeze, "freeze_target_catalog_version", side_effect=OperationalError("synthetic failure")):
            with self.assertRaises(CommandError): self.seed()
        version = TargetCatalogVersion.objects.using(self.alias).get()
        self.assertIsNone(version.frozen_at)
        with self.assertRaises(catalog.DemoCatalogError): services.create_demo_progress(session_token=SECRET)
        self.assertEqual(DemoTargetProgress.objects.using(self.alias).count(), 0)
        self.seed()
        version.refresh_from_db(using=self.alias)
        self.assertIsNotNone(version.frozen_at)

    def test_seed_rejects_incompatible_catalog_without_repair(self):
        version = TargetCatalogVersion.objects.using(self.alias).create(catalog_id=CATALOG_ID, version=VERSION)
        before = self.rows()
        with self.assertRaises(CommandError): self.seed()
        self.assertEqual(self.rows(), before)
        self.assertIsNone(version.frozen_at)

    def test_new_game_initial_state(self):
        progress = self.new()
        self.assertEqual((progress.xp_total, progress.current_level, progress.current_epoch.code), (0, 1, CODES[0]))
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 0)

    def test_hundred_xp_and_greek_cause(self):
        progress = self.new()
        result = self.grant(progress, 100)
        self.assertEqual((result.progression.level_after, result.progression.epoch_after_code), (2, CODES[1]))
        event = DemoTargetEvolutionEvent.objects.using(self.alias).get()
        self.assertEqual((event.xp_event_id, event.progress_id, event.epoch.code, event.ordinal), (result.event_id, progress.pk, CODES[1], 2))

    def test_seven_hundred_six_evolutions_and_no_eighth_epoch(self):
        progress = self.new()
        result = self.grant(progress)
        progress.refresh_from_db(using=self.alias)
        self.assertEqual((progress.xp_total, progress.current_level, progress.current_epoch.code), (700, 8, CODES[6]))
        self.assertEqual(result.progression.crossed_levels, tuple(range(2, 9)))
        self.assertEqual(result.progression.crossed_epoch_codes, CODES[1:])
        self.assertTrue(result.progression.choice_newly_unlocked)
        events = tuple(DemoTargetEvolutionEvent.objects.using(self.alias).order_by("ordinal"))
        self.assertEqual(tuple(e.ordinal for e in events), tuple(range(2, 8)))
        self.assertTrue(all(e.xp_event_id == result.event_id and e.catalog_id == progress.catalog_id for e in events))
        next_result = self.grant(progress, 200)
        self.assertEqual((next_result.progression.level_after, next_result.progression.epoch_after_code), (9, CODES[6]))
        self.assertFalse(next_result.progression.choice_newly_unlocked)
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 6)

    def test_replay_recovers_original_after_later_operation_without_writes_or_a1(self):
        progress = self.new()
        token = self.operation(progress)
        original = self.grant(progress, token=token)
        self.grant(progress, 200)
        before = self.rows()
        with patch.object(services, "plan_target_xp_grant", side_effect=AssertionError("no replay recalculation")), \
                patch.object(services, "exact_catalog", side_effect=AssertionError("no new-use catalog validation")), CaptureQueriesContext(self.db) as queries:
            replay = self.grant(progress, token=token)
        self.assertTrue(replay.replay)
        self.assertEqual(replay.progression, original.progression)
        self.assertEqual(self.rows(), before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))

    def test_reused_key_other_amount_is_conflict(self):
        progress = self.new()
        token = self.operation(progress)
        self.grant(progress, token=token)
        before = self.rows()
        with self.assertRaises(services.DemoConflictError): self.grant(progress, 100, token)
        self.assertEqual(self.rows(), before)

    def test_invalid_amounts_and_overflow_before_writes(self):
        progress = self.new()
        token = self.operation(progress)
        for amount in (0, -1, True, 1.5, "700", None, MAX_XP + 1):
            with self.subTest(amount=amount), self.assertRaises(services.DemoInputError): self.grant(progress, amount, token)
        self.grant(progress, MAX_XP, token)
        before = self.rows()
        with self.assertRaises(services.DemoInputError): self.grant(progress, 1)
        self.assertEqual(self.rows(), before)

    def test_cached_model_state_is_not_trusted(self):
        progress = self.new()
        progress.xp_total, progress.current_level = 999, 99
        result = self.grant(progress, 100)
        self.assertEqual(result.progression.xp_before, 0)
        DemoTargetProgress.objects.using(self.alias).filter(pk=progress.pk).update(current_level=9)
        with self.assertRaises(services.DemoIntegrityError): self.grant(progress, 1)

    def test_outer_transaction_rejected(self):
        progress = self.new()
        token = self.operation(progress)
        with transaction.atomic(using=self.alias):
            with self.assertRaises(services.DemoTransactionError): self.grant(progress, token=token)

    def test_rollback_on_progress_update_failure(self):
        progress = self.new()
        token = self.operation(progress)
        before = self.rows()
        with patch.object(DemoTargetProgress, "save", side_effect=OperationalError("synthetic")):
            with self.assertRaises(services.DemoDatabaseError): self.grant(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_rollback_after_partial_evolution_creation(self):
        progress = self.new()
        token = self.operation(progress)
        before = self.rows()
        from django.db.models.query import QuerySet
        original = QuerySet.create
        counter = 0
        def fail(query, **kwargs):
            nonlocal counter
            if query.model is DemoTargetEvolutionEvent:
                counter += 1
                if counter == 3: raise IntegrityError("synthetic third evolution")
            return original(query, **kwargs)
        with patch.object(QuerySet, "create", fail):
            with self.assertRaises(services.DemoIntegrityError): self.grant(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_session_ownership_and_server_operation_identity(self):
        progress = self.new()
        token = self.operation(progress)
        with self.assertRaises(services.DemoAccessError): self.grant(progress, token=token, secret=OTHER)
        other = self.new(OTHER)
        with self.assertRaises(services.DemoAccessError): self.grant(other, token=token, secret=OTHER)
        with self.assertRaises(services.DemoAccessError): services.read_demo_progress(progress.pk, session_token=OTHER)
        for bad in ("fake", token + "x", signing.dumps({"progress": True, "owner": "x", "key": "x"}, salt=services.SALT)):
            with self.subTest(token=bad), self.assertRaises(services.DemoAccessError): self.grant(progress, token=bad)

    def test_database_uniqueness_checks_and_protected_fks(self):
        progress = self.new()
        result = self.grant(progress)
        event = DemoTargetXPEvent.objects.using(self.alias).get(pk=result.event_id)
        values = {field.attname: getattr(event, field.attname) for field in event._meta.fields if field.name not in ("id", "created_at")}
        with self.assertRaises(IntegrityError): DemoTargetXPEvent.objects.using(self.alias).create(**values)
        with self.assertRaises(IntegrityError): DemoTargetProgress.objects.using(self.alias).filter(pk=progress.pk).update(xp_total=-1)
        evo = DemoTargetEvolutionEvent.objects.using(self.alias).first()
        with self.assertRaises(IntegrityError):
            DemoTargetEvolutionEvent.objects.using(self.alias).create(progress=progress, xp_event=event,
                catalog_id=progress.catalog_id, epoch_id=evo.epoch_id, ordinal=evo.ordinal)
        with self.assertRaises(IntegrityError), transaction.atomic(using=self.alias):
            DemoTargetProgress.objects.using(self.alias).filter(pk=progress.pk).update(current_epoch_id=999999)
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError): progress.delete(using=self.alias)

    def test_contradictory_history_not_replayed(self):
        progress = self.new()
        token = self.operation(progress)
        result = self.grant(progress, token=token)
        DemoTargetEvolutionEvent.objects.using(self.alias).filter(xp_event_id=result.event_id).first().delete(using=self.alias)
        with self.assertRaises(services.DemoIntegrityError): self.grant(progress, token=token)

    def test_reopening_file_preserves_progress_and_replay(self):
        progress = self.new()
        token = self.operation(progress)
        original = self.grant(progress, token=token)
        self.db.close()
        reopened, xp, evolutions = services.read_demo_progress(progress.pk, session_token=SECRET)
        self.assertEqual((reopened.xp_total, len(xp), len(evolutions)), (700, 1, 6))
        self.assertEqual(self.grant(reopened, token=token).progression, original.progression)

    def test_http_refresh_replay_and_restart_preserve_old_history(self):
        self.assertEqual(self.http_start().status_code, 200)
        data = self.http_data()
        self.assertEqual(self.client.post(URL, data).status_code, 302)
        for _ in range(2): self.assertEqual(self.client.get(URL).status_code, 200)
        self.assertEqual(self.client.post(URL, data).status_code, 302)
        response = self.client.get(URL)
        self.assertIn("Operación histórica recuperada", response.content.decode())
        self.assertIn('id="xp-total">700<', response.content.decode())
        self.assertIn("12 OPCIONES DESBLOQUEADAS", response.content.decode())
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 1)
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 6)
        self.assertEqual(self.client.post(URL, {"action": "start"}).status_code, 302)
        self.assertEqual(DemoTargetProgress.objects.using(self.alias).count(), 2)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 1)
        self.assertEqual(self.client.post(URL, data).status_code, 403)

    def test_another_browser_cannot_consume_operation_or_inject_game_id(self):
        self.http_start()
        data = self.http_data()
        other = Client()
        self.http_start(other)
        self.assertEqual(other.post(URL, data).status_code, 403)
        self.assertEqual(other.get(URL, {"progress": self.client.session["demo_progress"]}).status_code, 400)
        for key in ("progress", "profile_id", "user_id", "level", "catalog", "authorized"):
            with self.subTest(key=key): self.assertEqual(self.client.post(URL, {**data, key: "1"}).status_code, 400)

    def test_http_strict_numbers_duplicates_and_escape(self):
        self.http_start()
        data = self.http_data()
        for amount in ("", "0", "-1", "+1", "1.0", " 1", "1 ", "1e3", "١", "1" * 20, '<script>bad</script>'):
            with self.subTest(amount=amount):
                response = self.client.post(URL, {**data, "amount": amount})
                self.assertEqual(response.status_code, 400)
                self.assertNotIn('<script>bad</script>', response.content.decode())
        for key, value in data.items():
            with self.subTest(duplicate=key):
                response = self.client.post(URL, urlencode([*data.items(), (key, value)]), content_type="application/x-www-form-urlencoded")
                self.assertEqual(response.status_code, 400)

    def test_real_csrf_and_methods(self):
        self.seed()
        client = Client(enforce_csrf_checks=True)
        client.get(URL)
        self.assertEqual(client.post(URL, {"action": "start"}).status_code, 403)
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(client.post(URL, {"action": "start", "csrfmiddlewaretoken": token}).status_code, 302)
        for method in ("put", "patch", "delete", "head", "options"):
            with self.subTest(method=method):
                self.assertEqual(getattr(client, method)(URL, HTTP_X_CSRFTOKEN=token).status_code, 405)

    def test_v1_and_old_demo_are_untouched(self):
        progress = self.new()
        before = self.rows()
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError("V1")):
            self.grant(progress)
        after = self.rows()
        for table, rows in before.items():
            if not table.startswith("ecomotor_target_demo_"):
                self.assertEqual(after[table], rows, table)

    def test_only_migrate_can_create_missing_file(self):
        self.db.close()
        self.path.unlink()
        with self.assertRaises(CommandError): self.seed()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.client.get(URL).status_code, 503)
        self.assertFalse(self.path.exists())
        with self.assertRaises(ImproperlyConfigured): demo_connection()
        self.migrate()
        self.assertTrue(self.path.exists())
        self.seed()

    def test_disappearance_just_before_native_open_does_not_recreate(self):
        self.db.close()
        backup = self.root / "synthetic-backup.sqlite3"
        copyfile(self.path, backup)
        from django.db.backends.sqlite3.base import DatabaseWrapper
        original = DatabaseWrapper.get_new_connection
        configuration = self.db.settings_dict
        for action in ("seed", "http"):
            with self.subTest(action=action):
                if not self.path.exists(): copyfile(backup, self.path)
                def disappear(wrapper, params):
                    self.assertTrue(params["database"].endswith("?mode=rw"))
                    self.path.unlink()
                    return original(wrapper, params)
                # At the last step, after both backend path checks, before the
                # native SQLite open: only mode=rw can prevent recreation here.
                with patch.object(DatabaseWrapper, "get_new_connection", disappear):
                    if action == "seed":
                        with self.assertRaises(CommandError): self.seed()
                    else:
                        self.assertEqual(self.client.get(URL).status_code, 503)
                self.assertFalse(self.path.exists())
                self.assertIsNone(self.db.connection)
                self.assertIs(self.db.settings_dict, configuration)

    def test_hardlinks_to_either_habitual_database_rejected_including_migrate(self):
        self.db.close()
        for name in (self.root / "db.sqlite3", self.root / "instance" / "target_demo.sqlite3"):
            with self.subTest(name=name):
                if name.exists(): name.unlink()
                self.path.rename(name)
                self.path.hardlink_to(name)
                before = sha256(name.read_bytes()).hexdigest()
                with self.assertRaises(CommandError): self.migrate()
                with self.assertRaises(CommandError): self.seed()
                self.assertEqual(self.client.get(URL).status_code, 503)
                self.assertEqual(sha256(name.read_bytes()).hexdigest(), before)
                self.path.unlink()
                name.rename(self.path)

    def test_symlink_rejection_including_migrate_without_platform_privileges(self):
        self.db.close()
        original = Path.is_symlink
        before = sha256(self.path.read_bytes()).hexdigest()
        with patch.object(Path, "is_symlink", lambda p: p == self.path or original(p)):
            with self.assertRaises(CommandError): self.migrate()
            with self.assertRaises(CommandError): self.seed()
            self.assertEqual(self.client.get(URL).status_code, 503)
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_incompatible_name_and_effective_connection_rejected(self):
        self.db.close()
        other = self.root / "other.sqlite3"
        copyfile(self.path, other)
        before = sha256(other.read_bytes()).hexdigest()
        with patch.dict(self.db.settings_dict, NAME=other):
            with self.assertRaises(CommandError): self.migrate()
            self.assertEqual(self.client.get(URL).status_code, 503)
        self.db.connection = sqlite3.connect(other)
        with self.assertRaises(ImproperlyConfigured): demo_connection()
        self.db.close()
        self.assertEqual(sha256(other.read_bytes()).hexdigest(), before)

    def test_migrate_again_preserves_existing_catalog_and_history(self):
        progress = self.new()
        self.grant(progress)
        before = self.rows()
        self.migrate()
        self.assertEqual(self.rows(), before)

    def test_http_session_reopened_in_another_client_keeps_progress(self):
        self.http_start()
        self.client.post(URL, self.http_data())
        browser = Client()
        browser.cookies = self.client.cookies.copy()
        self.db.close()
        response = browser.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="xp-total">700<', response.content.decode())
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 6)

    def test_http_operation_stable_before_grant_and_conflict_after(self):
        self.http_start()
        original = self.http_data()
        self.client.get(URL)
        self.assertEqual(self.http_data(), original)
        self.client.post(URL, original)
        self.client.get(URL)
        self.assertNotEqual(self.http_data()["operation"], original["operation"])
        self.assertEqual(self.client.post(URL, {**original, "amount": "100"}).status_code, 409)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 1)

    def test_rollback_on_xp_event_creation_failure(self):
        progress = self.new()
        token = self.operation(progress)
        before = self.rows()
        from django.db.models.query import QuerySet
        original = QuerySet.create
        def fail(query, **values):
            if query.model is DemoTargetXPEvent: raise OperationalError("synthetic create failure")
            return original(query, **values)
        with patch.object(QuerySet, "create", fail):
            with self.assertRaises(services.DemoDatabaseError): self.grant(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_foreign_evolution_cause_is_rejected_on_replay(self):
        progress = self.new()
        other = self.new(OTHER)
        token = self.operation(progress)
        result = self.grant(progress, token=token)
        DemoTargetEvolutionEvent.objects.using(self.alias).filter(xp_event_id=result.event_id).update(progress_id=other.pk)
        with self.assertRaises(services.DemoIntegrityError): self.grant(progress, token=token)

    def test_invalid_catalog_epoch_on_progress_blocks_new_grant(self):
        progress = self.new()
        later = TargetEpoch.objects.using(self.alias).get(catalog_id=progress.catalog_id, ordinal=7)
        DemoTargetProgress.objects.using(self.alias).filter(pk=progress.pk).update(current_epoch=later)
        token = self.operation(progress)
        with self.assertRaises(services.DemoIntegrityError): self.grant(progress, token=token)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 0)

    def test_no_user_or_selection_relationships_in_demo_schema(self):
        for model in (DemoTargetProgress, DemoTargetXPEvent, DemoTargetEvolutionEvent):
            for field in model._meta.fields:
                if field.is_relation:
                    self.assertIn(field.related_model._meta.app_label, ("ecomotor", "ecomotor_target_demo"))
        from apps.ecomotor import target_persistent_demo_settings as production
        self.assertEqual(production.SESSION_COOKIE_NAME, "target_persistent_demo_session")
        self.assertEqual(production.CSRF_COOKIE_PATH, URL)

    def test_missing_seed_does_not_auto_install_by_http(self):
        before = self.rows()
        self.assertEqual(self.client.get(URL).status_code, 200)
        self.assertEqual(self.client.post(URL, {"action": "start"}).status_code, 503)
        self.assertEqual(self.rows(), before)

    def test_live_file_identity_change_is_rejected(self):
        before = self.rows()
        with patch.object(self.db, "_demo_file_identity", (-1, -1)):
            with self.assertRaises(ImproperlyConfigured): demo_connection()
            self.assertEqual(self.client.get(URL).status_code, 503)
            with self.assertRaises(CommandError): self.seed()
        self.assertEqual(self.rows(), before)

    def test_no_foreign_history_disclosed_through_corrupt_cause(self):
        own = self.new()
        foreign = self.new(OTHER)
        result = self.grant(foreign, secret=OTHER)
        evo = DemoTargetEvolutionEvent.objects.using(self.alias).filter(xp_event_id=result.event_id).first()
        DemoTargetEvolutionEvent.objects.using(self.alias).filter(pk=evo.pk).update(progress_id=own.pk)
        with self.assertRaises(services.DemoIntegrityError): services.read_demo_progress(own.pk, session_token=SECRET)


class PersistentConcurrencyTests(PersistentTests):
    # Avoid inheriting the functional tests a second time; see load_tests below.
    def race(self, *, same_key):
        progress = self.new()
        first = self.operation(progress)
        second = first if same_key else self.operation(progress)
        barrier = Barrier(2)
        def worker(token, amount):
            db = connections[self.alias]
            try:
                barrier.wait(timeout=10)
                result = services.grant_demo_target_xp(progress, amount=amount, operation_token=token, session_token=SECRET)
                return result, id(db.connection)
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(worker, first, 100)
            b = pool.submit(worker, second, 100 if same_key else 200)
            results = (a.result(timeout=15), b.result(timeout=15))
        self.assertNotEqual(results[0][1], results[1][1])
        progress.refresh_from_db(using=self.alias)
        self.assertEqual(progress.xp_total, 100 if same_key else 300)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 1 if same_key else 2)
        self.assertEqual(sum(r[0].replay for r in results), 1 if same_key else 0)

    def test_real_same_key_concurrency(self): self.race(same_key=True)
    def test_real_different_keys_concurrency(self): self.race(same_key=False)

    def test_real_timeout_and_explicit_retry_new_transaction(self):
        progress = self.new()
        token = self.operation(progress)
        held, release = Event(), Event()
        def blocker():
            db = connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    held.set()
                    if not release.wait(12): raise AssertionError("test synchronization timeout")
            finally: db.close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(blocker)
            self.assertTrue(held.wait(5))
            started = monotonic()
            try:
                with self.assertRaises(services.DemoBusyError) as error: self.grant(progress, token=token)
                self.assertIsInstance(error.exception.__cause__, OperationalError)
                self.assertGreaterEqual(monotonic() - started, 4.5)
            finally: release.set()
            future.result(timeout=5)
        self.assertFalse(self.db.in_atomic_block)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 0)
        self.assertEqual(self.grant(progress, token=token).progression.xp_after, 700)

    def test_transaction_begins_immediate_before_mutable_read(self):
        progress = self.new()
        token = self.operation(progress)
        with CaptureQueriesContext(self.db) as queries:
            self.grant(progress, token=token)
        sql = [q["sql"].upper() for q in queries]
        self.assertIn("BEGIN IMMEDIATE", sql)
        first = next(i for i, text in enumerate(sql) if text.startswith("SELECT"))
        self.assertLess(sql.index("BEGIN IMMEDIATE"), first)


def load_tests(loader, suite, pattern):
    # Explicit, predictable discovery under exclusive settings only. Keep the
    # shared fixture without rerunning inherited functional methods twice.
    import unittest
    selected = unittest.TestSuite(loader.loadTestsFromTestCase(PersistentTests))
    for name in PersistentConcurrencyTests.__dict__:
        if name.startswith("test_"):
            selected.addTest(PersistentConcurrencyTests(name))
    return selected
