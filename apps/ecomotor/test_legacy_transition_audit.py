"""A3.1 tests: every identity, amount and catalog below is synthetic."""

from dataclasses import FrozenInstanceError, asdict, replace
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from unittest import TestCase
from unittest.mock import patch

from django.test import TestCase as DatabaseTestCase
from django.test.utils import CaptureQueriesContext

from . import legacy_transition_audit as audit
from .legacy_transition_audit import (
    InvalidLegacySnapshotError, LegacyAuditCoverage, LegacyAuditIssue,
    LegacyAuditResult, LegacyAuditSnapshot, LegacyAuditStatus as Status,
    LegacyCharacterStatsSnapshot, LegacyEvolutionEventSnapshot,
    LegacyProfileSnapshot, LegacyStageSnapshot, LegacyXPEventSnapshot,
    audit_legacy_transition,
)


def synthetic_snapshot():
    return LegacyAuditSnapshot(
        profile=LegacyProfileSnapshot(1, 20, 2, "synthetic-stage-2"),
        character_stats=LegacyCharacterStatsSnapshot(1, -2, 3, 4, 5, 6, 7, 9),
        xp_events=(LegacyXPEventSnapshot(9, 1, "synthetic-fact", 20, 0, 20),),
        evolution_events=(LegacyEvolutionEventSnapshot(5, 1, 9, 2),),
        stages=(LegacyStageSnapshot(1, "synthetic-stage-1", 1, 0),
                LegacyStageSnapshot(2, "synthetic-stage-2", 2, 13)),
        coverage=LegacyAuditCoverage(True, True, True, True),
    )


class LegacyTransitionAuditTests(TestCase):
    def setUp(self):
        self.snapshot = synthetic_snapshot()

    def run_audit(self, **changes):
        return audit_legacy_transition(replace(self.snapshot, **changes))

    def assert_issue(self, result, code, status=Status.INCONSISTENT):
        self.assertEqual(result.status, status)
        self.assertIn(code, {item.code for item in result.issues})

    def test_coherent_v1_subset_compatible_without_migration_authorization(self):
        result = self.run_audit()
        self.assertEqual(result, LegacyAuditResult(1, Status.COMPATIBLE, ()))
        self.assertEqual(set(asdict(result)), {"profile_id", "status", "issues"})
        self.assertIn("Never migration approval", LegacyAuditResult.__doc__)

    def test_initial_zero_profile_with_complete_empty_histories(self):
        result = self.run_audit(
            profile=LegacyProfileSnapshot(1, 0, 1, "synthetic-stage-1"),
            xp_events=(), evolution_events=(),
        )
        self.assertEqual(result.status, Status.COMPATIBLE)

    def test_xp_without_evolution_is_valid(self):
        self.assertEqual(self.run_audit(evolution_events=()).status, Status.COMPATIBLE)

    def test_order_independence_with_multiple_events(self):
        xp = self.snapshot.xp_events + (LegacyXPEventSnapshot(3, 1, "synthetic-second", 3, 1, 4),)
        evolutions = self.snapshot.evolution_events + (LegacyEvolutionEventSnapshot(7, 1, 3, 1),)
        first = self.run_audit(xp_events=xp, evolution_events=evolutions)
        second = self.run_audit(xp_events=xp[::-1], evolution_events=evolutions[::-1],
                                stages=self.snapshot.stages[::-1])
        self.assertEqual(first, second)
        self.assertEqual(first.status, Status.COMPATIBLE)

    def test_no_chronology_or_exhaustive_history_inferred_from_pk_or_sum(self):
        # Gaps and reversed PK chronology do not prove corruption or completeness.
        xp = (LegacyXPEventSnapshot(99, 1, "synthetic-early", 2, 3, 5),
              LegacyXPEventSnapshot(1, 1, "synthetic-late", 1, 19, 20))
        result = self.run_audit(xp_events=xp, evolution_events=())
        self.assertEqual(result.status, Status.COMPATIBLE)

    def test_every_incomplete_coverage_flag_requires_review(self):
        for name in asdict(self.snapshot.coverage):
            with self.subTest(name=name):
                result = self.run_audit(coverage=replace(self.snapshot.coverage, **{name: False}))
                self.assert_issue(result, "EVIDENCE_INCOMPLETE", Status.REQUIRES_DECISION)

    def test_unobserved_stats_not_equivalent_to_checked_absence(self):
        result = self.run_audit(character_stats=None, coverage=replace(
            self.snapshot.coverage, character_stats_observed=False))
        self.assert_issue(result, "EVIDENCE_INCOMPLETE", Status.REQUIRES_DECISION)
        self.assertNotIn("CHARACTER_STATS_MISSING", {item.code for item in result.issues})
        self.assert_issue(self.run_audit(character_stats=None), "CHARACTER_STATS_MISSING")

    def test_missing_cause_with_partial_inventory_requires_review(self):
        result = self.run_audit(xp_events=(), coverage=replace(
            self.snapshot.coverage, xp_events_complete=False))
        self.assert_issue(result, "XP_CAUSE_NOT_FOUND", Status.REQUIRES_DECISION)

    def test_missing_cause_with_complete_inventory_is_inconsistent(self):
        self.assert_issue(self.run_audit(xp_events=()), "XP_CAUSE_NOT_FOUND")

    def test_missing_stage_with_partial_inventory_requires_review(self):
        result = self.run_audit(stages=(), coverage=replace(self.snapshot.coverage, stages_complete=False))
        self.assert_issue(result, "STAGE_REFERENCE_NOT_FOUND", Status.REQUIRES_DECISION)
        self.assert_issue(result, "CURRENT_STAGE_NOT_FOUND", Status.REQUIRES_DECISION)

    def test_missing_stage_with_complete_inventory_is_inconsistent(self):
        result = self.run_audit(stages=())
        self.assert_issue(result, "STAGE_REFERENCE_NOT_FOUND")
        self.assert_issue(result, "CURRENT_STAGE_NOT_FOUND")

    def test_accumulated_xp_without_sufficient_history_requires_decision(self):
        for coverage in (True, False):
            with self.subTest(complete=coverage):
                result = self.run_audit(xp_events=(), evolution_events=(), coverage=replace(
                    self.snapshot.coverage, xp_events_complete=coverage))
                self.assert_issue(result, "ACCUMULATED_XP_WITHOUT_SUFFICIENT_HISTORY", Status.REQUIRES_DECISION)

    def test_no_historical_stage_attributes_or_level_reconstruction(self):
        # Current stage metadata cannot establish past thresholds/codes/levels.
        stages = tuple(replace(row, minimum_xp=999, ordinal=7) for row in self.snapshot.stages)
        result = self.run_audit(stages=stages, profile=replace(self.snapshot.profile, current_level=888),
                                coverage=replace(self.snapshot.coverage, stages_complete=False))
        self.assertEqual(result.status, Status.REQUIRES_DECISION)
        self.assertEqual({item.code for item in result.issues}, {"EVIDENCE_INCOMPLETE"})
        self.assertIn("not persisted", audit.__doc__)

    def test_duplicate_xp_identity(self):
        self.assert_issue(self.run_audit(xp_events=self.snapshot.xp_events * 2), "DUPLICATE_XP_ID")

    def test_duplicate_operation_key_for_same_profile(self):
        event = replace(self.snapshot.xp_events[0], id=10)
        self.assert_issue(self.run_audit(xp_events=self.snapshot.xp_events + (event,)), "DUPLICATE_OPERATION_KEY")

    def test_operation_key_uniqueness_is_scoped_to_profile(self):
        event = replace(self.snapshot.xp_events[0], id=10, profile_id=2)
        result = self.run_audit(xp_events=self.snapshot.xp_events + (event,))
        self.assert_issue(result, "XP_PROFILE_MISMATCH")
        self.assertNotIn("DUPLICATE_OPERATION_KEY", {item.code for item in result.issues})

    def test_invalid_xp_arithmetic_amount_range_and_key(self):
        for changes in ({"xp_after": 19}, {"amount": 0}, {"amount": -1},
                        {"xp_before": -1}, {"xp_after": -1}, {"amount": 2**63},
                        {"xp_before": 2**63}, {"xp_after": 2**63},
                        {"operation_key": ""}, {"operation_key": "x" * 256}):
            with self.subTest(changes=changes):
                self.assert_issue(self.run_audit(xp_events=(replace(self.snapshot.xp_events[0], **changes),)),
                                  "INVALID_XP_SNAPSHOT")

    def test_confirmed_xp_above_current_total(self):
        self.assert_issue(self.run_audit(profile=replace(self.snapshot.profile, historical_xp_total=19)),
                          "XP_EXCEEDS_PROFILE_TOTAL")

    def test_foreign_xp_and_causal_owner_mismatch(self):
        result = self.run_audit(xp_events=(replace(self.snapshot.xp_events[0], profile_id=2),))
        self.assert_issue(result, "XP_PROFILE_MISMATCH")
        self.assert_issue(result, "EVOLUTION_CAUSE_PROFILE_MISMATCH")

    def test_duplicate_evolution_identity_and_profile_stage(self):
        self.assert_issue(self.run_audit(evolution_events=self.snapshot.evolution_events * 2),
                          "DUPLICATE_EVOLUTION_ID")
        event = replace(self.snapshot.evolution_events[0], id=6)
        self.assert_issue(self.run_audit(evolution_events=self.snapshot.evolution_events + (event,)),
                          "DUPLICATE_PROFILE_EVOLUTION")

    def test_foreign_evolution_rejected_even_if_cause_has_same_foreign_owner(self):
        result = self.run_audit(xp_events=(replace(self.snapshot.xp_events[0], profile_id=2),),
                                evolution_events=(replace(self.snapshot.evolution_events[0], profile_id=2),))
        self.assert_issue(result, "EVOLUTION_PROFILE_MISMATCH")

    def test_conflicting_duplicate_cause_does_not_choose_arbitrary_owner(self):
        xp = self.snapshot.xp_events + (replace(self.snapshot.xp_events[0], profile_id=2),)
        first = self.run_audit(xp_events=xp)
        self.assertEqual(first, self.run_audit(xp_events=xp[::-1]))
        self.assert_issue(first, "EVOLUTION_CAUSE_PROFILE_MISMATCH")

    def test_stats_owner_and_technical_ranges(self):
        self.assert_issue(self.run_audit(character_stats=replace(self.snapshot.character_stats, profile_id=2)),
                          "STATS_PROFILE_MISMATCH")
        for name in ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points"):
            for value in ((-1, 2**63) if name == "available_points" else (-2**63 - 1, 2**63)):
                with self.subTest(name=name, value=value):
                    self.assert_issue(self.run_audit(character_stats=replace(self.snapshot.character_stats, **{name: value})),
                                      "INVALID_STATS_VALUES")

    def test_signed_stats_boundaries_and_legacy_points_are_not_gameplay_policy(self):
        stats = replace(self.snapshot.character_stats, atk=-2**63, def_stat=2**63 - 1,
                        available_points=2**63 - 1)
        self.assertEqual(self.run_audit(character_stats=stats).status, Status.COMPATIBLE)

    def test_invalid_profile_values_are_diagnostics_not_repairs(self):
        for changes in ({"historical_xp_total": -1}, {"historical_xp_total": 2**63},
                        {"current_level": 0}, {"current_level": 2**63},
                        {"current_stage_code": ""}, {"current_stage_code": "x" * 33},
                        {"active_specialization_code": ""}):
            with self.subTest(changes=changes):
                self.assert_issue(self.run_audit(profile=replace(self.snapshot.profile, **changes)),
                                  "INVALID_PROFILE_VALUES")

    def test_duplicate_stage_pk_code_and_ordinal(self):
        for row, code in ((self.snapshot.stages[0], "DUPLICATE_STAGE_ID"),
                          (replace(self.snapshot.stages[0], id=3), "DUPLICATE_STAGE_CODE"),
                          (replace(self.snapshot.stages[0], id=3, code="synthetic-other"), "DUPLICATE_STAGE_ORDINAL")):
            with self.subTest(code=code):
                self.assert_issue(self.run_audit(stages=self.snapshot.stages + (row,)), code)

    def test_invalid_stage_values(self):
        for changes in ({"code": ""}, {"code": "x" * 33}, {"ordinal": 0},
                        {"ordinal": 8}, {"minimum_xp": -1}, {"minimum_xp": 2**63}):
            with self.subTest(changes=changes):
                stages = (replace(self.snapshot.stages[0], **changes), self.snapshot.stages[1])
                self.assert_issue(self.run_audit(stages=stages), "INVALID_STAGE_VALUES")

    def test_partial_stage_codes_and_ordinals_do_not_claim_complete_catalog_validation(self):
        stages = self.snapshot.stages + (replace(self.snapshot.stages[0], id=3),)
        result = self.run_audit(stages=stages, coverage=replace(self.snapshot.coverage, stages_complete=False))
        self.assertEqual(result.status, Status.REQUIRES_DECISION)
        self.assertEqual({item.code for item in result.issues}, {"EVIDENCE_INCOMPLETE"})

    def test_opaque_operation_key_is_not_trimmed_or_exposed(self):
        event = replace(self.snapshot.xp_events[0], operation_key=" ")
        self.assertEqual(self.run_audit(xp_events=(event,)).status, Status.COMPATIBLE)

    def test_multiple_issues_and_precedence_keep_secondary_evidence_gaps(self):
        result = self.run_audit(xp_events=self.snapshot.xp_events * 2, character_stats=None,
                                coverage=LegacyAuditCoverage(False, False, False, False))
        self.assert_issue(result, "DUPLICATE_XP_ID")
        self.assertIn("EVIDENCE_INCOMPLETE", {item.code for item in result.issues})
        self.assertEqual(result, self.run_audit(xp_events=self.snapshot.xp_events * 2, character_stats=None,
                                               coverage=LegacyAuditCoverage(False, False, False, False)))

    def test_typed_snapshot_required_not_mapping_or_model_like_object(self):
        for value in (None, {}, asdict(self.snapshot), object()):
            with self.subTest(value=type(value)), self.assertRaises(InvalidLegacySnapshotError):
                audit_legacy_transition(value)
        with self.assertRaises(InvalidLegacySnapshotError):
            replace(self.snapshot, profile=asdict(self.snapshot.profile))

    def test_strict_types_bool_fraction_text_none_rejected(self):
        for row in (self.snapshot.profile, self.snapshot.character_stats, self.snapshot.xp_events[0],
                    self.snapshot.evolution_events[0], self.snapshot.stages[0]):
            for name, original in asdict(row).items():
                if type(original) is int:
                    for value in (True, False, 1.0, Decimal("1"), "1", None, []):
                        with self.subTest(row=type(row), name=name, value=value), self.assertRaises(InvalidLegacySnapshotError):
                            replace(row, **{name: value})
                elif type(original) is str:
                    for value in ([], {}, 1, None):
                        with self.subTest(row=type(row), name=name), self.assertRaises(InvalidLegacySnapshotError):
                            replace(row, **{name: value})

    def test_invalid_identifiers_rejected_before_audit(self):
        for name in ("id", "profile_id", "xp_event_id", "stage_id"):
            for value in (0, -1, 2**63):
                with self.subTest(name=name, value=value), self.assertRaises(InvalidLegacySnapshotError):
                    replace(self.snapshot.evolution_events[0], **{name: value})

    def test_coverage_requires_exact_boolean_and_typed_stats(self):
        for value in (1, 0, None, "true", []):
            with self.subTest(value=value), self.assertRaises(InvalidLegacySnapshotError):
                replace(self.snapshot.coverage, xp_events_complete=value)
        for changes in ({"coverage": {}}, {"character_stats": {}}):
            with self.assertRaises(InvalidLegacySnapshotError):
                replace(self.snapshot, **changes)

    def test_explicit_collections_only_no_iterators_nested_mutability_or_strings(self):
        for name in ("xp_events", "evolution_events", "stages"):
            for value in (None, "abc", {}, set(), iter(()), [[]], [{}], [object()]):
                with self.subTest(name=name, value=type(value)), self.assertRaises(InvalidLegacySnapshotError):
                    replace(self.snapshot, **{name: value})

    def test_defensive_copies_and_all_snapshot_dataclasses_frozen(self):
        rows = list(self.snapshot.xp_events)
        snapshot = replace(self.snapshot, xp_events=rows)
        result = audit_legacy_transition(snapshot)
        rows.clear()
        self.assertEqual(snapshot.xp_events, self.snapshot.xp_events)
        self.assertEqual(audit_legacy_transition(snapshot), result)
        for row in (snapshot, snapshot.profile, snapshot.coverage, snapshot.character_stats,
                    *snapshot.xp_events, *snapshot.evolution_events, *snapshot.stages, result):
            name = next(iter(asdict(row)))
            with self.subTest(row=type(row)), self.assertRaises(FrozenInstanceError):
                setattr(row, name, None)

    def test_diagnostics_defensively_copied_immutable_and_no_key_payload(self):
        result = self.run_audit(xp_events=self.snapshot.xp_events * 2)
        rows = list(result.issues)
        copy = LegacyAuditResult(result.profile_id, result.status, rows)
        rows.clear()
        self.assertEqual(copy, result)
        self.assertIsInstance(copy.issues, tuple)
        with self.assertRaises(FrozenInstanceError):
            copy.issues[0].code = "changed"
        self.assertNotIn("synthetic-fact", repr(result))
        for value in ("text", [{}], [["nested"]], iter(())):
            with self.assertRaises(InvalidLegacySnapshotError):
                LegacyAuditResult(1, Status.INCONSISTENT, value)
        with self.assertRaises(InvalidLegacySnapshotError):
            LegacyAuditIssue([], Status.INCONSISTENT, "xp_event")

    def test_no_external_access_or_input_mutation(self):
        before = asdict(self.snapshot)
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError), \
                patch("time.time", side_effect=AssertionError):
            self.assertEqual(self.run_audit(), self.run_audit())
        self.assertEqual(asdict(self.snapshot), before)

    def test_isolated_import_and_execution_does_not_load_django(self):
        code = (
            "import sys; sys.path.insert(0,sys.argv[1]); "
            "from apps.ecomotor.legacy_transition_audit import *; "
            "s=LegacyAuditSnapshot(LegacyProfileSnapshot(1,0,1,'synthetic'),"
            "LegacyCharacterStatsSnapshot(1,0,0,0,0,0,0,0),(),(),"
            "(LegacyStageSnapshot(1,'synthetic',1,0),),LegacyAuditCoverage(True,True,True,True)); "
            "assert audit_legacy_transition(s).status is LegacyAuditStatus.COMPATIBLE; "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules)"
        )
        completed = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)


class LegacyAuditV1IsolationTests(DatabaseTestCase):
    def setUp(self):
        from . import initialization_config
        from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
        create_xp_catalogs()
        self.profile = create_xp_profile(username="a3-synthetic-v1")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def persisted_state(self):
        from apps.users.models import UserProfileEcomotor
        from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent
        return [list(model.objects.order_by("pk").values()) for model in (
            UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent, LevelThreshold, EvolutionStage,
        )]

    def extract_for_test_only(self):
        # Extraction intentionally exists ONLY in this integration test, not in
        # the auditor API. No fixture/adapter is installed in production.
        from .models import CharacterStats, EvolutionEvent, EvolutionStage, XPEvent
        self.profile.refresh_from_db()
        stats = CharacterStats.objects.get(profile=self.profile)
        return LegacyAuditSnapshot(
            LegacyProfileSnapshot(self.profile.pk, self.profile.historical_xp_total,
                                  self.profile.current_level, self.profile.current_stage_code,
                                  self.profile.active_specialization_code),
            LegacyCharacterStatsSnapshot(self.profile.pk, stats.atk, stats.def_stat, stats.log_stat,
                                         stats.spe, stats.vel, stats.int_stat, stats.available_points),
            tuple(LegacyXPEventSnapshot(**row) for row in XPEvent.objects.values(
                "id", "profile_id", "operation_key", "amount", "xp_before", "xp_after")),
            tuple(LegacyEvolutionEventSnapshot(**row) for row in EvolutionEvent.objects.values(
                "id", "profile_id", "xp_event_id", "stage_id")),
            tuple(LegacyStageSnapshot(**row) for row in EvolutionStage.objects.values(
                "id", "code", "ordinal", "minimum_xp")),
            LegacyAuditCoverage(True, True, True, True),
        )

    def test_s3_points_replay_conflicts_without_automatic_audit(self):
        from .models import CharacterStats, XPEvent
        from .xp_service import IdempotencyConflictError, grant_historical_xp
        with patch.object(audit, "audit_legacy_transition", side_effect=AssertionError):
            first = grant_historical_xp(self.profile, 102, "a3-synthetic-grant")
            before = self.persisted_state()
            replay = grant_historical_xp(self.profile, 102, "a3-synthetic-grant")
            with self.assertRaises(IdempotencyConflictError):
                grant_historical_xp(self.profile, 103, "a3-synthetic-grant")
        self.assertEqual((first.stat_points_awarded, first.available_points_after), (7, 14))
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.xp_event_id, first.xp_event_id)
        self.assertEqual(XPEvent.objects.count(), 1)
        self.assertEqual(CharacterStats.objects.get(profile=self.profile).available_points, 14)
        self.assertEqual(self.persisted_state(), before)

    def test_audit_of_real_s3_snapshots_has_zero_queries_and_no_changes(self):
        from django.db import connection
        from .xp_service import grant_historical_xp
        grant_historical_xp(self.profile, 102, "a3-synthetic-observed")
        snapshot = self.extract_for_test_only()
        before = self.persisted_state()
        with CaptureQueriesContext(connection) as queries:
            result = audit_legacy_transition(snapshot)
        self.assertEqual(len(queries), 0)
        self.assertEqual(result.status, Status.COMPATIBLE)
        self.assertEqual(self.persisted_state(), before)

    def test_a11_a12_a21_stay_independent_and_pure(self):
        from django.db import connection
        from .test_target_progression import synthetic_catalog
        from .target_progression import calculate_target_progression
        from .target_xp_plan import plan_target_xp_grant
        before = self.persisted_state()
        with CaptureQueriesContext(connection) as queries, \
                patch.object(audit, "audit_legacy_transition", side_effect=AssertionError):
            catalog = synthetic_catalog()
            plan = plan_target_xp_grant(0, 102, catalog)
            self.assertEqual(plan.progression, calculate_target_progression(0, 102, catalog))
        self.assertEqual(len(queries), 0)
        self.assertEqual(self.persisted_state(), before)

    def test_numeric_ranges_match_current_v1_sqlite_backend_without_inspecting_it_in_audit(self):
        from django.db import connection
        self.assertEqual(connection.vendor, "sqlite")
        self.assertEqual(connection.ops.integer_field_range("IntegerField"), (-2**63, 2**63 - 1))
        for kind in ("PositiveIntegerField", "PositiveBigIntegerField"):
            self.assertEqual(connection.ops.integer_field_range(kind), (0, 2**63 - 1))
