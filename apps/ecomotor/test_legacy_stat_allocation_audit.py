"""INT-A2-T04: synthetic V1 evidence and isolated SQLite transactions only."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import traceback
from unittest.mock import patch

from django.db import DatabaseError, OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileEcomotor

from . import initialization_config, legacy_stat_allocation_audit as audit
from .legacy_stat_allocation_audit import (
    InvalidStatAllocationAuditAliasError, InvalidStatAllocationAuditProfileIdError,
    StatAllocationAuditProfileNotFoundError, StatAllocationAuditReadError,
    StatAllocationAuditStatus, StatAllocationAuditTransactionError,
    audit_legacy_stat_allocations,
)
from .models import CharacterStats, EvolutionEvent, StatAllocationEvent, XPEvent
from .stat_allocation import AllocationConflictError, allocate_stat_points
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class LegacyStatAllocationAuditTests(TransactionTestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="t04-synthetic-owner")
        self.connection = connections["default"]
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def diagnose(self):
        return audit_legacy_stat_allocations(self.profile.pk, using="default")

    def spend(self, key="t04-spend", points=2):
        if self.profile.historical_xp_total == 0:
            grant_historical_xp(self.profile, 102, "t04-to-actual")
            self.profile.refresh_from_db()
        return allocate_stat_points(self.profile, "atk", points, key)

    def state(self):
        return tuple(tuple(model.objects.order_by("pk").values()) for model in (
            UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent, StatAllocationEvent,
        ))

    def test_empty_history_is_observed_not_certified_complete(self):
        result = self.diagnose()
        self.assertEqual(result.profile_id, self.profile.pk)
        self.assertEqual(result.status, StatAllocationAuditStatus.OBSERVED_CONSISTENT)
        self.assertEqual((result.observed_event_count, result.s7_valid_event_ids, result.issues), (0, (), ()))
        self.assertIn("FULL_POINTS_HISTORY_NOT_PROVEN", result.evidence_limits)
        self.assertIn("POINT_GRANTS_AND_UNRECORDED_SPENDS_NOT_AUDITED", result.evidence_limits)

    def test_valid_events_are_all_checked_without_s3_or_stats_interpretation(self):
        first = self.spend("t04-first", 2)
        second = self.spend(" t04-second ", 3)
        # Current state and catalogs are irrelevant to the historical S7 rows.
        CharacterStats.objects.filter(profile=self.profile).update(available_points=0)
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="unknown")
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            result = self.diagnose()
        self.assertEqual(result.status, StatAllocationAuditStatus.OBSERVED_CONSISTENT)
        self.assertEqual(result.observed_event_count, 2)
        self.assertEqual(result.s7_valid_event_ids, (first.allocation_event_id, second.allocation_event_id))
        self.assertEqual(result.issues, ())
        self.assertNotIn("t04-second", repr(result))
        with self.assertRaises(FrozenInstanceError):
            result.observed_event_count = 0
        with self.assertRaises(FrozenInstanceError):
            result.issues = ()
        self.assertEqual(asdict(result)["profile_id"], self.profile.pk)

    def test_s7_arithmetic_ranges_identity_and_codes_reused_without_mutation(self):
        self.spend()
        original = StatAllocationEvent.objects.get(profile=self.profile)
        changes = (
            {"increase_applied": original.points_spent + 1},
            {"available_points_before": original.available_points_before + 1},
            {"attribute_after": original.attribute_after + 1},
            {"points_spent": 0},
            {"points_spent": 1.5},
            {"attribute": "not-allowed"},
            {"operation_key": ""},
            {"stage_code_at_allocation": "x" * 33},
            {"profile_id": self.profile.pk + 1},
            {"pk": -1},
        )
        for fields in changes:
            event = StatAllocationEvent.objects.get(pk=original.pk)
            for name, value in fields.items():
                setattr(event, name, value)
            with self.subTest(fields=fields), patch.object(audit, "_load_events", return_value=[event]):
                result = self.diagnose()
            self.assertEqual(result.status, StatAllocationAuditStatus.INCONSISTENT)
            self.assertEqual({issue.code for issue in result.issues}, {"INVALID_S7_EVENT"})
            self.assertEqual(result.s7_valid_event_ids, ())
        self.assertEqual(StatAllocationEvent.objects.get(pk=original.pk).points_spent, original.points_spent)

    def test_real_sqlite_fractional_snapshot_is_inconsistent_not_coerced(self):
        self.spend()
        with self.connection.cursor() as cursor:
            # Keep the SQL equation true; S7 still rejects fractional snapshots.
            cursor.execute("UPDATE ecomotor_statallocationevent "
                           "SET attribute_before = 2.5, attribute_after = 4.5 WHERE profile_id = %s",
                           [self.profile.pk])
        result = self.diagnose()
        self.assertEqual(result.status, StatAllocationAuditStatus.INCONSISTENT)
        self.assertEqual(result.issues[0].code, "INVALID_S7_EVENT")

    def test_duplicate_ids_and_keys_report_each_observed_row(self):
        self.spend()
        event = StatAllocationEvent.objects.get(profile=self.profile)
        # Both duplications are impossible through normal S7 writes/SQL UNIQUE;
        # feed a corrupted materialization to exercise the defensive audit.
        with patch.object(audit, "_load_events", return_value=[event, event]):
            result = self.diagnose()
        self.assertEqual(result.observed_event_count, 2)
        self.assertEqual({issue.code for issue in result.issues}, {
            "DUPLICATE_EVENT_ID", "DUPLICATE_OPERATION_KEY",
        })
        self.assertEqual(result.status, StatAllocationAuditStatus.INCONSISTENT)

    def test_distinct_event_ids_with_duplicate_key_are_flagged(self):
        self.spend()
        event = StatAllocationEvent.objects.get(profile=self.profile)
        another = StatAllocationEvent.objects.get(profile=self.profile)
        another.pk = event.pk + 1000
        with patch.object(audit, "_load_events", return_value=[event, another]):
            result = self.diagnose()
        self.assertEqual({issue.code for issue in result.issues}, {"DUPLICATE_OPERATION_KEY"})
        self.assertEqual({issue.event_id for issue in result.issues}, {event.pk, another.pk})

    def test_profile_isolation_and_no_foreign_payload_leak(self):
        self.spend()
        other = create_xp_profile(username="t04-synthetic-other")
        grant_historical_xp(other, 102, "t04-other-actual")
        allocate_stat_points(other, "atk", 2, "t04-secret-other")
        own = self.diagnose()
        foreign = audit_legacy_stat_allocations(other.pk, using="default")
        self.assertEqual((own.observed_event_count, foreign.observed_event_count), (1, 1))
        self.assertNotEqual(own.s7_valid_event_ids, foreign.s7_valid_event_ids)
        self.assertNotIn("secret", repr(own))
        # Even an unexpected foreign row must fail S7's owner validation.
        row = StatAllocationEvent.objects.get(profile=other)
        with patch.object(audit, "_load_events", return_value=[row]):
            self.assertEqual(self.diagnose().issues[0].code, "INVALID_S7_EVENT")

    def test_invalid_identifiers_and_missing_profile_fail_before_read(self):
        for value in (0, -1, True, False, 1.0, "1", None, 2**63, self.profile):
            with self.subTest(value=repr(value)), CaptureQueriesContext(self.connection) as queries:
                with self.assertRaises(InvalidStatAllocationAuditProfileIdError):
                    audit_legacy_stat_allocations(value, using="default")
            self.assertEqual(len(queries), 0)
        for alias in (None, True, 1, "", "unknown-t04", [], {}):
            with self.subTest(alias=repr(alias)), self.assertRaises(InvalidStatAllocationAuditAliasError):
                audit_legacy_stat_allocations(self.profile.pk, using=alias)
        with self.assertRaises(StatAllocationAuditProfileNotFoundError):
            audit_legacy_stat_allocations(2**63 - 1, using="default")

    def test_outer_transaction_and_incompatible_connection_rejected(self):
        with transaction.atomic(), CaptureQueriesContext(self.connection) as queries:
            with self.assertRaises(StatAllocationAuditTransactionError):
                self.diagnose()
        self.assertEqual(len(queries), 0)
        for options in ({}, {"transaction_mode": "DEFERRED", "timeout": 5},
                        {"transaction_mode": "IMMEDIATE", "timeout": 1}):
            with self.subTest(options=options), patch.dict(self.connection.settings_dict, OPTIONS=options):
                with self.assertRaises(StatAllocationAuditTransactionError):
                    self.diagnose()

    def test_read_failures_never_return_partial_result_or_secret_error(self):
        self.spend("t04-private-key")
        for fail_at in (1, 2):
            seen = 0
            secret = "t04-private-key in injected database error"

            def fail(execute, sql, params, many, context):
                nonlocal seen
                if sql.lstrip().upper().startswith("SELECT"):
                    seen += 1
                    if seen == fail_at:
                        raise OperationalError(secret)
                return execute(sql, params, many, context)

            with self.subTest(fail_at=fail_at), self.connection.execute_wrapper(fail):
                with self.assertRaises(StatAllocationAuditReadError) as caught:
                    self.diagnose()
            self.assertEqual(seen, fail_at)
            self.assertNotIn(secret, "".join(traceback.format_exception(caught.exception)))
            self.assertIsNone(caught.exception.__cause__)
            self.assertFalse(self.connection.in_atomic_block)
        with patch.object(self.connection, "commit", side_effect=DatabaseError("secret")):
            with self.assertRaises(StatAllocationAuditReadError):
                self.diagnose()
        with patch.object(self.connection, "ensure_connection", side_effect=DatabaseError("secret")):
            with self.assertRaises(StatAllocationAuditReadError) as caught:
                self.diagnose()
        self.assertIsNone(caught.exception.__cause__)

    def test_all_reads_in_immediate_transaction_no_writes_or_extractor(self):
        self.spend()
        statements = []

        def observe(execute, sql, params, many, context):
            statements.append(sql)
            if sql.lstrip().upper().startswith("SELECT"):
                self.assertTrue(context["connection"].in_atomic_block)
                self.assertEqual(context["connection"].alias, "default")
            return execute(sql, params, many, context)

        before = self.state()
        with patch("apps.ecomotor.legacy_inventory_reader.extract_legacy_audit_snapshot",
                   side_effect=AssertionError("A3.2 extractor must not run")), \
                patch("apps.ecomotor.stat_allocation.allocate_stat_points",
                      side_effect=AssertionError("S7 writer must not run")), \
                self.connection.execute_wrapper(observe):
            self.diagnose()
        self.assertEqual(statements[0], "BEGIN IMMEDIATE")
        self.assertEqual(len([sql for sql in statements if sql.startswith("SELECT")]), 2)
        self.assertTrue(all(sql.startswith(("BEGIN IMMEDIATE", "SELECT")) for sql in statements))
        self.assertEqual(self.state(), before)

    def test_s3_and_s7_regression_no_dependency_on_audit(self):
        with patch.object(audit, "audit_legacy_stat_allocations", side_effect=AssertionError):
            first = self.spend("t04-v1", 2)
            replay = allocate_stat_points(self.profile, "atk", 2, "t04-v1")
            self.assertTrue(replay.replayed)
            self.assertEqual(first.allocation_event_id, replay.allocation_event_id)
            with self.assertRaises(AllocationConflictError):
                allocate_stat_points(self.profile, "atk", 3, "t04-v1")
            xp_replay = grant_historical_xp(self.profile, 102, "t04-to-actual")
            self.assertTrue(xp_replay.replayed)
        self.assertEqual(self.diagnose().status, StatAllocationAuditStatus.OBSERVED_CONSISTENT)


class LegacyStatAllocationAuditConcurrencyTests(TransactionTestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="t04-sqlite-")
        self.addCleanup(directory.cleanup)
        self.alias = "t04_file_test"
        previous = type(self).databases
        type(self).databases = previous | {self.alias}
        self.addCleanup(setattr, type(self), "databases", previous)
        settings = connections["default"].settings_dict.copy()
        settings["NAME"] = str(Path(directory.name) / "isolated.sqlite3")
        settings["OPTIONS"] = settings["OPTIONS"].copy()
        connections.databases[self.alias] = settings
        self.addCleanup(self.close_database)
        executor = MigrationExecutor(connections[self.alias])
        executor.migrate(executor.loader.graph.leaf_nodes())
        create_xp_catalogs(self.alias)
        self.profile = create_xp_profile(self.alias, username="t04-file-owner")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "t04-file-actual")
        self.first = allocate_stat_points(self.profile, "atk", 2, "t04-file-first")

    def close_database(self):
        connections[self.alias].close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def test_writer_waits_until_read_snapshot_finishes(self):
        reader_selected = Event()
        writer_started = Event()
        writer_acquired = Event()

        def reader():
            connection = connections[self.alias]

            def pause(execute, sql, params, many, context):
                result = execute(sql, params, many, context)
                if sql.startswith("SELECT") and not reader_selected.is_set():
                    reader_selected.set()
                    if not writer_started.wait(3):
                        raise AssertionError("Writer did not try to begin")
                    self.assertFalse(writer_acquired.is_set())
                return result

            try:
                with connection.execute_wrapper(pause):
                    return audit_legacy_stat_allocations(self.profile.pk, using=self.alias)
            finally:
                connection.close()

        def writer():
            connection = connections[self.alias]

            def observe(execute, sql, params, many, context):
                if sql == "BEGIN IMMEDIATE":
                    writer_started.set()
                    result = execute(sql, params, many, context)
                    writer_acquired.set()
                    return result
                return execute(sql, params, many, context)

            try:
                if not reader_selected.wait(3):
                    raise AssertionError("Reader did not begin")
                with connection.execute_wrapper(observe):
                    return allocate_stat_points(self.profile, "atk", 3, "t04-file-second")
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            read_future = pool.submit(reader)
            write_future = pool.submit(writer)
            observed = read_future.result(timeout=12)
            written = write_future.result(timeout=12)

        self.assertEqual(observed.status, StatAllocationAuditStatus.OBSERVED_CONSISTENT)
        self.assertEqual(observed.s7_valid_event_ids, (self.first.allocation_event_id,))
        self.assertTrue(writer_acquired.is_set())
        self.assertEqual(written.available_points_after, 9)
        after = audit_legacy_stat_allocations(self.profile.pk, using=self.alias)
        self.assertEqual(after.observed_event_count, 2)
        self.assertEqual(after.s7_valid_event_ids, (
            self.first.allocation_event_id, written.allocation_event_id,
        ))
