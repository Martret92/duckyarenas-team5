"""S11-A: conexiones independientes y transacciones realmente solapadas en SQLite."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, get_ident
from unittest.mock import patch

from django.db import OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.users.models import UserProfileEcomotor

from . import initialization_config
from .models import CharacterStats, EvolutionEvent, Specialization, UserSpecializationProgress, XPEvent
from .specialization_service import (
    SpecializationConflictError, SpecializationDatabaseError, select_initial_specialization,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class SpecializationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="s11-concurrency-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "s11_file_test"
        previous = type(self).databases
        type(self).databases = previous | {self.alias}
        self.addCleanup(setattr, type(self), "databases", previous)
        settings = connections["default"].settings_dict.copy()
        settings["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        settings["OPTIONS"] = settings["OPTIONS"].copy()
        self.assertEqual(settings["OPTIONS"], {"transaction_mode": "IMMEDIATE", "timeout": 5})
        connections.databases[self.alias] = settings
        self.connection = connections[self.alias]
        self.addCleanup(self.close_database)
        executor = MigrationExecutor(self.connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        create_xp_catalogs(self.alias)
        self.profile = create_xp_profile(self.alias)
        self.alpha = Specialization.objects.using(self.alias).create(code="s11-concurrent-alpha", name="Ficticia A")
        self.beta = Specialization.objects.using(self.alias).create(code="s11-concurrent-beta", name="Ficticia B")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s11-concurrent-actual")
        self.before = self.unchanged_state()

    def close_database(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def unchanged_state(self):
        profile = UserProfileEcomotor.objects.using(self.alias).values().get(pk=self.profile.pk)
        profile.pop("active_specialization_code")
        return profile, [list(model.objects.using(self.alias).order_by("pk").values()) for model in (
            CharacterStats, XPEvent, EvolutionEvent,
        )]

    def assert_final(self, selected=None):
        current = UserProfileEcomotor.objects.using(self.alias).get(pk=self.profile.pk)
        rows = list(UserSpecializationProgress.objects.using(self.alias).all())
        self.assertEqual(self.unchanged_state(), self.before)
        if selected is None:
            self.assertIsNone(current.active_specialization_code)
            self.assertEqual(rows, [])
        else:
            self.assertEqual(current.active_specialization_code, selected.code)
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0].profile_id, rows[0].specialization_id, rows[0].domain_xp_total),
                             (current.pk, selected.pk, 0))

    def overlap(self, second_code):
        acquired = Event()
        second_attempt = Event()
        def worker(first, code):
            db = connections[self.alias]
            sqls = []
            begun = False
            def observe(execute, sql, params, many, context):
                nonlocal begun
                sqls.append(sql)
                if sql.upper().startswith("BEGIN IMMEDIATE"):
                    if not first:
                        second_attempt.set()
                    result = execute(sql, params, many, context)
                    begun = True  # El BEGIN real ya adquirió la transacción de escritura.
                    return result
                if sql.upper().startswith("SELECT"):
                    self.assertTrue(begun)
                    if first and not acquired.is_set():
                        acquired.set()
                        if not second_attempt.wait(3):
                            raise AssertionError("El segundo escritor no intentó BEGIN IMMEDIATE.")
                return execute(sql, params, many, context)
            try:
                if not first and not acquired.wait(3):
                    raise AssertionError("La primera transacción no adquirió el lock.")
                with db.execute_wrapper(observe):
                    try:
                        result = select_initial_specialization(self.profile, code)
                    except SpecializationConflictError as error:
                        result = error
                return result, get_ident(), id(db.connection), sqls
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            one = pool.submit(worker, True, self.alpha.code)
            two = pool.submit(worker, False, second_code)
            rows = [one.result(timeout=12), two.result(timeout=12)]
        self.assertNotEqual(rows[0][1], rows[1][1])
        self.assertNotEqual(rows[0][2], rows[1][2])
        for _, _, _, sqls in rows:
            begin = next(i for i, sql in enumerate(sqls) if sql.upper().startswith("BEGIN IMMEDIATE"))
            read = next(i for i, sql in enumerate(sqls) if sql.upper().startswith("SELECT"))
            self.assertLess(begin, read)
        return rows[0][0], rows[1][0]

    def test_same_code_one_selection_and_idempotent_second_writer(self):
        first, second = self.overlap(self.alpha.code)
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.progress_id, second.progress_id)
        self.assert_final(self.alpha)

    def test_different_codes_do_not_overwrite_each_other(self):
        first, second = self.overlap(self.beta.code)
        self.assertTrue(first.created)
        self.assertIsInstance(second, SpecializationConflictError)
        self.assert_final(self.alpha)

    def test_uncommitted_selection_invisible_and_atomic_rollback(self):
        wrote_profile = Event()
        release = Event()
        def writer():
            db = connections[self.alias]
            def fail_after_write(execute, sql, params, many, context):
                result = execute(sql, params, many, context)
                if sql.upper().startswith("UPDATE"):
                    wrote_profile.set()
                    if not release.wait(3):
                        raise AssertionError("El lector no verificó el estado confirmado.")
                    raise OperationalError("s11-test-rollback-after-update")
                return result
            try:
                with db.execute_wrapper(fail_after_write):
                    return select_initial_specialization(self.profile, self.alpha.code)
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(writer)
            try:
                self.assertTrue(wrote_profile.wait(3))
                self.assert_final()
            finally:
                release.set()
            with self.assertRaises(SpecializationDatabaseError) as caught:
                future.result(timeout=12)
        self.assertIsInstance(caught.exception.__cause__, OperationalError)
        self.assert_final()

    def test_real_timeout_clean_retry_and_repeat_in_new_transaction(self):
        def worker():
            try:
                return select_initial_specialization(self.profile, self.alpha.code)
            finally:
                connections[self.alias].close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic(using=self.alias):
                future = pool.submit(worker)
                with self.assertRaises(SpecializationDatabaseError) as caught:
                    future.result(timeout=12)
                self.assertIsInstance(caught.exception.__cause__, OperationalError)
                self.assertIn("locked", str(caught.exception.__cause__).lower())
                self.assert_final()
            first = pool.submit(worker).result(timeout=12)
            repeated = pool.submit(worker).result(timeout=12)
        self.assertTrue(first.created)
        self.assertFalse(repeated.created)
        self.assertEqual(first.progress_id, repeated.progress_id)
        self.assert_final(self.alpha)
