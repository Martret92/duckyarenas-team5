"""Escritores realmente solapados en SQLite temporal, sin tocar db.sqlite3."""

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
from .models import CharacterStats, LevelThreshold, StatAllocationEvent, XPEvent
from .stat_allocation import (
    AllocationConflictError, AllocationDatabaseError, InsufficientPointsError, allocate_stat_points,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class StatAllocationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="s7-concurrency-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "s7_file_test"
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
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s7-concurrent-actual")

    def close_database(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def overlap(self, first_call, second_call):
        acquired = Event()
        second_begin = Event()
        def worker(first, call):
            db = connections[self.alias]
            sqls = []
            def observe(execute, sql, params, many, context):
                sqls.append(sql)
                if first and sql.upper().startswith("SELECT") and not acquired.is_set():
                    acquired.set()
                    if not second_begin.wait(3):
                        raise AssertionError("El segundo escritor no intentó BEGIN IMMEDIATE")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"):
                    second_begin.set()
                return execute(sql, params, many, context)
            try:
                if not first and not acquired.wait(3):
                    raise AssertionError("La primera transacción no adquirió el lock")
                with db.execute_wrapper(observe):
                    try:
                        result = call()
                    except (AllocationConflictError, InsufficientPointsError) as error:
                        result = error
                return result, get_ident(), id(db.connection), sqls
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            one = pool.submit(worker, True, first_call)
            two = pool.submit(worker, False, second_call)
            rows = [one.result(timeout=12), two.result(timeout=12)]
        self.assertNotEqual(rows[0][1], rows[1][1])
        self.assertNotEqual(rows[0][2], rows[1][2])
        for _, _, _, sqls in rows:
            begin = next(i for i, sql in enumerate(sqls) if sql.upper().startswith("BEGIN IMMEDIATE"))
            read = next(i for i, sql in enumerate(sqls) if sql.upper().startswith("SELECT"))
            self.assertLess(begin, read)
        return rows[0][0], rows[1][0]

    def allocation(self, points, key, attribute="atk"):
        return lambda: allocate_stat_points(self.profile, attribute, points, key)

    def assert_final(self, balance, atk, allocations, xp=102, xp_events=1):
        profile = UserProfileEcomotor.objects.using(self.alias).get(pk=self.profile.pk)
        stats = CharacterStats.objects.using(self.alias).get(profile_id=profile.pk)
        self.assertEqual((profile.historical_xp_total, stats.available_points, stats.atk), (xp, balance, atk))
        self.assertEqual(StatAllocationEvent.objects.using(self.alias).count(), allocations)
        self.assertEqual(XPEvent.objects.using(self.alias).count(), xp_events)
        for event in StatAllocationEvent.objects.using(self.alias).all():
            self.assertEqual(event.profile_id, profile.pk)
            self.assertEqual(event.attribute_after, event.attribute_before + event.points_spent)
            self.assertEqual(event.available_points_after, event.available_points_before - event.points_spent)
            self.assertGreaterEqual(event.available_points_after, 0)

    def test_distinct_keys_preserve_both_spends(self):
        first, second = self.overlap(self.allocation(3, "first"), self.allocation(4, "second"))
        self.assertEqual((first.attribute_before, first.attribute_after, second.attribute_before, second.attribute_after),
                         (2, 5, 5, 9))
        self.assert_final(7, 9, 2)

    def test_same_key_same_parameters_one_event_and_replay(self):
        first, second = self.overlap(self.allocation(3, "same"), self.allocation(3, "same"))
        self.assertFalse(first.replayed)
        self.assertTrue(second.replayed)
        self.assertEqual(first.allocation_event_id, second.allocation_event_id)
        self.assert_final(11, 5, 1)

    def test_same_key_different_parameters_conflict(self):
        first, second = self.overlap(self.allocation(3, "same"), self.allocation(4, "same"))
        self.assertFalse(first.replayed)
        self.assertIsInstance(second, AllocationConflictError)
        self.assert_final(11, 5, 1)

    def test_combined_spend_cannot_exceed_balance(self):
        first, second = self.overlap(self.allocation(10, "first"), self.allocation(10, "second"))
        self.assertFalse(first.replayed)
        self.assertIsInstance(second, InsufficientPointsError)
        self.assert_final(4, 12, 1)

    def add_future_level(self):
        # Ficticio: S3 puede otorgar puntos incluso tras alcanzar Actual.
        LevelThreshold.objects.using(self.alias).create(level=5, minimum_xp=119, stat_points_awarded=8)

    def test_s3_then_s7_preserves_awarded_and_spent_points(self):
        self.add_future_level()
        first, second = self.overlap(
            lambda: grant_historical_xp(self.profile, 17, "s7-with-s3"), self.allocation(18, "spend"))
        self.assertEqual(first.stat_points_awarded, 8)
        self.assertFalse(second.replayed)
        self.assert_final(4, 20, 1, xp=119, xp_events=2)

    def test_s7_then_s3_preserves_both_updates(self):
        self.add_future_level()
        first, second = self.overlap(self.allocation(3, "spend"),
                                     lambda: grant_historical_xp(self.profile, 17, "s7-with-s3"))
        self.assertFalse(first.replayed)
        self.assertEqual(second.stat_points_awarded, 8)
        self.assert_final(19, 5, 1, xp=119, xp_events=2)

    def test_failed_spend_before_s3_remains_explicit_and_partial_free(self):
        self.add_future_level()
        first, second = self.overlap(self.allocation(18, "insufficient"),
                                     lambda: grant_historical_xp(self.profile, 17, "s7-later-s3"))
        self.assertIsInstance(first, InsufficientPointsError)
        self.assertEqual(second.stat_points_awarded, 8)
        self.assert_final(22, 2, 0, xp=119, xp_events=2)

    def test_real_timeout_and_same_key_retry_new_transaction(self):
        def worker():
            try:
                return allocate_stat_points(self.profile, "atk", 3, "s7-timeout")
            finally:
                connections[self.alias].close()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic(using=self.alias):
                future = pool.submit(worker)
                with self.assertRaises(AllocationDatabaseError) as caught:
                    future.result(timeout=12)
                self.assertIsInstance(caught.exception.__cause__, OperationalError)
                self.assertIn("locked", str(caught.exception.__cause__).lower())
                self.assert_final(14, 2, 0)
            first = pool.submit(worker).result(timeout=12)
            replay = pool.submit(worker).result(timeout=12)
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(first.allocation_event_id, replay.allocation_event_id)
        self.assert_final(11, 5, 1)
