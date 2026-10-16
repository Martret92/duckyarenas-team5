"""Transacciones S3 realmente solapadas, en SQLite temporal file-backed."""

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
from .models import CharacterStats, EvolutionEvent, XPEvent
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import IdempotencyConflictError, XPDatabaseError, grant_historical_xp


class XPConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-s3-concurrency-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "s3_file_test"
        previous = type(self).databases
        type(self).databases = previous | {self.alias}
        self.addCleanup(setattr, type(self), "databases", previous)
        config = connections["default"].settings_dict.copy()
        config["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        config["OPTIONS"] = config["OPTIONS"].copy()
        self.assertEqual(config["OPTIONS"], {"transaction_mode": "IMMEDIATE", "timeout": 5})
        connections.databases[self.alias] = config
        self.connection = connections[self.alias]
        self.addCleanup(self.close_database)
        executor = MigrationExecutor(self.connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        create_xp_catalogs(self.alias)
        self.profile = create_xp_profile(self.alias)
        patcher = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        patcher.start()
        self.addCleanup(patcher.stop)

    def close_database(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def overlap(self, first_amount, first_key, second_amount, second_key):
        first_locked = Event()
        second_begin = Event()

        def worker(first, amount, key):
            connection = connections[self.alias]
            statements = []

            def observe(execute, sql, params, many, context):
                statements.append(sql)
                if first and sql.upper().startswith("SELECT") and not first_locked.is_set():
                    first_locked.set()
                    if not second_begin.wait(3):
                        raise AssertionError("La segunda llamada no intentó BEGIN IMMEDIATE.")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"):
                    second_begin.set()
                return execute(sql, params, many, context)

            try:
                if not first and not first_locked.wait(3):
                    raise AssertionError("La primera llamada no adquirió la transacción.")
                with connection.execute_wrapper(observe):
                    try:
                        result = grant_historical_xp(self.profile, amount, key)
                    except IdempotencyConflictError as error:
                        result = error
                return result, get_ident(), id(connection.connection), statements
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(worker, True, first_amount, first_key)
            second = pool.submit(worker, False, second_amount, second_key)
            rows = [first.result(timeout=12), second.result(timeout=12)]
        self.assertNotEqual(rows[0][1], rows[1][1])
        self.assertNotEqual(rows[0][2], rows[1][2])
        for _, _, _, statements in rows:
            begin = next(i for i, sql in enumerate(statements) if sql.upper().startswith("BEGIN IMMEDIATE"))
            read = next(i for i, sql in enumerate(statements) if sql.upper().startswith("SELECT"))
            self.assertLess(begin, read)
        return rows[0][0], rows[1][0]

    def assert_persisted(self, xp, level, stage, points, events, evolutions):
        profile = UserProfileEcomotor.objects.using(self.alias).get(pk=self.profile.pk)
        stats = CharacterStats.objects.using(self.alias).get(profile_id=profile.pk)
        self.assertEqual((profile.historical_xp_total, profile.current_level,
                          profile.current_stage_code, stats.available_points),
                         (xp, level, f"s3-test-stage-{stage}", points))
        self.assertEqual(XPEvent.objects.using(self.alias).count(), events)
        self.assertEqual(EvolutionEvent.objects.using(self.alias).count(), evolutions)
        self.assertEqual(UserProfileEcomotor.objects.using(self.alias).count(), 1)
        self.assertEqual(CharacterStats.objects.using(self.alias).count(), 1)
        for evolution in EvolutionEvent.objects.using(self.alias).select_related("xp_event"):
            self.assertEqual(evolution.profile_id, evolution.xp_event.profile_id)

    def test_simultaneous_same_key_same_amount_grants_once_and_replays(self):
        first, second = self.overlap(17, "test-same", 17, "test-same")
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.xp_event_id, second.xp_event_id)
        self.assertEqual(first.evolution_event_ids, second.evolution_event_ids)
        self.assertIsNone(second.stat_points_awarded)
        self.assert_persisted(17, 2, 2, 9, 1, 1)

    def test_simultaneous_same_key_different_amount_reports_conflict(self):
        first, second = self.overlap(17, "test-conflict", 34, "test-conflict")
        self.assertFalse(first.replayed)
        self.assertIsInstance(second, IdempotencyConflictError)
        self.assert_persisted(17, 2, 2, 9, 1, 1)

    def test_distinct_keys_preserve_both_grants_and_all_crossed_thresholds(self):
        first, second = self.overlap(17, "test-first", 34, "test-second")
        self.assertFalse(first.replayed)
        self.assertFalse(second.replayed)
        self.assertEqual((first.xp_before, first.xp_after, second.xp_before, second.xp_after),
                         (0, 17, 17, 51))
        self.assertEqual(first.crossed_levels + second.crossed_levels, (2, 3, 4))
        self.assertEqual(first.crossed_stage_codes + second.crossed_stage_codes,
                         XP_CONFIGURATION.ordered_stage_codes[1:4])
        self.assertEqual(first.stat_points_awarded + second.stat_points_awarded, 7)
        self.assert_persisted(51, 4, 4, 14, 2, 3)
        rows = list(EvolutionEvent.objects.using(self.alias).order_by("pk"))
        self.assertEqual([row.xp_event_id for row in rows],
                         [first.xp_event_id, second.xp_event_id, second.xp_event_id])

    def test_real_lock_timeout_rolls_back_and_same_key_retry_is_clean(self):
        def worker():
            try:
                return grant_historical_xp(self.profile, 17, "test-lock-retry")
            finally:
                connections[self.alias].close()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic(using=self.alias):
                future = pool.submit(worker)
                with self.assertRaises(XPDatabaseError) as caught:
                    future.result(timeout=12)
                self.assertIsInstance(caught.exception.__cause__, OperationalError)
                self.assertIn("locked", str(caught.exception.__cause__).lower())
                self.assert_persisted(0, 1, 1, 7, 0, 0)
            first = pool.submit(worker).result(timeout=12)
            replay = pool.submit(worker).result(timeout=12)
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(first.xp_event_id, replay.xp_event_id)
        self.assert_persisted(17, 2, 2, 9, 1, 1)
