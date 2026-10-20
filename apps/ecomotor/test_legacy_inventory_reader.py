"""A3.2: synthetic fixtures only; real SQLite transactions and independent threads."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, get_ident
import traceback
from unittest.mock import patch

from django.apps import apps
from django.db import DatabaseError, OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Model, QuerySet
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileEcomotor

from . import initialization_config, legacy_inventory_reader as reader, legacy_transition_audit as auditor
from .legacy_inventory_reader import (
    InvalidLegacyDatabaseAliasError, InvalidLegacyProfileIdError,
    LegacyForeignCausalityError, LegacyInventoryEvidenceError,
    LegacyInventoryReadError, LegacyInventoryTransactionError,
    LegacyProfileNotFoundError, extract_legacy_audit_snapshot,
)
from .legacy_transition_audit import LegacyAuditSnapshot, LegacyAuditStatus
from .models import CharacterStats, EvolutionEvent, EvolutionStage, XPEvent
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import IdempotencyConflictError, grant_historical_xp


class LegacyInventoryReaderTests(TransactionTestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="a32-synthetic-owner")
        self.connection = connections["default"]
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def extract(self):
        return extract_legacy_audit_snapshot(self.profile.pk, using="default")

    def all_state(self):
        return {model._meta.label: list(model.objects.order_by("pk").values())
                for model in apps.get_models()}

    def assert_complete(self, snapshot):
        self.assertIs(type(snapshot), LegacyAuditSnapshot)
        self.assertEqual(asdict(snapshot.coverage), {
            "xp_events_complete": True, "evolution_events_complete": True,
            "stages_complete": True, "character_stats_observed": True,
        })

    def assert_clean_boundary(self):
        self.assertFalse(self.connection.in_atomic_block)
        self.assertTrue(self.connection.get_autocommit())
        self.assertFalse(self.connection.connection.in_transaction)

    def test_initial_profile_empty_events_and_full_catalog(self):
        snapshot = self.extract()
        self.assert_complete(snapshot)
        self.assertEqual(snapshot.profile.profile_id, self.profile.pk)
        self.assertEqual(snapshot.profile.historical_xp_total, 0)
        self.assertEqual(snapshot.xp_events, ())
        self.assertEqual(snapshot.evolution_events, ())
        self.assertEqual(len(snapshot.stages), 7)
        self.assertEqual(tuple(row.code for row in snapshot.stages), XP_CONFIGURATION.ordered_stage_codes)
        self.assertEqual(snapshot.character_stats.atk, 2)
        self.assertEqual(snapshot.character_stats.available_points, 7)
        self.assert_clean_boundary()

    def test_profile_id_strict_and_representable_before_any_queries(self):
        for value in (0, -1, True, False, 1.0, "1", None, 2**63, {}, self.profile,
                      UserProfileEcomotor.objects.all()):
            with self.subTest(kind=type(value)), CaptureQueriesContext(self.connection) as queries:
                with self.assertRaises(InvalidLegacyProfileIdError):
                    extract_legacy_audit_snapshot(value, using="default")
            self.assertEqual(len(queries), 0)

    def test_alias_mandatory_configured_and_exact_string(self):
        with self.assertRaises(TypeError):
            extract_legacy_audit_snapshot(self.profile.pk)
        for alias in (None, 1, True, "", "a32-unknown", {}, []):
            with self.subTest(kind=type(alias)), self.assertRaises(InvalidLegacyDatabaseAliasError):
                extract_legacy_audit_snapshot(self.profile.pk, using=alias)

    def test_absent_profile_is_explicit_error(self):
        with self.assertRaises(LegacyProfileNotFoundError):
            extract_legacy_audit_snapshot(2**63 - 1, using="default")
        self.assert_clean_boundary()

    def test_active_outer_atomic_transaction_rejected_without_selects(self):
        with transaction.atomic(), CaptureQueriesContext(self.connection) as queries:
            with self.assertRaises(LegacyInventoryTransactionError):
                self.extract()
        self.assertEqual(len(queries), 0)

    def test_manual_autocommit_off_rejected(self):
        self.connection.set_autocommit(False)
        try:
            with self.assertRaises(LegacyInventoryTransactionError):
                self.extract()
        finally:
            self.connection.rollback()
            self.connection.set_autocommit(True)

    def test_raw_outer_transaction_rejected(self):
        with self.connection.cursor() as cursor:
            cursor.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaises(LegacyInventoryTransactionError):
                self.extract()
        finally:
            self.connection.rollback()

    def test_incompatible_connection_options_rejected_without_changing_them(self):
        for options in ({"transaction_mode": "DEFERRED", "timeout": 5},
                        {"transaction_mode": "IMMEDIATE", "timeout": 1}, {},
                        {"transaction_mode": "IMMEDIATE", "timeout": 5, "autocommit": True},
                        {"transaction_mode": "EXCLUSIVE", "timeout": 5}):
            with self.subTest(options=options), patch.dict(self.connection.settings_dict, OPTIONS=options):
                with self.assertRaises(LegacyInventoryTransactionError):
                    self.extract()
                self.assertEqual(self.connection.settings_dict["OPTIONS"], options)

    def test_non_sqlite_or_effective_mode_mismatch_rejected(self):
        for name, value in (("vendor", "postgresql"), ("transaction_mode", "DEFERRED")):
            with self.subTest(name=name), patch.object(self.connection, name, value):
                with self.assertRaises(LegacyInventoryTransactionError):
                    self.extract()

    def test_native_sqlite_autocommit_override_rejected_without_leaking_a_transaction(self):
        if not hasattr(self.connection.connection, "autocommit"):
            self.skipTest("Native autocommit override is available starting in Python 3.12.")
        native = self.connection.connection
        previous = native.autocommit
        native.autocommit = True
        try:
            with self.assertRaises(LegacyInventoryTransactionError):
                self.extract()
            self.assertFalse(native.in_transaction)
        finally:
            native.autocommit = previous

    def test_stats_absence_is_observed_not_initialized(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        snapshot = self.extract()
        self.assert_complete(snapshot)
        self.assertIsNone(snapshot.character_stats)
        self.assertFalse(CharacterStats.objects.filter(profile=self.profile).exists())
        result = auditor.audit_legacy_transition(snapshot)
        self.assertIn("CHARACTER_STATS_MISSING", {issue.code for issue in result.issues})

    def test_single_xp_without_evolution_and_exact_spaced_key(self):
        key = "  a32-synthetic exact key  "
        grant_historical_xp(self.profile, 3, key)
        snapshot = self.extract()
        self.assertEqual(len(snapshot.xp_events), 1)
        self.assertEqual(snapshot.xp_events[0].operation_key, key)
        self.assertEqual((snapshot.xp_events[0].amount, snapshot.xp_events[0].xp_before,
                          snapshot.xp_events[0].xp_after), (3, 0, 3))
        self.assertEqual(snapshot.evolution_events, ())

    def test_multiple_grants_evolutions_and_snapshots_preserved(self):
        first = grant_historical_xp(self.profile, 17, "a32-synthetic-first")
        second = grant_historical_xp(self.profile, 34, "a32-synthetic-second")
        snapshot = self.extract()
        self.assert_complete(snapshot)
        self.assertEqual(tuple(row.id for row in snapshot.xp_events), (first.xp_event_id, second.xp_event_id))
        self.assertEqual(tuple(row.xp_event_id for row in snapshot.evolution_events),
                         (first.xp_event_id, second.xp_event_id, second.xp_event_id))
        self.assertEqual(snapshot.profile.historical_xp_total, 51)
        self.assertEqual(snapshot.character_stats.available_points, 14)

    def test_pk_order_is_not_current_stage_ordinal_order_or_functional_chronology(self):
        # Explicit synthetic PKs intentionally disagree with XP/ordinal order.
        XPEvent.objects.create(id=400, profile=self.profile, operation_key="a32-early",
                               amount=2, xp_before=0, xp_after=2)
        XPEvent.objects.create(id=300, profile=self.profile, operation_key="a32-late",
                               amount=3, xp_before=2, xp_after=5)
        EvolutionStage.objects.all().delete()
        EvolutionStage.objects.create(id=400, code="a32-epoch-one", name="Synthetic", ordinal=1, minimum_xp=0)
        EvolutionStage.objects.create(id=300, code="a32-epoch-two", name="Synthetic", ordinal=2, minimum_xp=9)
        EvolutionEvent.objects.create(id=400, profile=self.profile, xp_event_id=400, stage_id=400)
        EvolutionEvent.objects.create(id=300, profile=self.profile, xp_event_id=300, stage_id=300)
        snapshot = self.extract()
        for rows in (snapshot.xp_events, snapshot.evolution_events, snapshot.stages):
            self.assertEqual(tuple(row.id for row in rows), (300, 400))

    def test_representable_incoherence_is_not_normalized_or_repaired(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="a32-unknown", current_level=888)
        CharacterStats.objects.filter(profile=self.profile).update(atk=-123)
        snapshot = self.extract()
        self.assertEqual(snapshot.profile.current_stage_code, "a32-unknown")
        self.assertEqual(snapshot.profile.current_level, 888)
        self.assertEqual(snapshot.character_stats.atk, -123)
        self.assert_complete(snapshot)
        self.assertEqual(auditor.audit_legacy_transition(snapshot).status, LegacyAuditStatus.INCONSISTENT)

    def test_empty_catalog_is_full_observed_evidence(self):
        EvolutionStage.objects.all().delete()
        snapshot = self.extract()
        self.assertEqual(snapshot.stages, ())
        self.assert_complete(snapshot)

    def test_independent_profile_history_never_included(self):
        other = create_xp_profile(username="a32-synthetic-other")
        foreign = grant_historical_xp(other, 17, "a32-foreign-secret")
        snapshot = self.extract()
        self.assertEqual(snapshot.xp_events, ())
        self.assertEqual(snapshot.evolution_events, ())
        self.assertNotIn(str(foreign.operation_key), repr(snapshot))

    def assert_foreign_error_safe(self):
        with self.assertRaises(LegacyForeignCausalityError) as caught:
            self.extract()
        self.assertEqual(str(caught.exception), "Cross-profile evolution causality detected.")
        self.assertIsNone(caught.exception.__cause__)
        self.assert_clean_boundary()

    def test_own_evolution_with_foreign_cause_rejected(self):
        other = create_xp_profile(username="a32-foreign-cause-owner")
        foreign = grant_historical_xp(other, 3, "a32-foreign-secret")
        EvolutionEvent.objects.create(profile=self.profile, xp_event_id=foreign.xp_event_id,
                                      stage=EvolutionStage.objects.get(ordinal=2))
        self.assert_foreign_error_safe()

    def test_foreign_evolution_with_own_cause_rejected(self):
        own = grant_historical_xp(self.profile, 3, "a32-own-cause")
        other = create_xp_profile(username="a32-foreign-evolution-owner")
        EvolutionEvent.objects.create(profile=other, xp_event_id=own.xp_event_id,
                                      stage=EvolutionStage.objects.get(ordinal=2))
        self.assert_foreign_error_safe()

    def test_real_missing_cause_preserved_for_independent_audit(self):
        # TEST ONLY: controlled orphan fixture. Production never changes PRAGMAs.
        with self.connection.constraint_checks_disabled():
            event = EvolutionEvent.objects.create(profile=self.profile, xp_event_id=900001,
                                                  stage=EvolutionStage.objects.get(ordinal=2))
            try:
                snapshot = self.extract()
                self.assert_complete(snapshot)
                self.assertEqual(snapshot.evolution_events[0].xp_event_id, 900001)
                self.assertEqual(snapshot.xp_events, ())
                result = auditor.audit_legacy_transition(snapshot)
                self.assertIn("XP_CAUSE_NOT_FOUND", {issue.code for issue in result.issues})
            finally:
                event.delete()

    def test_missing_stage_reference_is_not_discarded_by_join(self):
        own = grant_historical_xp(self.profile, 3, "a32-orphan-stage-cause")
        with self.connection.constraint_checks_disabled():
            event = EvolutionEvent.objects.create(profile=self.profile, xp_event_id=own.xp_event_id, stage_id=900002)
            try:
                snapshot = self.extract()
                self.assertEqual(snapshot.evolution_events[0].stage_id, 900002)
                self.assert_complete(snapshot)
            finally:
                event.delete()

    def test_each_sql_read_failure_returns_safe_error_never_partial_snapshot(self):
        # Five materialization SELECTs and both minimal causality SELECTs.
        for fail_at in range(1, 8):
            seen = 0
            payload = "a32-sensitive-operation SQL foreign-id-900003"

            def fail(execute, sql, params, many, context):
                nonlocal seen
                if sql.lstrip().upper().startswith("SELECT"):
                    seen += 1
                    if seen == fail_at:
                        raise OperationalError(payload)
                return execute(sql, params, many, context)

            with self.subTest(select=fail_at), self.connection.execute_wrapper(fail):
                with self.assertRaises(LegacyInventoryReadError) as caught:
                    self.extract()
            self.assertEqual(seen, fail_at)
            self.assertNotIn(payload, "".join(traceback.format_exception(caught.exception)))
            self.assertIsNone(caught.exception.__cause__)
            self.assertTrue(caught.exception.__suppress_context__)
            self.assert_clean_boundary()

    def test_connection_open_and_commit_failures_do_not_return_success(self):
        for method in ("ensure_connection", "commit"):
            with self.subTest(method=method), patch.object(self.connection, method, side_effect=DatabaseError("sensitive")):
                with self.assertRaises(LegacyInventoryReadError) as caught:
                    self.extract()
            self.assertEqual(str(caught.exception), "Legacy inventory could not be read.")
            self.assert_clean_boundary()

    def test_nonrepresentable_persisted_evidence_fails_without_coercion(self):
        # SQLite permits text in an INTEGER affinity column: no ORM coercion in fixture.
        with self.connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_characterstats SET atk = %s WHERE profile_id = %s",
                           ("a32-not-an-integer", self.profile.pk))
        with self.assertRaises(LegacyInventoryEvidenceError) as caught:
            self.extract()
        self.assertIsNone(caught.exception.__cause__)
        self.assertNotIn("a32-not-an-integer", "".join(traceback.format_exception(caught.exception)))
        self.assert_clean_boundary()

    def test_evidence_error_hides_sensitive_internal_chain(self):
        payload = "a32-sensitive-snapshot-payload"
        with patch.object(reader, "LegacyXPEventSnapshot", side_effect=auditor.InvalidLegacySnapshotError(payload)):
            grant_historical_xp(self.profile, 3, "a32-synthetic-for-evidence-error")
            with self.assertRaises(LegacyInventoryEvidenceError) as caught:
                self.extract()
        self.assertNotIn(payload, "".join(traceback.format_exception(caught.exception)))

    def test_arbitrary_programming_error_not_disguised_as_read_error(self):
        with patch.object(reader, "LegacyProfileSnapshot", side_effect=RuntimeError("programming error")):
            with self.assertRaisesRegex(RuntimeError, "programming error"):
                self.extract()
        self.assert_clean_boundary()

    def test_materialized_immutable_types_and_no_deferred_queries(self):
        grant_historical_xp(self.profile, 17, "a32-synthetic-materialized")
        snapshot = self.extract()
        with CaptureQueriesContext(self.connection) as queries:
            before = asdict(snapshot)

            def visit(value):
                self.assertNotIsInstance(value, (Model, QuerySet))
                if is_dataclass(value):
                    field = fields(value)[0]
                    with self.assertRaises(FrozenInstanceError):
                        setattr(value, field.name, None)
                    for field in fields(value):
                        visit(getattr(value, field.name))
                elif isinstance(value, tuple):
                    for item in value:
                        visit(item)
            visit(snapshot)
            self.assertEqual(before, asdict(snapshot))
        self.assertEqual(len(queries), 0)

    def test_every_query_in_same_transaction_no_business_writes_or_user_data(self):
        statements = []

        def observe(execute, sql, params, many, context):
            statements.append(sql)
            if sql.lstrip().upper().startswith("SELECT"):
                self.assertTrue(context["connection"].in_atomic_block)
                self.assertIs(context["connection"], self.connection)
            return execute(sql, params, many, context)

        before = self.all_state()
        with self.connection.execute_wrapper(observe):
            self.extract()
        self.assertEqual(statements[0], "BEGIN IMMEDIATE")
        self.assertEqual(len([sql for sql in statements if sql.startswith("SELECT")]), 7)
        self.assertTrue(all(sql.startswith(("SELECT", "BEGIN IMMEDIATE")) for sql in statements))
        for private in ("auth_user", "username", "password", "email", "select_for_update", "PRAGMA"):
            self.assertNotIn(private.lower(), " ".join(statements).lower())
        self.assertEqual(self.all_state(), before)

    def test_separate_audit_only_when_explicitly_requested(self):
        with patch.object(auditor, "audit_legacy_transition", side_effect=AssertionError), \
                patch("apps.ecomotor.target_catalog_validation.validate_target_level_epoch_catalog", side_effect=AssertionError), \
                patch("apps.ecomotor.target_progression.calculate_target_progression", side_effect=AssertionError), \
                patch("apps.ecomotor.target_xp_plan.plan_target_xp_grant", side_effect=AssertionError):
            snapshot = self.extract()
        self.assertEqual(auditor.audit_legacy_transition(snapshot).status, LegacyAuditStatus.COMPATIBLE)

    def test_reader_never_logs_or_prints_evidence(self):
        grant_historical_xp(self.profile, 3, "a32-sensitive-key-not-for-logs")
        with patch("builtins.print") as output, patch("logging.Logger._log") as log:
            self.extract()
        output.assert_not_called()
        log.assert_not_called()

    def test_s3_preserves_points_causality_replay_conflict_and_never_calls_reader(self):
        with patch.object(reader, "extract_legacy_audit_snapshot", side_effect=AssertionError):
            first = grant_historical_xp(self.profile, 51, "a32-synthetic-v1")
            before = self.all_state()
            replay = grant_historical_xp(self.profile, 51, "a32-synthetic-v1")
            with self.assertRaises(IdempotencyConflictError):
                grant_historical_xp(self.profile, 52, "a32-synthetic-v1")
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.xp_event_id, first.xp_event_id)
        self.assertEqual((first.stat_points_awarded, first.available_points_after), (7, 14))
        self.assertEqual(len(first.evolution_event_ids), 3)
        snapshot = self.extract()
        self.assertTrue(all(row.xp_event_id == first.xp_event_id for row in snapshot.evolution_events))
        self.assertEqual(self.all_state(), before)


class LegacyInventoryFileTests(TransactionTestCase):
    """Real file-backed alias, with the unmodified approved SQLite options."""

    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-a32-inventory-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "a32_file_test"
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
        self.profile = create_xp_profile(self.alias, username="a32-synthetic-file")
        config_patch = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config_patch.start()
        self.addCleanup(config_patch.stop)

    def close_database(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def test_alternative_alias_used_for_all_reads_without_default_access(self):
        grant_historical_xp(self.profile, 17, "a32-alias-only")
        create_xp_profile(username="a32-default-other")
        with CaptureQueriesContext(connections["default"]) as queries:
            snapshot = extract_legacy_audit_snapshot(self.profile.pk, using=self.alias)
        self.assertEqual(len(queries), 0)
        self.assertEqual(snapshot.profile.historical_xp_total, 17)
        self.assertEqual(snapshot.xp_events[0].operation_key, "a32-alias-only")
        with self.assertRaises(LegacyProfileNotFoundError):
            extract_legacy_audit_snapshot(2**63 - 1, using=self.alias)

    def overlap_reader_with_writer(self, amount):
        reader_selected = Event()
        writer_begin = Event()
        writer_acquired = Event()
        writer_committed = Event()

        def read():
            connection = connections[self.alias]
            statements = []

            def observe(execute, sql, params, many, context):
                statements.append(sql)
                result = execute(sql, params, many, context)
                if sql.startswith("SELECT"):
                    self.assertTrue(connection.in_atomic_block)
                    self.assertEqual(context["connection"].alias, self.alias)
                    if not reader_selected.is_set():
                        reader_selected.set()
                        if not writer_begin.wait(3):
                            raise AssertionError("Writer did not attempt its transaction.")
                        self.assertFalse(writer_acquired.is_set())
                        self.assertFalse(writer_committed.is_set())
                return result

            try:
                with connection.execute_wrapper(observe):
                    snapshot = extract_legacy_audit_snapshot(self.profile.pk, using=self.alias)
                return snapshot, get_ident(), id(connection.connection), statements
            finally:
                connection.close()

        def write():
            connection = connections[self.alias]

            def observe(execute, sql, params, many, context):
                if sql == "BEGIN IMMEDIATE":
                    writer_begin.set()
                    result = execute(sql, params, many, context)
                    writer_acquired.set()
                    return result
                return execute(sql, params, many, context)

            try:
                if not reader_selected.wait(3):
                    raise AssertionError("Reader did not acquire its transaction.")
                with connection.execute_wrapper(observe):
                    result = grant_historical_xp(self.profile, amount, "a32-concurrent-writer")
                writer_committed.set()
                return result, get_ident(), id(connection.connection)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            read_future = pool.submit(read)
            write_future = pool.submit(write)
            observed = read_future.result(timeout=12)
            confirmed = write_future.result(timeout=12)
        self.assertNotEqual(observed[1], confirmed[1])
        self.assertNotEqual(observed[2], confirmed[2])
        self.assertTrue(writer_committed.is_set())
        self.assertEqual(observed[3][0], "BEGIN IMMEDIATE")
        self.assertTrue(all(sql.startswith(("SELECT", "BEGIN IMMEDIATE")) for sql in observed[3]))
        return observed[0], confirmed[0]

    def test_writer_waits_then_continues_without_interleaving_initial_snapshot(self):
        snapshot, result = self.overlap_reader_with_writer(17)
        self.assertEqual(snapshot.profile.historical_xp_total, 0)
        self.assertEqual(snapshot.character_stats.available_points, 7)
        self.assertEqual(snapshot.xp_events, ())
        self.assertEqual(snapshot.evolution_events, ())
        later = extract_legacy_audit_snapshot(self.profile.pk, using=self.alias)
        self.assertEqual(later.profile.historical_xp_total, 17)
        self.assertEqual(later.character_stats.available_points, 9)
        self.assertEqual(later.xp_events[0].id, result.xp_event_id)
        self.assertEqual(len(later.evolution_events), 1)

    def test_existing_snapshot_does_not_mix_second_grant_or_evolutions(self):
        first = grant_historical_xp(self.profile, 17, "a32-before-overlap")
        snapshot, result = self.overlap_reader_with_writer(34)
        self.assertEqual(snapshot.profile.historical_xp_total, 17)
        self.assertEqual(snapshot.character_stats.available_points, 9)
        self.assertEqual(tuple(row.id for row in snapshot.xp_events), (first.xp_event_id,))
        self.assertEqual(len(snapshot.evolution_events), 1)
        self.assertEqual(result.xp_after, 51)
        later = extract_legacy_audit_snapshot(self.profile.pk, using=self.alias)
        self.assertEqual(later.profile.historical_xp_total, 51)
        self.assertEqual(later.character_stats.available_points, 14)
        self.assertEqual(len(later.xp_events), 2)
        self.assertEqual(len(later.evolution_events), 3)

    def test_real_lock_timeout_is_safe_and_new_extraction_succeeds(self):
        def read():
            connection = connections[self.alias]
            try:
                try:
                    value = extract_legacy_audit_snapshot(self.profile.pk, using=self.alias)
                except LegacyInventoryReadError as error:
                    value = error
                clean = (not connection.in_atomic_block and connection.get_autocommit()
                         and not connection.connection.in_transaction)
                return value, clean
            finally:
                connection.close()

        before = tuple(XPEvent.objects.using(self.alias).values_list("id", flat=True))
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic(using=self.alias):
                failed, clean = pool.submit(read).result(timeout=12)
                self.assertIsInstance(failed, LegacyInventoryReadError)
                self.assertIsNone(failed.__cause__)
                self.assertTrue(failed.__suppress_context__)
                self.assertTrue(clean)
            snapshot, clean = pool.submit(read).result(timeout=12)
        self.assertTrue(clean)
        self.assertIs(type(snapshot), LegacyAuditSnapshot)
        self.assertEqual(snapshot.profile.historical_xp_total, 0)
        self.assertEqual(tuple(row.id for row in snapshot.xp_events), before)
        self.assertFalse(self.connection.in_atomic_block)
