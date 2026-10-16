"""SQLite real file-backed: workers independientes; nunca usa db.sqlite3."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, get_ident
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.users.models import UserProfileEcomotor

from . import initialization_config
from .initialization import InitializationDatabaseError, ensure_ecomotor_initialized
from .models import CharacterStats
from .test_initialization import TEST_CONFIGURATION, create_catalogs


class InitializationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-s2a-concurrency-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "s2a_file_test"
        # TransactionTestCase debe autorizar explícitamente el alias temporal.
        # Se registra tras el setup del runner: nunca será la BD habitual.
        previous_databases = type(self).databases
        type(self).databases = previous_databases | {self.alias}
        self.addCleanup(setattr, type(self), "databases", previous_databases)
        config = connections["default"].settings_dict.copy()
        config["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        # Se conservan IMMEDIATE y timeout reales: no se relajan para el test.
        config["OPTIONS"] = config["OPTIONS"].copy()
        self.assertEqual(config["OPTIONS"], {"transaction_mode": "IMMEDIATE", "timeout": 5})
        connections.databases[self.alias] = config
        self.connection = connections[self.alias]
        self.addCleanup(self.close_database)
        executor = MigrationExecutor(self.connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        self.user = get_user_model().objects.using(self.alias).create(username="s2a-concurrent-test")
        create_catalogs(self.alias)
        patcher = patch.object(initialization_config, "INITIAL_CONFIGURATION", TEST_CONFIGURATION)
        patcher.start()
        self.addCleanup(patcher.stop)

    def close_database(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def test_overlapping_calls_serialize_and_return_one_persisted_pair(self):
        first_locked = Event()
        second_begin = Event()

        def worker(first):
            connection = connections[self.alias]
            statements = []

            def observe(execute, sql, params, many, context):
                statements.append(sql)
                if first and sql.upper().startswith("SELECT") and not first_locked.is_set():
                    # Ya se ha ejecutado BEGIN IMMEDIATE en esta conexión.
                    first_locked.set()
                    if not second_begin.wait(3):
                        raise AssertionError("La segunda conexión no intentó BEGIN.")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"):
                    second_begin.set()
                return execute(sql, params, many, context)

            try:
                if not first and not first_locked.wait(3):
                    raise AssertionError("La primera conexión no adquirió la transacción.")
                with connection.execute_wrapper(observe):
                    result = ensure_ecomotor_initialized(self.user)
                return result, get_ident(), id(connection.connection), statements
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(worker, True)
            second = pool.submit(worker, False)
            results = [first.result(timeout=12), second.result(timeout=12)]
        self.assertNotEqual(results[0][1], results[1][1])
        self.assertNotEqual(results[0][2], results[1][2])
        self.assertEqual([entry[0].created for entry in results], [True, False])
        self.assertEqual(results[0][0].profile_id, results[1][0].profile_id)
        self.assertEqual(results[0][0].character_stats_id, results[1][0].character_stats_id)
        for _, _, _, statements in results:
            begin = next(i for i, sql in enumerate(statements) if sql.upper().startswith("BEGIN IMMEDIATE"))
            read = next(i for i, sql in enumerate(statements) if sql.upper().startswith("SELECT"))
            self.assertLess(begin, read)
        self.assertEqual(UserProfileEcomotor.objects.using(self.alias).count(), 1)
        self.assertEqual(CharacterStats.objects.using(self.alias).count(), 1)

    def test_lock_timeout_is_controlled_and_retry_uses_new_transaction(self):
        def worker():
            try:
                return ensure_ecomotor_initialized(self.user)
            finally:
                connections[self.alias].close()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic(using=self.alias):
                pending = pool.submit(worker)
                with self.assertRaises(InitializationDatabaseError) as caught:
                    pending.result(timeout=12)
                self.assertIsInstance(caught.exception.__cause__, OperationalError)
                self.assertIn("locked", str(caught.exception.__cause__).lower())
                self.assertEqual(UserProfileEcomotor.objects.using(self.alias).count(), 0)
                self.assertEqual(CharacterStats.objects.using(self.alias).count(), 0)
            result = pool.submit(worker).result(timeout=12)
        self.assertTrue(result.created)
        self.assertEqual(UserProfileEcomotor.objects.using(self.alias).count(), 1)
        self.assertEqual(CharacterStats.objects.using(self.alias).count(), 1)
