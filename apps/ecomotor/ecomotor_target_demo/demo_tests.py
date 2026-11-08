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
if not apps.is_installed("apps.ecomotor.ecomotor_target_demo"):
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
                  "ENGINE": "apps.ecomotor.ecomotor_target_demo.db_backend", "NAME": self.path,
                  "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5}}
        connections.databases[self.alias] = config
        self.db = connections[self.alias]
        self.addCleanup(self.close)
        context = override_settings(BASE_DIR=self.root, TARGET_PERSISTENT_DEMO_ALIAS=self.alias,
            ROOT_URLCONF="apps.ecomotor.ecomotor_target_demo.urls")
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
        migration = import_module("apps.ecomotor.ecomotor_target_demo.migrations.0001_initial").Migration
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

    def test_only_explicit_nullable_synthetic_user_relationship_in_demo_schema(self):
        from django.contrib.auth import get_user_model
        for model in (DemoTargetProgress, DemoTargetXPEvent, DemoTargetEvolutionEvent):
            for field in model._meta.fields:
                if field.is_relation:
                    if model is DemoTargetProgress and field.name == "synthetic_user":
                        self.assertIs(field.related_model, get_user_model())
                        self.assertTrue(field.one_to_one and field.null)
                        self.assertEqual(field.remote_field.on_delete.__name__, "PROTECT")
                        continue
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



from dataclasses import FrozenInstanceError
from decimal import Decimal
from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES, InvalidTargetStatsError
from . import playable_services as playable
from .models import DemoTargetOptionConfiguration as Configuration, DemoTargetPlayableState as PlayableState, DemoTargetPlayableEvent as PlayableEvent
from .data import OPTION_CODES

GAMER = OPTION_CODES[-1]
ROMAN = OPTION_CODES[2]


def allocation(points=45):
    return tuple((code, points if code == "ATK" else 0) for code in TARGET_STAT_CODES)


class PlayableTests(PersistentTests):
    def ready(self):
        progress = self.new()
        self.grant(progress)
        return progress

    def token(self, progress, action="configure", secret=SECRET):
        return playable.issue_playable_operation(progress, action=action, session_token=secret)

    def configure(self, progress, code=GAMER, points=45, revision=None, token=None, secret=SECRET):
        return playable.configure_demo_option(progress, option_code=code, increments=allocation(points),
            expected_revision=revision, operation_token=token or self.token(progress, secret=secret), session_token=secret)

    def switch(self, progress, code, revision, token=None):
        return playable.switch_demo_option(progress, option_code=code, expected_revision=revision,
            operation_token=token or self.token(progress, "switch"), session_token=SECRET)

    def redistribute(self, progress, points=20, revision=1, config_revision=1, token=None):
        return playable.redistribute_demo_option(progress, option_code=GAMER, increments=allocation(points),
            expected_revision=revision, configuration_revision=config_revision,
            operation_token=token or self.token(progress, "redistribute"), session_token=SECRET)

    def test_migration_two_dependency_and_existing_xp_preserved(self):
        progress = self.ready()
        call_command("migrate", "ecomotor_target_demo", "0001", database=self.alias, verbosity=0, stdout=StringIO())
        self.migrate()
        migration = import_module("apps.ecomotor.ecomotor_target_demo.migrations.0002_playable_configurations").Migration
        self.assertEqual(migration.dependencies, [("ecomotor", "0007_target_catalog_freeze"),
                                                  ("ecomotor_target_demo", "0001_initial")])
        self.assertFalse(any(type(op).__name__ == "RunPython" for op in migration.operations))
        observed, xp_events, evolutions = services.read_demo_progress(progress.pk, session_token=SECRET)
        self.assertEqual((observed.xp_total, len(xp_events), len(evolutions)), (700, 1, 6))
        self.assertEqual(Configuration.objects.using(self.alias).count(), 0)

    def test_selection_blocked_before_eight_without_writes(self):
        progress = self.new()
        token = self.token(progress)
        before = self.rows()
        with self.assertRaises(services.DemoInputError): self.configure(progress, token=token)
        self.assertEqual(before, self.rows())

    def test_twelve_options_and_full_partial_zero_independent(self):
        progress = self.ready()
        self.assertEqual(len(OPTION_CODES), 12)
        for n, code in enumerate(OPTION_CODES):
            result = self.configure(progress, code, (45, 13, 0)[n % 3], revision=n or None)
            self.assertEqual(result.after.revision, n + 1)
            self.assertEqual(result.after.active_option, code)
            config = next(c for c in result.after.configurations if c.prepared.definition.option_code == code)
            self.assertEqual(config.prepared.calculation.points_used, (45, 13, 0)[n % 3])
        self.assertEqual(Configuration.objects.using(self.alias).count(), 12)
        self.assertEqual(PlayableState.objects.using(self.alias).count(), 1)

    def test_main_gamer_roman_switch_redistribute_reopen(self):
        progress = self.ready()
        first = self.configure(progress)
        second = self.configure(progress, ROMAN, 10, revision=1)
        switched = self.switch(progress, GAMER, 2)
        updated = self.redistribute(progress, 24, revision=3)
        self.assertEqual((first.after.revision, second.after.revision, switched.after.revision, updated.after.revision), (1, 2, 3, 4))
        self.db.close()
        state, history = playable.read_demo_playable(progress, session_token=SECRET)
        gamer = playable._find(state, GAMER)
        roman = playable._find(state, ROMAN)
        self.assertEqual((state.active_option, gamer.revision, roman.revision), (GAMER, 2, 1))
        self.assertEqual((gamer.prepared.calculation.points_used, roman.prepared.calculation.points_used), (24, 10))
        self.assertEqual((gamer.prepared.definition, gamer.prepared.calculation.budget),
                         (first.after.configurations[0].prepared.definition, 45))
        self.assertEqual(len(history), 4)
        progress.refresh_from_db(using=self.alias)
        self.assertEqual((progress.xp_total, DemoTargetXPEvent.objects.using(self.alias).count(), DemoTargetEvolutionEvent.objects.using(self.alias).count()), (700, 1, 6))

    def test_invalid_allocations_and_overflow_leave_no_partial_state(self):
        progress = self.ready()
        token = self.token(progress)
        invalid = [allocation(46), allocation(-1), allocation(True), allocation(1.0), allocation(Decimal(1)),
                   allocation("1"), allocation(MAX_XP+1), allocation()[:-1], allocation()+(("SPE", 0),), allocation()+(("ATK", 0),)]
        for pairs in invalid:
            before = self.rows()
            with self.subTest(pairs=pairs), self.assertRaises(InvalidTargetStatsError):
                playable.configure_demo_option(progress, option_code=GAMER, increments=pairs, operation_token=token, session_token=SECRET)
            self.assertEqual(self.rows(), before)

    def test_revision_first_even_active_target_and_noop_no_writes(self):
        progress = self.ready()
        self.configure(progress)
        before = self.rows()
        for revision in (None, 0, True, "1", 2):
            with self.subTest(revision=revision), self.assertRaises((services.DemoInputError, playable.DemoRevisionError)):
                self.switch(progress, GAMER, revision)
        with CaptureQueriesContext(self.db) as queries:
            result = self.switch(progress, GAMER, 1)
            same = self.redistribute(progress, 45)
        self.assertFalse(result.changed)
        self.assertFalse(same.changed)
        self.assertIsNone(result.event_id)
        self.assertEqual(self.rows(), before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))

    def test_old_configuration_and_state_revisions_rejected(self):
        progress = self.ready()
        self.configure(progress)
        self.redistribute(progress)
        before = self.rows()
        with self.assertRaises(playable.DemoRevisionError): self.redistribute(progress, revision=1)
        with self.assertRaises(playable.DemoRevisionError): self.redistribute(progress, revision=2, config_revision=1)
        self.assertEqual(self.rows(), before)

    def test_replay_create_after_later_operations_and_conflict(self):
        progress = self.ready()
        token = self.token(progress)
        first = self.configure(progress, token=token)
        self.configure(progress, ROMAN, 0, revision=1)
        before = self.rows()
        with patch.object(playable, "synthetic_definition", side_effect=AssertionError("future definitions are irrelevant")):
            replay = self.configure(progress, token=token)
        self.assertTrue(replay.replay)
        self.assertEqual((replay.before, replay.after), (first.before, first.after))
        self.assertFalse(replay.changed)
        for code, points, revision in ((ROMAN, 45, None), (GAMER, 44, None), (GAMER, 45, 2)):
            with self.assertRaises(services.DemoConflictError): self.configure(progress, code, points, revision, token)
        self.assertEqual(self.rows(), before)

    def test_redistribution_historical_replay_after_later_change(self):
        progress = self.ready()
        self.configure(progress)
        token = self.token(progress, "redistribute")
        first = self.redistribute(progress, 12, token=token)
        self.redistribute(progress, 30, revision=2, config_revision=2)
        before = self.rows()
        replay = self.redistribute(progress, 12, token=token)
        self.assertTrue(replay.replay)
        self.assertEqual(replay.after, first.after)
        with self.assertRaises(services.DemoConflictError): self.redistribute(progress, 13, token=token)
        self.assertEqual(before, self.rows())

    def test_old_switch_form_is_stale_not_historical_change(self):
        progress = self.ready()
        self.configure(progress)
        self.configure(progress, ROMAN, revision=1)
        token = self.token(progress, "switch")
        self.switch(progress, GAMER, 2, token)
        before = self.rows()
        with self.assertRaises(playable.DemoRevisionError): self.switch(progress, GAMER, 2, token)
        self.assertEqual(before, self.rows())

    def test_existing_configuration_never_overwritten_by_configure(self):
        progress = self.ready()
        self.configure(progress)
        before = self.rows()
        with self.assertRaises(services.DemoConflictError): self.configure(progress, points=0, revision=1)
        self.assertEqual(self.rows(), before)

    def test_missing_config_cannot_switch_or_redistribute(self):
        progress = self.ready()
        self.configure(progress, ROMAN)
        with self.assertRaises(services.DemoInputError): self.switch(progress, GAMER, 1)
        with self.assertRaises(services.DemoInputError): self.redistribute(progress)

    def test_session_and_purpose_isolation(self):
        progress = self.ready()
        token = self.token(progress)
        with self.assertRaises(services.DemoAccessError): self.configure(progress, token=token, secret=OTHER)
        with self.assertRaises(services.DemoAccessError): self.configure(progress, token=self.operation(progress))
        with self.assertRaises(services.DemoAccessError): self.configure(progress, token=self.token(progress, "switch"))
        with self.assertRaises(services.DemoAccessError): playable.read_demo_playable(progress, session_token=OTHER)
        other = self.new(OTHER)
        with self.assertRaises(services.DemoAccessError): self.configure(other, token=token, secret=OTHER)

    def test_rollback_on_each_partial_write(self):
        progress = self.ready()
        token = self.token(progress)
        before = self.rows()
        for model in (Configuration, PlayableState, PlayableEvent):
            with self.subTest(model=model), patch.object(model, "save", side_effect=IntegrityError("synthetic")):
                with self.assertRaises(services.DemoIntegrityError): self.configure(progress, token=token)
            self.assertEqual(self.rows(), before)
        self.configure(progress, token=token)
        before = self.rows()
        with patch.object(PlayableEvent, "save", side_effect=OperationalError("synthetic")):
            with self.assertRaises(services.DemoDatabaseError): self.redistribute(progress)
        self.assertEqual(self.rows(), before)

    def test_corrupt_history_and_current_config_rejected(self):
        progress = self.ready()
        token = self.token(progress)
        self.configure(progress, token=token)
        event = PlayableEvent.objects.using(self.alias).get()
        original = event.after
        bad = {**original, "revision": 2}
        PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=bad)
        with self.assertRaises(services.DemoIntegrityError): self.configure(progress, token=token)
        PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=original)
        Configuration.objects.using(self.alias).filter(progress=progress).update(increments=[["ATK", True]])
        with self.assertRaises(services.DemoIntegrityError): playable.read_demo_playable(progress, session_token=SECRET)

    def test_foreign_active_config_detected(self):
        own = self.ready()
        self.configure(own)
        foreign = self.ready()
        self.configure(foreign)
        other_config = Configuration.objects.using(self.alias).get(progress=foreign)
        PlayableState.objects.using(self.alias).filter(progress=own).update(active_configuration=other_config)
        with self.assertRaises(services.DemoIntegrityError): playable.read_demo_playable(own, session_token=SECRET)

    def test_models_constraints_and_no_user_ducky_relations(self):
        progress = self.ready()
        self.configure(progress)
        config = Configuration.objects.using(self.alias).get()
        values = {f.attname: getattr(config, f.attname) for f in config._meta.fields if f.name not in ("id", "created_at", "updated_at")}
        with self.assertRaises(IntegrityError): Configuration.objects.using(self.alias).create(**values)
        for changes in ({"revision": 0}, {"budget": -1}, {"option_code": ""}, {"definition_version": ""}):
            with self.assertRaises(IntegrityError): Configuration.objects.using(self.alias).filter(pk=config.pk).update(**changes)
        for model in (Configuration, PlayableState, PlayableEvent):
            for field in model._meta.fields:
                if field.is_relation:
                    self.assertIn(field.related_model._meta.app_label, ("ecomotor", "ecomotor_target_demo"))
                    self.assertEqual(field.remote_field.on_delete.__name__, "PROTECT")
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError): config.delete(using=self.alias)

    def test_immutable_result_and_input_copies(self):
        progress = self.ready()
        pairs = [list(p) for p in allocation()]
        result = playable.configure_demo_option(progress, option_code=GAMER, increments=pairs,
            operation_token=self.token(progress), session_token=SECRET)
        pairs[0][1] = 0
        self.assertEqual(result.after.configurations[0].prepared.calculation.points_used, 45)
        for obj, key in ((result, "action"), (result.after, "revision"), (result.after.configurations[0], "revision")):
            with self.assertRaises((FrozenInstanceError, AttributeError)): setattr(obj, key, 0)
            self.assertFalse(hasattr(obj, "__dict__"))

    def test_xp_and_foreign_apps_unchanged_and_public_a4_used(self):
        progress = self.ready()
        before = self.rows()
        from . import stats_definitions
        import apps.ecomotor.target_stats_preparation as preparation
        with patch.object(playable, "prepare_target_stats_configuration", wraps=preparation.prepare_target_stats_configuration) as prepare, patch.object(stats_definitions, "validate_target_stats_definition", wraps=stats_definitions.validate_target_stats_definition) as definition, patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError("V1")):
            self.configure(progress)
            self.redistribute(progress)
        self.assertTrue(prepare.called)
        self.assertTrue(definition.called)
        after = self.rows()
        allowed = {Configuration._meta.db_table, PlayableState._meta.db_table, PlayableEvent._meta.db_table}
        self.assertTrue(all(rows == after[table] for table, rows in before.items() if table not in allowed))

    def test_outer_transaction_and_cached_progress_rejected_or_reloaded(self):
        progress = self.ready()
        token = self.token(progress)
        with transaction.atomic(using=self.alias):
            with self.assertRaises(services.DemoTransactionError): self.configure(progress, token=token)
        progress.current_level = 1
        self.assertTrue(self.configure(progress, token=token).changed)

    def playable_http(self, *, action="configure", option=GAMER, revision="", config_revision="1", points="45"):
        progress = DemoTargetProgress.objects.using(self.alias).get(pk=self.client.session["demo_progress"])
        secret = self.client.session["demo_secret"]
        data = {"action": action, "operation": self.token(progress, action, secret), "option_code": option, "expected_revision": revision}
        if action != "switch": data.update({code: points if code == "ATK" else "0" for code in TARGET_STAT_CODES})
        if action == "redistribute": data["configuration_revision"] = config_revision
        return data

    def http_ready(self):
        self.http_start()
        self.assertEqual(self.client.post(URL, self.http_data()).status_code, 302)

    def test_http_main_workflow_persistence_and_historical_replay(self):
        self.http_ready()
        gamer = self.playable_http()
        self.assertEqual(self.client.post(URL, gamer).status_code, 302)
        self.assertEqual(self.client.post(URL, self.playable_http(option=ROMAN, revision="1", points="12")).status_code, 302)
        self.assertEqual(self.client.post(URL, self.playable_http(action="switch", revision="2")).status_code, 302)
        self.assertEqual(self.client.post(URL, self.playable_http(action="redistribute", revision="3", points="23")).status_code, 302)
        self.db.close()
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("23 usados / 22 restantes", response.content.decode())
        self.assertIn("45 puntos provisionales", response.content.decode())
        self.assertEqual(self.client.post(URL, gamer).status_code, 302)
        self.assertEqual(PlayableEvent.objects.using(self.alias).count(), 4)
        self.assertEqual(Configuration.objects.using(self.alias).count(), 2)
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 6)

    def test_http_strict_fields_duplicates_ascii_and_escape(self):
        self.http_ready()
        data = self.playable_http()
        for invalid in ("-1", "1.0", "+1", " 1", "1 ", "١", "1e2", "1"*20, "", "<script>x</script>"):
            response = self.client.post(URL, {**data, "ATK": invalid})
            self.assertEqual(response.status_code, 400, invalid)
            self.assertNotIn("<script>x</script>", response.content.decode())
        for key in ("budget", "bases", "profile_id", "catalog", "level", "SPE", "authorized"):
            self.assertEqual(self.client.post(URL, {**data, key: "1"}).status_code, 400)
        for key, value in data.items():
            self.assertEqual(self.client.post(URL, urlencode([*data.items(), (key, value)]), content_type="application/x-www-form-urlencoded").status_code, 400)
        missing = dict(data)
        missing.pop("VEL")
        self.assertEqual(self.client.post(URL, missing).status_code, 400)
        self.assertEqual(Configuration.objects.using(self.alias).count(), 0)

    def test_http_csrf_another_session_and_get_no_configuration_write(self):
        self.http_ready()
        data = self.playable_http()
        guarded = Client(enforce_csrf_checks=True)
        guarded.cookies = self.client.cookies.copy()
        self.assertEqual(guarded.post(URL, data).status_code, 403)
        response = guarded.get(URL)
        csrf = guarded.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(guarded.post(URL, {**data, "csrfmiddlewaretoken": csrf}).status_code, 302)
        other = Client()
        self.http_start(other)
        self.assertEqual(other.post(URL, data).status_code, 403)
        before = self.rows()
        self.assertEqual(guarded.get(URL).status_code, 200)
        self.assertEqual(self.rows(), before)


class PlayableConcurrencyTests(PlayableTests):
    def race_playable(self, same):
        progress = self.ready()
        token = self.token(progress)
        other = token if same else self.token(progress)
        barrier = Barrier(2)
        def worker(key, code):
            db = connections[self.alias]
            try:
                barrier.wait(timeout=10)
                try:
                    result = self.configure(progress, code, token=key)
                except playable.DemoRevisionError as error:
                    result = error
                return result, id(db.connection)
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(worker, token, GAMER)
            b = pool.submit(worker, other, GAMER if same else ROMAN)
            results = (a.result(timeout=20), b.result(timeout=20))
        self.assertNotEqual(results[0][1], results[1][1])
        self.assertEqual(Configuration.objects.using(self.alias).count(), 1)
        self.assertEqual(PlayableEvent.objects.using(self.alias).count(), 1)
        if same: self.assertEqual(sum(r[0].replay for r in results), 1)
        else: self.assertEqual(sum(isinstance(r[0], playable.DemoRevisionError) for r in results), 1)

    def test_concurrent_same_playable_identity(self): self.race_playable(True)
    def test_concurrent_different_options_revision_serialization(self): self.race_playable(False)

    def test_xp_and_selection_concurrent_independent_histories(self):
        progress = self.ready()
        token = self.token(progress)
        xp_token = self.operation(progress)
        barrier = Barrier(2)
        def worker(kind):
            db = connections[self.alias]
            try:
                barrier.wait(timeout=10)
                if kind == "xp": return self.grant(progress, 200, xp_token)
                return self.configure(progress, token=token)
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = pool.submit(worker, "xp"), pool.submit(worker, "playable")
            a.result(timeout=20)
            b.result(timeout=20)
        progress.refresh_from_db(using=self.alias)
        self.assertEqual(progress.xp_total, 900)
        self.assertEqual((Configuration.objects.using(self.alias).count(), DemoTargetEvolutionEvent.objects.using(self.alias).count()), (1, 6))
        playable.read_demo_playable(progress, session_token=SECRET)

    def test_playable_timeout_no_partial_write_then_explicit_retry(self):
        progress = self.ready()
        token = self.token(progress)
        held, release = Event(), Event()
        def blocker():
            db = connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    held.set()
                    if not release.wait(12): raise AssertionError("synchronization timeout")
            finally: db.close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(blocker)
            self.assertTrue(held.wait(5))
            try:
                started = monotonic()
                with self.assertRaises(services.DemoBusyError): self.configure(progress, token=token)
                self.assertGreaterEqual(monotonic() - started, 4.5)
            finally: release.set()
            future.result(timeout=5)
        self.assertFalse(self.db.in_atomic_block)
        self.assertEqual(Configuration.objects.using(self.alias).count(), 0)
        self.assertTrue(self.configure(progress, token=token).changed)


from datetime import timedelta
from . import reward_demo_services as rewards, reward_demo_rules as reward_rules
from .models import DemoTargetRewardEvent as RewardEvent
from apps.ecomotor.reward_types import RewardDecision, RewardRuleSet, ProposedEffect


class RewardTests(PlayableTests):
    def test_unprovisioned_bank_read_keeps_historical_alias_and_no_writes(self):
        progress = self.new()
        before = self.rows()
        with patch.object(rewards.bank_service, "wallet_summary", side_effect=AssertionError("no Wallet")), patch.object(rewards.bank_service, "transaction_history", side_effect=AssertionError("no Wallet")), CaptureQueriesContext(self.db) as queries:
            overview = rewards.read_demo_bank(progress, session_token=SECRET)
        self.assertEqual((overview.provisioned, overview.balance, overview.movements), (False, None, ()))
        self.assertEqual(self.rows(), before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")) for q in queries))

    def test_coin_alias_rejected_before_writes_and_bank(self):
        progress = self.new()
        token = self.fact_token(progress, "coin_challenge")
        before = self.rows()
        with patch.object(rewards.bank_service, "credit_coins", side_effect=AssertionError("wrong alias")) as credit, CaptureQueriesContext(self.db) as queries:
            with self.assertRaises(services.DemoTransactionError):
                self.reward(progress, "coin_challenge", token)
        credit.assert_not_called()
        self.assertEqual(self.rows(), before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")) for q in queries))

    def fact_token(self, progress, activity="challenge", secret=SECRET):
        return rewards.issue_reward_fact(progress, activity=activity, session_token=secret)

    def reward(self, progress, activity="challenge", token=None, secret=SECRET):
        return rewards.apply_demo_reward(progress, activity=activity,
            fact_token=token or self.fact_token(progress, activity, secret), session_token=secret)

    def incompatible(self, token, **changes):
        payload = signing.loads(token, salt=rewards.SALT)
        payload.update(changes)
        return signing.dumps(payload, salt=rewards.SALT)

    def test_f1_applied_seven_hundred_six_causal_evolutions(self):
        progress = self.new()
        with patch.object(rewards, "evaluate_reward", wraps=rewards.evaluate_reward) as evaluate, patch.object(rewards, "semantic_fingerprint", wraps=rewards.semantic_fingerprint) as fingerprint:
            result = self.reward(progress)
        self.assertTrue(evaluate.called)
        self.assertTrue(fingerprint.called)
        self.assertIsInstance(result.decision, RewardDecision)
        self.assertEqual((result.status, result.xp_amount, result.progression.xp_before, result.progression.xp_after), ("APPLIED", 700, 0, 700))
        self.assertEqual(result.progression.level_after, 8)
        self.assertEqual(len(result.evolution_ids), 6)
        self.assertTrue(result.progression.choice_newly_unlocked)
        row = RewardEvent.objects.using(self.alias).get()
        self.assertEqual(row.xp_event_id, result.xp_event_id)
        event = DemoTargetXPEvent.objects.using(self.alias).get()
        self.assertEqual(event.operation_key, rewards._xp_key(result.identity))
        self.assertEqual(len(event.operation_key), 32)
        self.assertTrue(event.operation_key.startswith("rx1:"))
        self.assertEqual(PlayableState.objects.using(self.alias).count(), 0)

    def test_visit_no_reward_without_xp_core_or_evolutions(self):
        progress = self.new()
        with patch.object(services, "_grant_xp_in_transaction", side_effect=AssertionError("visit cannot grant")):
            result = self.reward(progress, "visit")
        self.assertEqual((result.status, result.xp_amount, result.xp_event_id, result.evolution_ids), ("NO_REWARD", 0, None, ()))
        self.assertEqual(result.decision.reason_codes, ("NO_MATCHING_RULE",))
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(), 0)
        self.assertEqual(DemoTargetEvolutionEvent.objects.using(self.alias).count(), 0)
        self.assertEqual(RewardEvent.objects.using(self.alias).count(), 1)

    def test_replay_preserves_instant_and_snapshots_without_current_rules(self):
        progress = self.new()
        token = self.fact_token(progress)
        first = self.reward(progress, token=token)
        self.grant(progress, 200)
        before = self.rows()
        with patch.object(rewards, "evaluate_reward", side_effect=AssertionError("historical")), patch.object(reward_rules, "RULE_SET", RewardRuleSet("future-empty", ())), patch.object(services, "plan_target_xp_grant", side_effect=AssertionError("no recalculation")), CaptureQueriesContext(self.db) as queries:
            replay = self.reward(progress, token=token)
        self.assertTrue(replay.replay)
        self.assertEqual(replay.occurred_at, first.occurred_at)
        self.assertEqual(replay.progression, first.progression)
        self.assertEqual(replay.fingerprint, first.fingerprint)
        self.assertEqual(self.rows(), before)
        self.assertFalse(any(q["sql"].upper().lstrip().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))

    def test_no_reward_replay_after_later_xp_uses_original_anchor(self):
        progress = self.new()
        for initial in (0, 100):
            if initial: self.grant(progress, initial)
            token = self.fact_token(progress, "visit")
            first = self.reward(progress, "visit", token)
            self.grant(progress, 200)
            before = self.rows()
            with patch.object(rewards, "evaluate_reward", side_effect=AssertionError("no evaluation")):
                replay = self.reward(progress, "visit", token)
            self.assertEqual(replay.progression, first.progression)
            self.assertEqual(self.rows(), before)
            self.assertTrue(replay.replay)

    def test_same_identity_changed_instant_or_activity_is_conflict(self):
        progress = self.new()
        token = self.fact_token(progress)
        first = self.reward(progress, token=token)
        changed = self.incompatible(token, occurred_at=(first.occurred_at + timedelta(seconds=1)).isoformat(timespec="microseconds"))
        before = self.rows()
        with self.assertRaises(services.DemoConflictError): self.reward(progress, token=changed)
        with self.assertRaises(services.DemoConflictError): self.reward(progress, "visit", self.incompatible(token, activity="visit"))
        self.assertEqual(self.rows(), before)

    def test_unsupported_effects_reject_entire_proposal(self):
        progress = self.new()
        for effects in ((ProposedEffect("COINS", 1),), (ProposedEffect("XP", 700), ProposedEffect("ITEM", 1))):
            before = self.rows()
            decision = RewardDecision("synthetic-unsupported", "rule", True, effects, ())
            with patch.object(rewards, "evaluate_reward", return_value=decision):
                with self.assertRaises(rewards.DemoRewardConfigurationError): self.reward(progress)
            self.assertEqual(self.rows(), before)

    def test_mixed_direct_and_rewards_history_and_playable_unchanged(self):
        progress = self.new()
        direct = self.operation(progress)
        self.grant(progress, 100, direct)
        self.reward(progress)
        self.configure(progress)
        before = tuple(Configuration.objects.using(self.alias).values()), tuple(PlayableState.objects.using(self.alias).values()), tuple(PlayableEvent.objects.using(self.alias).values())
        self.reward(progress)
        self.assertTrue(self.grant(progress, 100, direct).replay)
        progress.refresh_from_db(using=self.alias)
        self.assertEqual(progress.xp_total, 1500)
        services.read_demo_progress(progress.pk, session_token=SECRET)
        self.assertEqual(before, (tuple(Configuration.objects.using(self.alias).values()), tuple(PlayableState.objects.using(self.alias).values()), tuple(PlayableEvent.objects.using(self.alias).values())))
        self.assertEqual(RewardEvent.objects.using(self.alias).count(), 2)

    def test_single_immediate_boundary_and_no_core_without_context(self):
        progress = self.new()
        token = self.fact_token(progress)
        with CaptureQueriesContext(self.db) as queries:
            self.reward(progress, token=token)
        sql = [q["sql"].upper() for q in queries]
        self.assertEqual(sql.count("BEGIN IMMEDIATE"), 1)
        self.assertEqual(sql.count("COMMIT"), 1)
        self.assertFalse(any(q.startswith("SAVEPOINT") for q in sql))
        self.assertLess(sql.index("BEGIN IMMEDIATE"), next(i for i,q in enumerate(sql) if q.startswith("SELECT")))
        with self.assertRaises(services.DemoTransactionError): services._grant_xp_in_transaction(None, amount=1, operation_key="1"*32)
        with transaction.atomic(using=self.alias):
            with self.assertRaises(services.DemoTransactionError): self.reward(progress, token=token)
            with self.assertRaises(services.DemoTransactionError): services._grant_xp_in_transaction(object(), amount=1, operation_key="1"*32)
        with services._xp_transaction(progress, session_token=SECRET) as context:
            with transaction.atomic(using=self.alias):
                with self.assertRaises(services.DemoTransactionError): services._grant_xp_in_transaction(context, amount=1, operation_key="1"*32)
        with self.assertRaises(services.DemoTransactionError): services._grant_xp_in_transaction(context, amount=1, operation_key="1"*32)

    def test_rollback_xp_evolution_reward_and_final_verification(self):
        progress = self.new()
        token = self.fact_token(progress)
        before = self.rows()
        for model in (DemoTargetXPEvent, DemoTargetEvolutionEvent, DemoTargetProgress, RewardEvent):
            with self.subTest(model=model), patch.object(model, "save", side_effect=IntegrityError("synthetic")):
                with self.assertRaises(services.DemoIntegrityError): self.reward(progress, token=token)
            self.assertEqual(self.rows(), before)
        original = rewards._history
        def fail_after_create(current, alias):
            if RewardEvent.objects.using(alias).exists(): raise services.DemoIntegrityError("synthetic final verification")
            return original(current, alias)
        with patch.object(rewards, "_history", fail_after_create):
            with self.assertRaises(services.DemoIntegrityError): self.reward(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_rollback_after_third_evolution(self):
        progress = self.new()
        token = self.fact_token(progress)
        before = self.rows()
        from django.db.models.query import QuerySet
        original = QuerySet.create
        count = 0
        def fail(query, **kwargs):
            nonlocal count
            if query.model is DemoTargetEvolutionEvent:
                count += 1
                if count == 3: raise OperationalError("synthetic evolution")
            return original(query, **kwargs)
        with patch.object(QuerySet, "create", fail):
            with self.assertRaises(services.DemoDatabaseError): self.reward(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_corrupt_snapshot_or_causal_event_rejected(self):
        progress = self.new()
        token = self.fact_token(progress)
        result = self.reward(progress, token=token)
        row = RewardEvent.objects.using(self.alias).get()
        original = row.snapshot
        for changes in ({"xp_amount": 701}, {"evolution_ids": []}, {"eligible": False}, {"progression": {}}, {"schema": "unknown"}):
            RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(snapshot={**original, **changes})
            with self.assertRaises(services.DemoIntegrityError): self.reward(progress, token=token)
        RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(snapshot=original)
        DemoTargetEvolutionEvent.objects.using(self.alias).filter(xp_event_id=result.xp_event_id).first().delete(using=self.alias)
        with self.assertRaises(services.DemoIntegrityError): self.reward(progress, token=token)

    def test_orphan_reward_namespace_xp_never_reconstructed(self):
        progress = self.new()
        result = self.grant(progress)
        token = self.fact_token(progress)
        fact = rewards._fact(token, progress, services._owner(SECRET), "challenge")
        DemoTargetXPEvent.objects.using(self.alias).filter(pk=result.event_id).update(operation_key=rewards._xp_key(fact.identity))
        before = self.rows()
        with self.assertRaises(services.DemoIntegrityError): self.reward(progress, token=token)
        self.assertEqual(self.rows(), before)

    def test_foreign_reward_cause_and_missing_cause_rejected(self):
        progress = self.new()
        first = self.reward(progress)
        other = self.new(OTHER)
        foreign = self.grant(other, secret=OTHER)
        row = RewardEvent.objects.using(self.alias).get(progress=progress)
        RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(xp_event_id=foreign.event_id)
        with self.assertRaises(services.DemoIntegrityError): rewards.read_demo_rewards(progress, session_token=SECRET)
        with self.assertRaises(services.DemoIntegrityError): rewards.read_demo_rewards(other, session_token=OTHER)
        RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(xp_event_id=first.xp_event_id)
        with self.db.constraint_checks_disabled():
            RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(xp_event_id=999999)
        with self.assertRaises(services.DemoIntegrityError): rewards.read_demo_rewards(progress, session_token=SECRET)
        RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(xp_event_id=first.xp_event_id)

    def test_session_signed_fact_and_purpose_isolation(self):
        progress = self.new()
        token = self.fact_token(progress)
        for bad in (token+"x", "forged", self.operation(progress), self.token(progress), self.fact_token(progress, "visit")):
            with self.subTest(token=bad), self.assertRaises(services.DemoAccessError): self.reward(progress, token=bad)
        with self.assertRaises(services.DemoAccessError): self.reward(progress, token=token, secret=OTHER)
        other = self.new(OTHER)
        with self.assertRaises(services.DemoAccessError): self.reward(other, token=token, secret=OTHER)
        with self.assertRaises(services.DemoAccessError): rewards.read_demo_rewards(progress, session_token=OTHER)
        with self.assertRaises(services.DemoInputError): self.reward(progress, activity="real-game")

    def test_model_migration_checks_uniqueness_and_protect(self):
        progress = self.new()
        result = self.reward(progress)
        migration = import_module("apps.ecomotor.ecomotor_target_demo.migrations.0003_synthetic_rewards").Migration
        self.assertEqual(migration.dependencies, [("ecomotor_target_demo", "0002_playable_configurations")])
        self.assertEqual([type(op).__name__ for op in migration.operations], ["CreateModel"])
        row = RewardEvent.objects.using(self.alias).get()
        values = {f.attname:getattr(row,f.attname) for f in row._meta.fields if f.name not in ("id","confirmed_at")}
        with self.assertRaises(IntegrityError): RewardEvent.objects.using(self.alias).create(**values)
        with self.assertRaises(IntegrityError): RewardEvent.objects.using(self.alias).create(**{**values, "fact_id": "a"*32})
        with self.assertRaises(IntegrityError): RewardEvent.objects.using(self.alias).create(**{**values,
            "status": "NO_REWARD", "xp_amount": 0, "xp_event_id": None})
        for changes in ({"status":"NO_REWARD"},{"xp_amount":0},{"fingerprint":"x"},{"fact_id":""},{"origin_code":""}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError): RewardEvent.objects.using(self.alias).filter(pk=row.pk).update(**changes)
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError): DemoTargetXPEvent.objects.using(self.alias).get(pk=result.xp_event_id).delete(using=self.alias)
        self.assertTrue(all(f.remote_field.on_delete.__name__ == "PROTECT" for f in row._meta.fields if f.is_relation))

    def test_catalog_or_rule_failure_never_becomes_no_reward(self):
        progress = self.new()
        token = self.fact_token(progress, "visit")
        before = self.rows()
        with patch.object(rewards, "exact_catalog", side_effect=catalog.DemoCatalogError("synthetic")):
            with self.assertRaises(catalog.DemoCatalogError): self.reward(progress, "visit", token)
        with patch.object(rewards, "evaluate_reward", side_effect=rewards.InvalidRewardRuleSetError("synthetic")):
            with self.assertRaises(rewards.InvalidRewardRuleSetError): self.reward(progress, "visit", token)
        self.assertEqual(self.rows(), before)

    def test_reward_service_does_not_recreate_missing_sqlite(self):
        progress = self.new()
        token = self.fact_token(progress)
        self.db.close()
        self.path.unlink()  # Only this fixture's disposable SQLite.
        with self.assertRaises(ImproperlyConfigured): self.reward(progress, token=token)
        self.assertFalse(self.path.exists())

    def test_reopen_preserves_reward_and_immutable_result(self):
        progress = self.new()
        token = self.fact_token(progress)
        first = self.reward(progress, token=token)
        visit = self.reward(progress, "visit")
        self.configure(progress)
        self.db.close()
        history = rewards.read_demo_rewards(progress, session_token=SECRET)
        self.assertEqual([r.status for r in history], ["APPLIED", "NO_REWARD"])
        self.assertEqual(history[0], first)
        self.assertEqual(history[1], visit)
        self.assertTrue(self.reward(progress, token=token).replay)
        with self.assertRaises(FrozenInstanceError): first.status="NO_REWARD"
        self.assertFalse(hasattr(first,"__dict__"))

    def test_reward_writes_only_demo_tables_no_v1_or_other_teams(self):
        progress = self.new()
        before = self.rows()
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError("V1")):
            self.reward(progress)
            self.reward(progress,"visit")
        after = self.rows()
        self.assertTrue(all(rows == after[name] for name,rows in before.items() if not name.startswith("ecomotor_target_demo_")))

    def reward_http(self, activity="challenge", client=None):
        client = client or self.client
        return {"action":"reward","activity":activity,"fact_token":client.session["reward_tokens"][activity]}

    def test_http_rewards_then_gamer_replay_refresh_and_reopen(self):
        self.http_start()
        challenge = self.reward_http()
        self.assertEqual(self.client.post(URL,challenge).status_code,302)
        self.client.get(URL)
        self.assertEqual(self.client.post(URL,challenge).status_code,302)
        self.client.get(URL)
        visit = self.reward_http("visit")
        self.assertEqual(self.client.post(URL,visit).status_code,302)
        self.assertEqual(self.client.post(URL,visit).status_code,302)
        response=self.client.get(URL)
        self.assertIn("NO_REWARD",response.content.decode())
        self.assertIn("12 OPCIONES DESBLOQUEADAS",response.content.decode())
        self.assertEqual(self.client.post(URL,self.playable_http()).status_code,302)
        self.db.close()
        self.assertEqual(self.client.get(URL).status_code,200)
        self.assertEqual((RewardEvent.objects.using(self.alias).count(),DemoTargetXPEvent.objects.using(self.alias).count(),DemoTargetEvolutionEvent.objects.using(self.alias).count(),Configuration.objects.using(self.alias).count()),(2,1,6,1))
        self.assertEqual(self.client.post(URL,{"action":"start"}).status_code,302)
        self.assertEqual(RewardEvent.objects.using(self.alias).count(),2)
        self.assertEqual(self.client.post(URL,challenge).status_code,403)

    def test_http_reward_manipulation_duplicates_csrf_and_session(self):
        self.http_start()
        data=self.reward_http()
        for key in ("amount","origin_code","recipient_id","user_id","progress","rule_set_version","occurred_at","budget"):
            self.assertEqual(self.client.post(URL,{**data,key:"700"}).status_code,400)
        for key,value in data.items():
            self.assertEqual(self.client.post(URL,urlencode([*data.items(),(key,value)]),content_type="application/x-www-form-urlencoded").status_code,400)
        invalid = self.client.post(URL,{**data,"activity":"<script>x</script>"})
        self.assertEqual(invalid.status_code,400)
        self.assertNotIn("<script>x</script>", invalid.content.decode())
        guarded=Client(enforce_csrf_checks=True)
        guarded.cookies=self.client.cookies.copy()
        self.assertEqual(guarded.post(URL,data).status_code,403)
        guarded.get(URL)
        csrf=guarded.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(guarded.post(URL,{**data,"csrfmiddlewaretoken":csrf}).status_code,302)
        other=Client()
        self.http_start(other)
        self.assertEqual(other.post(URL,data).status_code,403)
        self.assertEqual(other.get(URL,{"fact_id":"foreign"}).status_code,400)


class RewardConcurrencyTests(RewardTests):
    def race_rewards(self, kind):
        progress=self.ready() if kind=="playable" else self.new()
        first=self.fact_token(progress)
        second=first if kind=="same" else self.fact_token(progress)
        if kind=="conflict":
            self.reward(progress, token=first)  # Establish the confirmed original before the race.
            payload=signing.loads(first,salt=rewards.SALT)
            instant=rewards._instant(payload["occurred_at"])+timedelta(seconds=1)
            second=self.incompatible(first,occurred_at=instant.isoformat(timespec="microseconds"))
        xp_token=self.operation(progress)
        playable_token=self.token(progress)
        barrier=Barrier(2)
        def worker(which):
            db=connections[self.alias]
            try:
                barrier.wait(timeout=10)
                if which==1 and kind=="direct": result=self.grant(progress,100,xp_token)
                elif which==1 and kind=="playable": result=self.configure(progress,token=playable_token)
                else:
                    try: result=self.reward(progress,token=first if which==0 else second)
                    except services.DemoConflictError as error: result=error
                return result,id(db.connection)
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=pool.submit(worker,0),pool.submit(worker,1)
            results=a.result(timeout=20),b.result(timeout=20)
        self.assertNotEqual(results[0][1],results[1][1])
        progress.refresh_from_db(using=self.alias)
        expected=1400 if kind in ("different","playable") else 800 if kind=="direct" else 700
        self.assertEqual(progress.xp_total,expected)
        self.assertEqual(RewardEvent.objects.using(self.alias).count(),2 if kind=="different" else 1)
        if kind=="same": self.assertEqual(sum(r[0].replay for r in results),1)
        if kind=="conflict":
            self.assertEqual(sum(isinstance(r[0],services.DemoConflictError) for r in results),1)
            self.assertEqual(sum(getattr(r[0], "replay", False) for r in results),1)
        if kind=="playable": self.assertEqual(Configuration.objects.using(self.alias).count(),1)
        rewards.read_demo_rewards(progress,session_token=SECRET)

    def test_same_fact_real_concurrency(self): self.race_rewards("same")
    def test_different_facts_real_concurrency(self): self.race_rewards("different")
    def test_rewards_and_direct_xp_real_concurrency(self): self.race_rewards("direct")
    def test_rewards_and_playable_real_concurrency(self): self.race_rewards("playable")
    def test_same_identity_incompatible_facts_real_concurrency(self): self.race_rewards("conflict")

    def test_real_reward_timeout_then_explicit_retry(self):
        progress=self.new()
        token=self.fact_token(progress)
        held,release=Event(),Event()
        def blocker():
            db=connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    held.set()
                    if not release.wait(12): raise AssertionError("synchronization timeout")
            finally: db.close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(blocker)
            self.assertTrue(held.wait(5))
            started=monotonic()
            try:
                with self.assertRaises(services.DemoBusyError): self.reward(progress,token=token)
                self.assertGreaterEqual(monotonic()-started,4.5)
            finally: release.set()
            future.result(timeout=5)
        self.assertFalse(self.db.in_atomic_block)
        self.assertEqual(RewardEvent.objects.using(self.alias).count(),0)
        self.assertEqual(DemoTargetXPEvent.objects.using(self.alias).count(),0)
        self.assertEqual(self.reward(progress,token=token).xp_amount,700)


class ConsolidationTests(PersistentTests):
    def test_django_identity_graph_and_original_migrations(self):
        import ast
        from django.db.migrations.loader import MigrationLoader
        config = apps.get_app_config("ecomotor_target_demo")
        self.assertEqual((config.name, config.label), ("apps.ecomotor.ecomotor_target_demo", "ecomotor_target_demo"))
        expected = {"DemoTargetProgress", "DemoTargetXPEvent", "DemoTargetEvolutionEvent",
                    "DemoTargetOptionConfiguration", "DemoTargetPlayableState", "DemoTargetPlayableEvent", "DemoTargetRewardEvent"}
        self.assertEqual({m.__name__ for m in config.get_models()}, expected)
        for model in config.get_models():
            self.assertEqual(model._meta.app_label, "ecomotor_target_demo")
            self.assertEqual(model._meta.db_table, "ecomotor_target_demo_" + model.__name__.lower())
            self.assertEqual(model.__module__, config.name + ".models")
        hashes = {"0001_initial":"09f7eb21fb13aebfcb99dd7951d8c4a434db68e1775b07026edc679863246522",
                  "0002_playable_configurations":"baf12dd0a66bd08416b5703fc4bb05758906a53fe74cc3a802f9f86376d83989",
                  "0003_synthetic_rewards":"0adbd48a735a480d74a00bf8325a9b65e5c1d3acdbe5c9aaf38a830d14f2be8b",
                  "0004_rewards_bank_schema":"6f740210d76395e28ea3135cec1d3a569a26bd7197b92df5720f913f23434a27"}
        loader = MigrationLoader(self.db)
        self.assertEqual({name for app,name in loader.disk_migrations if app==config.label},
                         set(hashes) | {"0005_rewards_duckies_schema", "0006_rewards_combined_schema"})
        self.assertTrue({(config.label,name) for name in hashes} <= set(loader.applied_migrations))
        for name,digest in hashes.items():
            source = Path(import_module(config.name + ".migrations." + name).__file__).read_text(encoding="utf-8")
            # AST hashing ignores CRLF/comments, but preserves every operation,
            # dependency and constraint from the approved pre-move migrations.
            observed = sha256(ast.dump(ast.parse(source),include_attributes=False).encode()).hexdigest()
            self.assertEqual(observed,digest)
        self.assertIn(("ecomotor","0007_target_catalog_freeze"),loader.disk_migrations[(config.label,"0001_initial")].dependencies)

    def test_new_package_resources_backend_commands_and_url(self):
        from django.core.management import get_commands
        from django.template.loader import get_template
        from django.contrib.staticfiles.finders import find
        from django.urls import resolve
        prefix="apps.ecomotor.ecomotor_target_demo"
        self.assertEqual(type(self.db).__module__,prefix+".db_backend.base")
        self.assertEqual(get_commands()["migrate"],prefix)
        self.assertEqual(get_commands()["seed_persistent_target_demo"],prefix)
        self.assertEqual(resolve(URL).func.__module__,prefix+".views")
        root=Path(apps.get_app_config("ecomotor_target_demo").path)
        self.assertEqual(Path(get_template("ecomotor_target_demo/home.html").origin.name),root/"templates"/"ecomotor_target_demo"/"home.html")
        self.assertEqual(Path(find("ecomotor_target_demo/persistent.css")),root/"static"/"ecomotor_target_demo"/"persistent.css")

    def test_repeated_migrate_preserves_rows_contenttypes_and_schema(self):
        progress=self.new()
        self.grant(progress)
        before=self.rows()
        with CaptureQueriesContext(self.db) as queries:
            self.migrate()
        self.assertEqual(self.rows(),before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("CREATE","ALTER","DROP","INSERT","UPDATE","DELETE","REPLACE")) for q in queries))
        self.assertEqual(len([row for row in before["django_content_type"] if row[1]=="ecomotor_target_demo"]),7)


class BankDefaultSubprocessTests(TestCase):
    """Do not inherit persistent_fixture or replace the parent's default."""

    def child(self, scenario, *, module="apps.ecomotor.ecomotor_target_demo.bank_default_fixture",
              prefix="ducky-bank-default-", marker="BANK_DEFAULT_EVIDENCE="):
        from copy import deepcopy
        import json
        import os
        import subprocess
        import sys
        from .isolation import MIGRATING
        from . import test_runner

        root_repo = Path(__file__).resolve().parents[3]
        protected = [root_repo / name for name in (
            "db.sqlite3", "db_preview.sqlite3", "instance/target_demo.sqlite3",
            "instance/target_persistent_demo.sqlite3", "local_settings.py",
            "local_urls.py", "local_demo_seed.py")]

        def hashes():
            return {str(p): sha256(p.read_bytes()).hexdigest() if p.is_file() else None for p in protected}

        parent = connections["default"]
        original_native = parent.connection
        original_config = deepcopy(connections.databases)
        original_state = (parent.autocommit, parent.in_atomic_block, tuple(parent.atomic_blocks),
                          settings.BASE_DIR, settings.TARGET_PERSISTENT_DEMO_ALIAS,
                          settings.TARGET_PERSISTENT_DEMO, MIGRATING.get(), test_runner.running)
        registry = {key: id(value) for key, value in apps.app_configs.items()}
        before = hashes()
        temporary_root = None
        try:
            with TemporaryDirectory(prefix=prefix) as directory:
                temporary_root = Path(directory)
                (temporary_root / "instance").mkdir()
                if scenario == "historical":
                    from shutil import copyfile
                    source = temporary_root / "before"
                    (source / "instance").mkdir(parents=True)
                    self._schema_before(source, root_repo, module)
                    copyfile(source / "instance" / "target_persistent_demo.sqlite3",
                             temporary_root / "instance" / "target_persistent_demo.sqlite3")
                    copyfile(source / "historical.json", temporary_root / "historical.json")
                process = subprocess.Popen(
                    [sys.executable, "-m", module,
                     str(temporary_root), scenario], cwd=root_repo,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
                try:
                    output, errors = process.communicate(timeout=90)
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.communicate(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.communicate(timeout=5)
                self.assertIsNotNone(process.returncode)
                self.assertEqual(process.returncode, 0, output + "\n" + errors)
                reports = [line.removeprefix(marker) for line in output.splitlines()
                           if line.startswith(marker)]
                self.assertEqual(len(reports), 1, output + errors)
                report = json.loads(reports[0])
                self.assertTrue(report["success"])
                self.assertEqual((report["failures"], report["errors"], report["skipped"]), (0, 0, 0))
                self.assertTrue(report["connections_closed"])
                self.assertTrue(report["only_fixture_connections"])
                self.assertEqual(report["alias"], "default")
                self.assertEqual(Path(report["file"]), temporary_root / "instance" / "target_persistent_demo.sqlite3")
                self.assertNotEqual(report["pid"], os.getpid())
                print(marker.replace("EVIDENCE", "CHILD") + json.dumps(report, sort_keys=True))
                return report
        finally:
            if temporary_root is not None:
                self.assertFalse(temporary_root.exists(), "Child file handles prevented fixture cleanup")
            self.assertIs(connections["default"], parent)
            self.assertIs(parent.connection, original_native)
            self.assertEqual(connections.databases, original_config)
            self.assertEqual((parent.autocommit, parent.in_atomic_block, tuple(parent.atomic_blocks),
                              settings.BASE_DIR, settings.TARGET_PERSISTENT_DEMO_ALIAS,
                              settings.TARGET_PERSISTENT_DEMO, MIGRATING.get(), test_runner.running), original_state)
            self.assertEqual({key: id(value) for key, value in apps.app_configs.items()}, registry)
            self.assertEqual(hashes(), before)

    def _schema_before(self, root, repo, module):
        import os
        import subprocess
        import sys
        process = subprocess.Popen([sys.executable, "-m", module, str(root), "before"],
            cwd=repo, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            output, errors = process.communicate(timeout=90)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, output + errors)

    def test_shared_default_commit_and_rollback(self):
        report = self.child("atomicity")
        self.assertEqual(report["tests"], 3)
        self.assertEqual(len(report["observations"]), 3)

    def test_real_bank_idempotency_and_conflicts(self):
        self.assertEqual(self.child("idempotency")["tests"], 1)

    def test_file_backed_concurrency_and_timeout(self):
        report = self.child("concurrency")
        self.assertEqual(report["tests"], 2)
        self.assertEqual(len(report["observations"]), 3)

    def test_child_failure_propagates_and_cleans_up(self):
        with self.assertRaisesRegex(AssertionError, "injected child failure after protected connection opened"):
            self.child("failure")


class Schema0004Tests(TestCase):
    """Separate processes preserve the parent's registry and protected default."""

    child = BankDefaultSubprocessTests.child
    _schema_before = BankDefaultSubprocessTests._schema_before

    def test_new_sqlite_schema_and_constraints(self):
        self.child("fresh", module="apps.ecomotor.ecomotor_target_demo.schema_0004_fixture")

    def test_physical_pre_0004_copy_and_original_replays(self):
        self.child("historical", module="apps.ecomotor.ecomotor_target_demo.schema_0004_fixture")


class RewardsBankSubprocessTests(TestCase):
    child = BankDefaultSubprocessTests.child

    def test_real_rewards_bank_functional_and_replay(self):
        self.assertEqual(self.child("functional", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 6)

    def test_real_rewards_bank_single_transaction_and_rollback(self):
        self.assertEqual(self.child("atomicity", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 4)

    def test_real_rewards_bank_historical_integrity(self):
        self.assertEqual(self.child("integrity", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 4)

    def test_real_rewards_bank_concurrency_and_timeout(self):
        self.assertEqual(self.child("concurrency", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 6)

    def test_http_bank_credit_readonly_history_and_replay(self):
        self.assertEqual(self.child("http-functional", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 3)

    def test_http_bank_csrf_sessions_tokens_and_fields(self):
        self.assertEqual(self.child("http-security", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 3)

    def test_http_bank_controlled_errors_and_real_timeout(self):
        self.assertEqual(self.child("http-errors", module="apps.ecomotor.ecomotor_target_demo.reward_bank_fixture")["tests"], 3)


class Schema0005Tests(TestCase):
    _schema_before = BankDefaultSubprocessTests._schema_before

    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.schema_0005_fixture",
            prefix="ducky-schema-0005-", marker="SCHEMA_0005_EVIDENCE=")

    def test_fresh_schema_four_outcomes_and_physical_constraints(self):
        report = self.child("fresh")
        self.assertEqual(report["tests"], 4)
        self.assertTrue(report["migration_scope_closed"])
        self.assertEqual(report["observations"][2],
                         {"update_combinations": 64, "accepted": 4, "rejected_by_named_check": 60})

    def test_physical_0004_copy_raw_history_and_v1_v2_replays(self):
        report = self.child("historical")
        self.assertEqual(report["tests"], 1)
        self.assertTrue(report["migration_scope_closed"])
        self.assertEqual(report["observations"][0]["historical_calls_replayed"], 9)
        self.assertTrue(report["observations"][0]["raw_v1_v2_json_unchanged"])
        self.assertTrue(report["observations"][0]["replay_readonly"])


class Schema0006Tests(TestCase):
    _schema_before = BankDefaultSubprocessTests._schema_before

    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.schema_0006_fixture",
            prefix="ducky-schema-0006-", marker="SCHEMA_0006_EVIDENCE=")

    def test_fresh_schema_five_outcomes_and_exhaustive_sql(self):
        report = self.child("fresh")
        self.assertEqual(report["tests"], 4)
        self.assertTrue(report["migration_scope_closed"])
        self.assertEqual(report["observations"][2], {
            "update_combinations": 64, "insert_combinations": 64,
            "accepted": 5, "rejected_by_named_check": 59})

    def test_physical_0005_copy_original_v1_v2_v3_and_replays(self):
        report = self.child("historical")
        self.assertEqual(report["tests"], 1)
        self.assertTrue(report["migration_scope_closed"])
        self.assertEqual(report["observations"][0]["historical_calls_replayed"], 10)
        self.assertTrue(report["observations"][0]["raw_v1_v2_v3_json_unchanged"])
        self.assertTrue(report["observations"][0]["replay_readonly"])


class RewardsDuckiesSubprocessTests(TestCase):
    """Only parent tests; child cases are reported separately, never rediscovered."""

    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.reward_duckies_fixture",
            prefix="ducky-rewards-duckies-", marker="DUCKIES_DEFAULT_EVIDENCE=")

    def test_real_rewards_boundary_savepoint_commit_and_rollback(self):
        report = self.child("atomicity")
        self.assertEqual(report["tests"], 4)
        self.assertEqual(len(report["observations"]), 4)
        first = report["observations"][0]
        for name in ("shared_native_connection", "single_begin_immediate", "duckies_savepoint",
                     "single_commit", "uncommitted_delivery_invisible"):
            self.assertIs(first[name], True)

    def test_duckies_idempotency_is_not_future_rewards_replay(self):
        report = self.child("idempotency")
        self.assertEqual(report["tests"], 1)
        self.assertIs(report["observations"][0]["not_rewards_coordinator_replay"], True)

    def test_independent_connections_conflicts_timeout_and_recovery(self):
        report = self.child("concurrency")
        self.assertEqual(report["tests"], 4)
        self.assertEqual(len(report["observations"]), 4)
        for observation in report["observations"][:3]:
            self.assertIs(observation["independent_native_connections"], True)
        self.assertGreaterEqual(report["observations"][3]["real_timeout_seconds"], 4.5)

    def test_child_failure_propagates_and_releases_temporary_file(self):
        with self.assertRaisesRegex(AssertionError,
                "injected Duckies child failure after protected connection opened"):
            self.child("failure")


class RewardsDuckiesServiceSubprocessTests(TestCase):
    """Five parent scenarios; the 19 real child cases have separate counts."""

    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.reward_duckies_fixture",
            prefix="ducky-rewards-duckies-", marker="DUCKIES_DEFAULT_EVIDENCE=")

    def test_item_coordinator_consumption_and_historical_replay(self):
        report = self.child("service-functional")
        self.assertEqual(report["tests"], 5)
        self.assertTrue(report["checks_and_no_model_changes"])
        self.assertTrue(report["observations"][1]["real_equip_and_consume"])
        self.assertTrue(report["observations"][1]["replay_without_inventory_query_or_dml"])

    def test_closed_mapping_strict_facts_and_overflow(self):
        self.assertEqual(self.child("service-validation")["tests"], 4)

    def test_causal_integrity_and_orphan_rejection(self):
        self.assertEqual(self.child("service-integrity")["tests"], 3)

    def test_single_outer_commit_and_full_rollback(self):
        report = self.child("service-atomicity")
        self.assertEqual(report["tests"], 2)
        for key in ("shared_native_connection", "single_begin_immediate", "single_commit", "inner_savepoint"):
            self.assertTrue(report["observations"][0][key])
        self.assertEqual(report["observations"][1]["rollback_stages"], 5)

    def test_real_concurrency_timeout_and_explicit_recovery(self):
        report = self.child("service-concurrency")
        self.assertEqual(report["tests"], 5)
        self.assertGreaterEqual(report["observations"][-1]["real_timeout_seconds"], 4.5)


class RewardsDuckiesHTTPSubprocessTests(TestCase):
    """Seven distinct 2D parents, fourteen child cases counted separately."""

    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.reward_duckies_fixture",
            prefix="ducky-rewards-duckies-", marker="DUCKIES_DEFAULT_EVIDENCE=")

    def test_http_grant_and_get_without_business_effects(self):
        report = self.child("http-functional")
        self.assertEqual(report["tests"], 2)
        self.assertTrue(report["observations"][0]["real_item_grant"])

    def test_original_last_and_row_replay(self):
        self.assertEqual(self.child("http-replay")["tests"], 1)

    def test_real_consumption_and_readonly_inventory_states(self):
        report = self.child("http-consumption")
        self.assertEqual(report["tests"], 2)
        self.assertTrue(report["observations"][0]["http_replay_without_delivery"])
        self.assertTrue(report["observations"][1]["no_dml"])

    def test_owned_sessions_and_new_game(self):
        self.assertEqual(self.child("http-sessions")["tests"], 1)

    def test_csrf_parameters_tokens_escape_and_conflict(self):
        self.assertEqual(self.child("http-security")["tests"], 3)

    def test_controlled_errors_real_timeout_and_retry(self):
        report = self.child("http-errors")
        self.assertEqual(report["tests"], 4)
        self.assertGreaterEqual(report["observations"][-1]["seconds"], 4.5)

    def test_xp_bank_visit_playable_and_reopen(self):
        self.assertEqual(self.child("http-compatibility")["tests"], 1)


class RewardsComboSubprocessTests(TestCase):
    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.reward_combo_fixture",
            prefix="ducky-rewards-combo-", marker="COMBO_DEFAULT_EVIDENCE=")

    def test_functional_v4_and_historical_replay(self):
        self.assertEqual(self.child("functional")["tests"], 3)

    def test_closed_v4_token_and_complete_proposal(self):
        self.assertEqual(self.child("validation")["tests"], 3)

    def test_strict_snapshot_real_causes_and_orphans(self):
        self.assertEqual(self.child("integrity")["tests"], 3)

    def test_shared_transaction_and_complete_rollback(self):
        self.assertEqual(self.child("atomicity")["tests"], 2)

    def test_independent_concurrency_and_real_timeout(self):
        self.assertEqual(self.child("concurrency")["tests"], 5)


class RewardsComboHTTPSubprocessTests(TestCase):
    def child(self, scenario):
        return BankDefaultSubprocessTests.child(self, scenario,
            module="apps.ecomotor.ecomotor_target_demo.reward_combo_http_fixture",
            prefix="ducky-rewards-combo-http-", marker="COMBO_HTTP_EVIDENCE=")

    def test_real_http_v4_form_prg_and_three_causes(self):
        self.assertEqual(self.child("functional")["tests"], 1)

    def test_replay_forms_spend_consume_xp_and_reopen(self):
        self.assertEqual(self.child("replay")["tests"], 2)

    def test_csrf_sessions_strict_fields_and_tokens(self):
        self.assertEqual(self.child("security")["tests"], 3)

    def test_controlled_errors_rollback_and_real_timeout(self):
        self.assertEqual(self.child("errors")["tests"], 4)

    def test_historical_modalities_and_playable_options(self):
        self.assertEqual(self.child("compatibility")["tests"], 1)


def load_tests(loader, suite, pattern):
    # Explicit, predictable discovery under exclusive settings only. Keep the
    # shared fixture without rerunning inherited functional methods twice.
    import unittest
    selected = unittest.TestSuite(loader.loadTestsFromTestCase(PersistentTests))
    for case in (PersistentConcurrencyTests, PlayableTests, PlayableConcurrencyTests, RewardTests, RewardConcurrencyTests, ConsolidationTests, BankDefaultSubprocessTests, Schema0004Tests, RewardsBankSubprocessTests, RewardsDuckiesSubprocessTests, RewardsDuckiesServiceSubprocessTests, RewardsDuckiesHTTPSubprocessTests, Schema0005Tests, Schema0006Tests, RewardsComboSubprocessTests, RewardsComboHTTPSubprocessTests, LegacyStatsArchivePhaseATests, PlayableArchivePhaseBTests):
        for name in case.__dict__:
            if name.startswith("test_"):
                selected.addTest(case(name))
    return selected

# DIAG-ATR-OBJ-02-SNAP-01 Phase A: pure historical CUACK verifier.
# These tests intentionally do not open any database or route the reader to HTTP.
from copy import deepcopy as _legacy_deepcopy
from dataclasses import FrozenInstanceError as _LegacyFrozenError
from . import legacy_stats_archive as legacy_archive


class LegacyStatsArchivePhaseATests(TestCase):
    """Exact historical JSON samples from the standalone synthetic schema."""

    def make_archive(self):
        codes = legacy_archive.LEGACY_STAT_CODES
        gamer, roman = OPTION_CODES[-1], OPTION_CODES[2]
        def allocation(code, amount):
            return [[c, amount if c == code else 0] for c in codes]
        def config(id, option, amount, code, revision=1):
            return {"id": id, "revision": revision, "option_code": option,
                    "catalog_id": legacy_archive.CATALOG_ID,
                    "catalog_version": legacy_archive.VERSION,
                    "definition_version": legacy_archive.LEGACY_DEFINITION_VERSION,
                    "bases": allocation("ATK", 0), "increments": allocation(code, amount),
                    "budget": legacy_archive.LEGACY_BUDGET}
        def state(revision, active, configs):
            return {"progress_id": 101, "catalog_id": 23, "revision": revision,
                    "active_option": active,
                    "configurations": sorted(_legacy_deepcopy(configs), key=lambda c: c["option_code"])}
        empty = state(0, None, [])
        first = config(15, gamer, 15, "ATK")
        second = config(19, roman, 10, "DEF")
        after1 = state(1, gamer, [first])
        after2 = state(2, roman, [first, second])
        after3 = state(3, gamer, [first, second])
        updated = config(15, gamer, 9, "ATK", revision=2)
        after4 = state(4, gamer, [updated, second])
        def event(n, action, option, inc, before, after, expected, config_rev=None):
            return {"event_id": n, "progress_id": 101, "operation_key": f"{n:032x}",
                    "action": action, "option_code": option,
                    "original_request": {"action": action, "option_code": option,
                        "increments": _legacy_deepcopy(inc), "expected_revision": expected,
                        "configuration_revision": config_rev},
                    "before": _legacy_deepcopy(before), "after": _legacy_deepcopy(after)}
        events = [
            event(1, "configure", gamer, first["increments"], empty, after1, None),
            event(2, "configure", roman, second["increments"], after1, after2, 1),
            event(3, "switch", gamer, None, after2, after3, 2),
            event(4, "redistribute", gamer, updated["increments"], after3, after4, 3, 1),
        ]
        return {"progress_id": 101, "catalog_pk": 23,
                "catalog_id": legacy_archive.CATALOG_ID,
                "catalog_version": legacy_archive.VERSION,
                "events": events, "current_state": _legacy_deepcopy(after4)}

    def check(self, data=None):
        return legacy_archive.validate_legacy_playable_archive(**(data or self.make_archive()))

    def reject(self, changed):
        with self.assertRaises(legacy_archive.InvalidLegacyArchiveError):
            self.check(changed)

    def test_four_step_history_and_calculations(self):
        archive = self.check()
        self.assertEqual([e.action for e in archive.events],
                         ["configure", "configure", "switch", "redistribute"])
        self.assertEqual((archive.state.revision, len(archive.state.configurations)), (4, 2))
        gamer = next(c for c in archive.state.configurations if c.option_code == OPTION_CODES[-1])
        self.assertEqual((gamer.revision, gamer.stats.points_used, gamer.stats.points_remaining), (2, 9, 36))
        self.assertEqual(gamer.stats.effective[-1], ("CUACK", 0))
        self.assertEqual(gamer.stats.effective[0], ("ATK", 9))
        self.assertEqual(archive.definition_version, "persist-stats-demo-2026-10-22-v1")

    def test_conserves_json_inputs_and_freezes_results_deeply(self):
        data = self.make_archive()
        original = _legacy_deepcopy(data)
        result = self.check(data)
        self.assertEqual(data, original)
        data["current_state"]["configurations"][0]["increments"][0][1] = 333
        self.assertEqual(next(c for c in result.state.configurations
                              if c.option_code == OPTION_CODES[-1]).stats.points_used, 9)
        with self.assertRaises(_LegacyFrozenError):
            result.state.revision = 99
        with self.assertRaises(_LegacyFrozenError):
            result.events[0].after = None
        with self.assertRaises(TypeError):
            result.events[0].after.configurations[0].stats.increments[0] = ("ATK", 5)
        self.assertFalse(hasattr(result.state, "__dict__"))

    def test_rejects_unknown_catalog_and_versions(self):
        for field, value in (("catalog_pk", True), ("catalog_id", "unexpected"),
                             ("catalog_version", "unknown"), ("progress_id", -1)):
            with self.subTest(field=field):
                data = self.make_archive()
                data[field] = value
                self.reject(data)
        for value in ("persist-stats-demo-esp-v2", "unknown", 7, None):
            with self.subTest(definition_version=value):
                data = self.make_archive()
                data["events"][1]["after"]["configurations"][0]["definition_version"] = value
                self.reject(data)

    def test_rejects_esp_replacement_and_mixed_codes(self):
        for section in ("bases", "increments"):
            for code in ("ESP", "SPE", "CUAK", "cuack", "LOG"):
                with self.subTest(section=section, code=code):
                    data = self.make_archive()
                    data["events"][0]["after"]["configurations"][0][section][-1][0] = code
                    self.reject(data)
        data = self.make_archive()
        data["events"][3]["original_request"]["increments"][-1][0] = "ESP"
        self.reject(data)

    def test_rejects_invalid_pair_types_missing_pairs_and_duplicates(self):
        for bad in ([], [["ATK", 1]] * 6, [["ATK", 1]], "ATK", None,
                    [["ATK", 0], ["DEF", 0], ["VEL", 0], ["INT", 0], ["LOG", 0], ["CUACK", True]],
                    [["ATK", 0], ["DEF", 0], ["VEL", 0], ["INT", 0], ["LOG", 0], ["CUACK", -1]],
                    [["ATK", 0], ["DEF", 0], ["VEL", 0], ["INT", 0], ["LOG", 0], ["CUACK", 1.0]]):
            with self.subTest(bad=bad):
                data = self.make_archive()
                data["current_state"]["configurations"][0]["increments"] = bad
                self.reject(data)

    def test_rejects_budget_and_bases_inconsistency(self):
        for field, bad in (("budget", 46), ("budget", 0), ("budget", True),
                           ("budget", -1), ("budget", 1.0)):
            with self.subTest(field=field, bad=bad):
                data = self.make_archive()
                data["current_state"]["configurations"][0][field] = bad
                self.reject(data)
        data = self.make_archive()
        data["current_state"]["configurations"][0]["bases"][0][1] = 1
        self.reject(data)
        data = self.make_archive()
        data["current_state"]["configurations"][0]["increments"][0][1] = 46
        self.reject(data)

    def test_rejects_snapshot_structure_and_revisions(self):
        for change in (lambda d: d["events"][0]["after"].pop("active_option"),
                       lambda d: d["events"][0]["after"].update(unexpected=1),
                       lambda d: d["events"][1]["after"].update(revision=7),
                       lambda d: d["events"][1]["before"].update(revision=0),
                       lambda d: d["current_state"].update(active_option="unknown"),
                       lambda d: d["current_state"].update(progress_id=True),
                       lambda d: d["current_state"].update(catalog_id=999),
                       lambda d: d["current_state"]["configurations"].append(
                           _legacy_deepcopy(d["current_state"]["configurations"][0]))):
            data = self.make_archive()
            change(data)
            self.reject(data)

    def test_rejects_event_keys_duplicates_and_order(self):
        for change in (lambda d: d["events"][1].update(event_id=1),
                       lambda d: d["events"][1].update(operation_key=d["events"][0]["operation_key"]),
                       lambda d: d["events"][1].update(progress_id=200),
                       lambda d: d["events"][1].update(operation_key="BAD"),
                       lambda d: d["events"][1].update(action="switch"),
                       lambda d: d["events"][1]["original_request"].pop("action"),
                       lambda d: d["events"][1]["original_request"].update(action="redistribute"),
                       lambda d: d["events"][1]["original_request"].update(expected_revision=True)):
            data = self.make_archive()
            change(data)
            self.reject(data)
        data = self.make_archive()
        data["events"] = list(reversed(data["events"]))
        self.reject(data)

    def test_rejects_bad_transitions_and_altered_other_options(self):
        mutations = (
            lambda d: d["events"][0]["after"].update(active_option=None),
            lambda d: d["events"][2]["after"].update(active_option=OPTION_CODES[2]),
            lambda d: d["events"][2]["after"]["configurations"][0].update(revision=2),
            lambda d: d["events"][3]["original_request"].update(configuration_revision=2),
            lambda d: d["events"][3]["after"]["configurations"][1]["increments"][0].__setitem__(1, 3),
            lambda d: d["events"][3]["original_request"].update(expected_revision=2),
            lambda d: d["events"][3]["original_request"].update(increments=None),
        )
        for mutate in mutations:
            data = self.make_archive()
            mutate(data)
            self.reject(data)

    def test_empty_or_unsorted_histories_rejected(self):
        for events in ([], (), None, "events"):
            data = self.make_archive()
            data["events"] = events
            self.reject(data)
        data = self.make_archive()
        data["events"] = data["events"][1:]
        self.reject(data)

    def test_rejects_unmatched_final_state_and_bad_catalog(self):
        data = self.make_archive()
        data["current_state"]["revision"] = 3
        self.reject(data)
        data = self.make_archive()
        data["current_state"]["configurations"][0]["catalog_id"] = "alien"
        self.reject(data)
        data = self.make_archive()
        data["events"][0]["after"]["configurations"][0]["definition_version"] = "persist-stats-demo-esp-v2"
        self.reject(data)

    def test_module_has_no_a4_django_or_io_dependencies(self):
        import inspect
        source = inspect.getsource(legacy_archive)
        for item in ("target_stats_validation", "target_stats_preparation",
                     "target_stats_config_validation", "django.", "sqlite3", ".objects", "open("):
            self.assertNotIn(item, source)
        self.assertEqual(self.check().definition_version, legacy_archive.LEGACY_DEFINITION_VERSION)


class PlayableArchivePhaseBTests(TestCase):
    """Stored V1 JSON is explicit evidence, never a call to current A4."""

    # Reuse fixture helpers without inheriting historical test methods.
    setUp = PersistentTests.setUp
    close = PersistentTests.close
    migrate = PersistentTests.migrate
    seed = PersistentTests.seed
    new = PersistentTests.new
    operation = PersistentTests.operation
    grant = PersistentTests.grant
    rows = PersistentTests.rows
    http_start = PersistentTests.http_start
    http_data = PersistentTests.http_data
    ready = PlayableTests.ready
    token = PlayableTests.token
    configure = PlayableTests.configure
    http_ready = PlayableTests.http_ready
    playable_http = PlayableTests.playable_http

    def legacy(self, progress=None):
        progress = progress or self.ready()
        data = LegacyStatsArchivePhaseATests().make_archive()
        configs = {}
        for row in data["current_state"]["configurations"]:
            configs[row["id"]] = Configuration.objects.using(self.alias).create(
                progress=progress, catalog_id=progress.catalog_id,
                option_code=row["option_code"], definition_version=row["definition_version"],
                bases=row["bases"], increments=row["increments"], budget=row["budget"], revision=row["revision"])
        def snapshot(raw):
            raw = _legacy_deepcopy(raw)
            raw["progress_id"], raw["catalog_id"] = progress.pk, progress.catalog_id
            for row in raw["configurations"]:
                row["id"] = configs[row["id"]].pk
            return raw
        for event in data["events"]:
            PlayableEvent.objects.using(self.alias).create(progress=progress,
                operation_key=event["operation_key"], action=event["action"],
                option_code=event["option_code"], original_request=event["original_request"],
                before=snapshot(event["before"]), after=snapshot(event["after"]))
        active = next(c for c in configs.values() if c.option_code == GAMER)
        PlayableState.objects.using(self.alias).create(progress=progress,
            active_configuration=active, revision=4)
        return progress

    def historical_token(self, progress, action="configure", secret=SECRET, key=None):
        return signing.dumps({"progress": progress.pk, "owner": services._owner(secret),
            "purpose": action, "key": key or "1".zfill(32)}, salt=playable.SALT)

    def business(self):
        return {key: value for key, value in self.rows().items() if key != "django_session"}

    def legacy_browser(self):
        progress = self.legacy()
        session = self.client.session
        session["demo_secret"], session["demo_progress"] = SECRET, progress.pk
        session["playable_last"] = {"action": "configure", "operation": self.historical_token(progress),
            "option_code": GAMER, "expected_revision": "",
            **{c: "15" if c == "ATK" else "0" for c in legacy_archive.LEGACY_STAT_CODES}}
        session.save()
        return progress, dict(session["playable_last"])

    def assert_no_dml(self, queries):
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))

    def test_legacy_complete_read_reopen_without_a4_or_writes(self):
        progress = self.legacy()
        before = self.business()
        for _ in range(2):
            self.db.close()
            with patch.object(playable, "prepare_target_stats_configuration", side_effect=AssertionError("no A4")), CaptureQueriesContext(self.db) as queries:
                state, history = playable.read_demo_playable(progress, session_token=SECRET)
            self.assertTrue(playable.is_legacy(state))
            self.assertEqual((state.revision, len(history), len(state.configurations)), (4, 4, 2))
            self.assertEqual(state.configurations[-1].stats.effective[-1][0], "CUACK")
            self.assert_no_dml(queries)
            self.assertEqual(self.business(), before)

    def test_legacy_blocks_tokens_all_actions_replay_noop_and_stale(self):
        progress = self.legacy()
        before = self.business()
        with CaptureQueriesContext(self.db) as queries:
            for action in playable.ACTIONS:
                with self.assertRaises(playable.DemoLegacyReadOnlyError):
                    playable.issue_playable_operation(progress, action=action, session_token=SECRET)
                for revision in (None, 1, 4):
                    with self.subTest(action=action, revision=revision), self.assertRaises(playable.DemoLegacyReadOnlyError):
                        playable._operate(progress, action=action, option_code=GAMER,
                            increments=[[c, 0] for c in legacy_archive.LEGACY_STAT_CODES] if action != "switch" else None,
                            operation_token=self.historical_token(progress, action), session_token=SECRET,
                            expected_revision=revision, configuration_revision=2 if action == "redistribute" else None)
        self.assert_no_dml(queries)
        self.assertEqual(self.business(), before)

    def test_legacy_access_and_token_priority(self):
        progress = self.legacy()
        for secret, token in ((OTHER, self.historical_token(progress)),
                (SECRET, self.historical_token(progress, secret=OTHER)),
                (SECRET, self.historical_token(progress, action="switch")), (SECRET, "altered")):
            with self.assertRaises(services.DemoAccessError):
                playable.configure_demo_option(progress, option_code=GAMER, increments=(),
                    expected_revision=4, operation_token=token, session_token=secret)

    def test_legacy_corruption_never_falls_back_or_repairs(self):
        progress = self.legacy()
        event = PlayableEvent.objects.using(self.alias).filter(progress=progress).order_by("pk").last()
        original = _legacy_deepcopy(event.after)
        mutations = [lambda d: d.update(revision=99),
            lambda d: d.update(progress_id=True), lambda d: d.update(catalog_id=999),
            lambda d: d["configurations"][0].update(definition_version="unknown"),
            lambda d: d["configurations"][0].update(definition_version="persist-stats-demo-esp-v2"),
            lambda d: d["configurations"][0].update(budget=46),
            lambda d: d["configurations"][0].update(id=True),
            lambda d: d["configurations"][0]["increments"].reverse(),
            lambda d: d["configurations"][0]["bases"][0].__setitem__(1, 1),
            lambda d: d["configurations"][0]["increments"][-1].__setitem__(0, "ESP")]
        for mutate in mutations:
            value = _legacy_deepcopy(original); mutate(value)
            PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=value)
            before = self.business()
            with patch.object(playable, "_decode", side_effect=AssertionError("no fallback")):
                with self.assertRaises(services.DemoIntegrityError):
                    playable.read_demo_playable(progress, session_token=SECRET)
            self.assertEqual(self.business(), before)
        PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=original)
        config = Configuration.objects.using(self.alias).filter(progress=progress).first()
        for version in ("unknown", "persist-stats-demo-esp-v2"):
            Configuration.objects.using(self.alias).filter(pk=config.pk).update(definition_version=version)
            with self.assertRaises(services.DemoIntegrityError):
                playable.read_demo_playable(progress, session_token=SECRET)

    def test_empty_allows_esp_but_partial_state_does_not(self):
        progress = self.ready()
        state, events = playable.read_demo_playable(progress, session_token=SECRET)
        self.assertEqual((state.revision, state.configurations, events), (0, (), ()))
        self.configure(progress)
        config = Configuration.objects.using(self.alias).get(progress=progress)
        self.assertEqual(config.definition_version, "persist-stats-demo-esp-v2")
        self.assertEqual(config.bases[-1], ["ESP", 0])
        PlayableEvent.objects.using(self.alias).filter(progress=progress).delete()
        with self.assertRaises(services.DemoIntegrityError):
            self.configure(progress, ROMAN, revision=1)

    def test_current_exact_version_required_and_no_legacy_fallback(self):
        progress = self.ready(); self.configure(progress)
        event = PlayableEvent.objects.using(self.alias).get(progress=progress)
        value = _legacy_deepcopy(event.after)
        value["configurations"][0]["definition_version"] = "arbitrary-not-empty"
        PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=value)
        Configuration.objects.using(self.alias).filter(progress=progress).update(definition_version="arbitrary-not-empty")
        with patch.object(playable, "validate_legacy_playable_archive", side_effect=AssertionError("no fallback")):
            with self.assertRaises(services.DemoIntegrityError): playable.read_demo_playable(progress, session_token=SECRET)

    def test_legacy_http_get_preserves_history_session_and_has_no_forms(self):
        progress, saved = self.legacy_browser()
        before = self.business()
        for _ in range(2):
            self.db.close()
            response = self.client.get(URL)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn("Archivo histórico CUACK", html)
            self.assertIn("CUACK", html)
            for text in ('name="CUACK"', 'name="ESP"', 'value="configure"', 'value="switch"', 'value="redistribute"', 'replay_%s'):
                self.assertNotIn(text, html)
            self.assertIn('id="rewards"', html)
            self.assertIn('id="banco"', html)
            self.assertIn('id="inventario"', html)
            self.assertEqual(self.client.session["playable_last"], saved)
            self.assertEqual(self.business(), before)

    def test_legacy_http_rejections_csrf_and_no_business_writes(self):
        progress, data = self.legacy_browser()
        self.client.get(URL)
        before = self.business()
        self.assertEqual(self.client.post(URL, data).status_code, 409)
        self.assertEqual(self.business(), before)
        for changes, expected in (({"extra": "1"}, 400), ({"CUACK": "bad"}, 400),
                ({"operation": "altered"}, 403), ({"operation": self.historical_token(progress, secret=OTHER)}, 403)):
            self.assertEqual(self.client.post(URL, {**data, **changes}).status_code, expected)
            self.assertEqual(self.business(), before)
        missing = dict(data);missing.pop("DEF")
        self.assertEqual(self.client.post(URL, missing).status_code, 400)
        self.assertEqual(self.client.post(URL, urlencode([*data.items(), ("action", "configure")]),
            content_type="application/x-www-form-urlencoded").status_code, 400)
        protected = Client(enforce_csrf_checks=True);protected.cookies = self.client.cookies.copy()
        self.assertEqual(protected.post(URL, data).status_code, 403)
        protected.get(URL)
        csrf = protected.cookies[settings.CSRF_COOKIE_NAME].value
        self.assertEqual(protected.post(URL, {**data, "csrfmiddlewaretoken": csrf}).status_code, 409)
        self.assertEqual(self.business(), before)

    def test_legacy_http_xp_and_no_reward_remain_operational(self):
        progress, saved = self.legacy_browser();self.client.get(URL)
        tables = lambda: {k:v for k,v in self.rows().items() if k in
            (Configuration._meta.db_table, PlayableState._meta.db_table, PlayableEvent._meta.db_table)}
        before = tables()
        self.assertEqual(self.client.post(URL, self.http_data(amount="1")).status_code, 302)
        self.client.get(URL)
        token = self.client.session["reward_tokens"]["visit"]
        self.assertEqual(self.client.post(URL, {"action":"reward", "activity":"visit", "fact_token":token}).status_code, 302)
        self.assertEqual(self.client.get(URL).status_code, 200)
        self.assertEqual(tables(), before)
        self.assertEqual(self.client.session["playable_last"], saved)

    def test_current_http_esp_and_legacy_post_field_rejected(self):
        self.http_ready(); response=self.client.get(URL)
        self.assertIn('name="ESP"',response.content.decode());self.assertNotIn('name="CUACK"',response.content.decode())
        data=self.playable_http();self.assertEqual(self.client.post(URL,{**data,"CUACK":"0"}).status_code,400)
        self.assertEqual(self.client.post(URL,data).status_code,302)
        self.assertEqual(self.client.post(URL,data).status_code,302)
        self.assertEqual(PlayableEvent.objects.using(self.alias).count(),1)


    def test_legacy_http_switch_redistribute_replay_noop_and_restart(self):
        progress, saved = self.legacy_browser();self.client.get(URL)
        before=self.business()
        for revision in ("2", "4"):
            data={"action":"switch","operation":self.historical_token(progress,"switch",key=f"{3:032x}"),
                  "option_code":GAMER,"expected_revision":revision}
            self.assertEqual(self.client.post(URL,data).status_code,409)
            data={**saved,"action":"redistribute","operation":self.historical_token(progress,"redistribute",key=f"{4:032x}"),
                  "expected_revision":"4","configuration_revision":"2","ATK":"9"}
            self.assertEqual(self.client.post(URL,data).status_code,409)
        self.assertEqual(self.business(),before)
        self.assertEqual(self.client.session["playable_last"],saved)
        self.assertEqual(self.client.post(URL,{"action":"start"}).status_code,302)
        self.assertNotIn("playable_last",self.client.session)
        self.assertEqual(self.client.post(URL,saved).status_code,403)
        self.assertEqual(PlayableEvent.objects.using(self.alias).filter(progress=progress).count(),4)

    def test_legacy_scope_immediate_and_foreign_session_http(self):
        progress,saved=self.legacy_browser()
        with CaptureQueriesContext(self.db) as queries:
            playable.read_demo_playable(progress,session_token=SECRET)
        sql=[q["sql"].upper() for q in queries]
        self.assertIn("BEGIN IMMEDIATE",sql)
        self.assertLess(sql.index("BEGIN IMMEDIATE"),next(i for i,q in enumerate(sql) if q.startswith("SELECT")))
        foreign=Client();session=foreign.session
        session["demo_progress"]=progress.pk;session["demo_secret"]=OTHER;session.save()
        for response in (foreign.get(URL),foreign.post(URL,saved)):
            self.assertEqual(response.status_code,403)
            self.assertNotIn("Archivo histórico CUACK",response.content.decode())

    def test_missing_state_and_truncated_legacy_events_are_invalid(self):
        progress=self.legacy()
        events=PlayableEvent.objects.using(self.alias).filter(progress=progress).order_by("pk")
        events.first().delete(using=self.alias)
        with self.assertRaises(services.DemoIntegrityError):
            playable.read_demo_playable(progress,session_token=SECRET)
        PlayableState.objects.using(self.alias).filter(progress=progress).delete()
        with self.assertRaises(services.DemoIntegrityError):
            playable.issue_playable_operation(progress,action="configure",session_token=SECRET)

    def test_current_bad_bases_and_budget_rejected_without_fallback(self):
        progress=self.ready();self.configure(progress)
        event=PlayableEvent.objects.using(self.alias).get(progress=progress)
        original=_legacy_deepcopy(event.after)
        for bases,budget in ((None,45),({},45),([["ATK",0]],45),([["ATK",True]],45),(original["configurations"][0]["bases"],46)):
            value=_legacy_deepcopy(original);value["configurations"][0].update(bases=bases,budget=budget)
            PlayableEvent.objects.using(self.alias).filter(pk=event.pk).update(after=value)
            with self.assertRaises(services.DemoIntegrityError):
                playable.read_demo_playable(progress,session_token=SECRET)
