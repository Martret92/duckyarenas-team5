"""A2.1: importes, códigos y versiones sintéticos; ninguna configuración oficial."""

from dataclasses import FrozenInstanceError, asdict, fields, replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.test import TestCase as DatabaseTestCase
from django.test.utils import CaptureQueriesContext

from . import target_progression, target_xp_plan as planner
from .target_xp_plan import (
    InvalidTargetCatalogError, InvalidTargetXPAmountError, InvalidTargetXPError,
    TargetXPPlan, plan_target_xp_grant,
)
from .test_target_progression import synthetic_catalog


class TargetXPPlanTests(TestCase):
    def setUp(self):
        self.catalog = synthetic_catalog()

    def plan(self, before=0, amount=1):
        return plan_target_xp_grant(before, amount, self.catalog)

    def test_minimum_positive_amount_from_zero(self):
        plan = self.plan()
        self.assertEqual(plan.amount, 1)
        self.assertEqual((plan.progression.xp_before, plan.progression.xp_after), (0, 1))
        self.assertEqual((plan.progression.level_before, plan.progression.level_after), (1, 1))
        self.assertEqual(plan.progression.epoch_after_code, self.catalog.ordered_epoch_codes[0])
        self.assertEqual(plan.progression.crossed_levels, ())
        self.assertEqual(plan.progression.crossed_epoch_codes, ())

    def test_increment_without_level_or_epoch_change(self):
        change = self.plan(1, 2).progression
        self.assertEqual((change.xp_before, change.xp_after), (1, 3))
        self.assertEqual(change.level_before, change.level_after)
        self.assertEqual(change.epoch_before_code, change.epoch_after_code)
        self.assertEqual(change.crossed_levels, ())
        self.assertEqual(change.crossed_epoch_codes, ())

    def test_exact_level_and_epoch_thresholds(self):
        for row in self.catalog.levels[1:]:
            with self.subTest(level=row.level):
                change = self.plan(row.minimum_xp - 1, 1).progression
                self.assertEqual(change.level_after, row.level)
                self.assertEqual(change.crossed_levels, (row.level,))
                expected = (self.catalog.ordered_epoch_codes[row.level - 1],) if row.level <= 7 else ()
                self.assertEqual(change.crossed_epoch_codes, expected)

    def test_jump_from_initial_to_eight_preserves_all_crossings(self):
        amount = self.catalog.levels[7].minimum_xp
        plan = self.plan(0, amount)
        self.assertEqual(plan.amount, amount)
        self.assertEqual(plan.progression.crossed_levels, (2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(plan.progression.crossed_epoch_codes, self.catalog.ordered_epoch_codes[1:])
        self.assertTrue(plan.progression.choice_newly_unlocked)
        self.assertFalse(plan.progression.choice_unlocked_before)
        self.assertTrue(plan.progression.choice_unlocked_after)

    def test_exact_level_eight_new_unlock_without_eighth_epoch(self):
        threshold = self.catalog.levels[7].minimum_xp
        change = self.plan(threshold - 1, 1).progression
        self.assertEqual((change.level_before, change.level_after), (7, 8))
        self.assertTrue(change.choice_newly_unlocked)
        self.assertEqual(change.crossed_epoch_codes, ())
        self.assertEqual(change.epoch_after_code, self.catalog.ordered_epoch_codes[-1])

    def test_already_eight_and_later_levels_do_not_repeat_unlock_or_epochs(self):
        before = self.catalog.levels[7].minimum_xp
        after = self.catalog.levels[9].minimum_xp
        change = self.plan(before, after - before).progression
        self.assertEqual((change.level_before, change.level_after), (8, 10))
        self.assertEqual(change.crossed_levels, (9, 10))
        self.assertEqual(change.crossed_epoch_codes, ())
        self.assertTrue(change.choice_unlocked_before)
        self.assertTrue(change.choice_unlocked_after)
        self.assertFalse(change.choice_newly_unlocked)
        self.assertEqual(change.epoch_before_code, self.catalog.ordered_epoch_codes[-1])
        self.assertEqual(change.epoch_after_code, self.catalog.ordered_epoch_codes[-1])

    def test_large_totals_without_backend_or_functional_limits(self):
        plan = self.plan(10**100, 10**150)
        self.assertEqual(plan.amount, 10**150)
        self.assertEqual(plan.progression.xp_after, 10**100 + 10**150)
        self.assertEqual(plan.progression.level_before, plan.progression.level_after)

    def test_amount_equals_xp_difference_for_every_returned_plan(self):
        for before, amount in ((0, 1), (0, 13), (12, 1), (13, 624), (637, 1000), (10**80, 10**90)):
            with self.subTest(before=before, amount=amount):
                plan = self.plan(before, amount)
                self.assertEqual(plan.amount, plan.progression.xp_after - plan.progression.xp_before)
                self.assertEqual(plan.progression.catalog_version, self.catalog.catalog_version)

    def test_invalid_amount_separate_from_xp_and_catalog_errors(self):
        for amount in (0, -1, True, False, 1.0, 1.5, "1", None, Decimal("1"), Fraction(1, 1), [], {}):
            with self.subTest(amount=amount), self.assertRaises(InvalidTargetXPAmountError):
                self.plan(0, amount)

    def test_invalid_before_without_implicit_conversion(self):
        for before in (-1, True, False, 0.0, "0", None, Decimal("0"), Fraction(0, 1), [], {}):
            with self.subTest(before=before), self.assertRaises(InvalidTargetXPError):
                self.plan(before, 1)

    def test_absent_mapping_or_incompatible_catalog(self):
        for catalog in (None, asdict(self.catalog), SimpleNamespace(**asdict(self.catalog)),
                        "a2-synthetic-version", [], object()):
            with self.subTest(catalog=type(catalog)), self.assertRaises(InvalidTargetCatalogError):
                plan_target_xp_grant(0, 1, catalog)

    def test_inputs_validated_before_delegation(self):
        with patch.object(target_progression, "calculate_target_progression", side_effect=AssertionError):
            with self.assertRaises(InvalidTargetXPError):
                self.plan(-1, 1)
            with self.assertRaises(InvalidTargetXPAmountError):
                self.plan(0, True)
            with self.assertRaises(InvalidTargetCatalogError):
                plan_target_xp_grant(0, 1, {})

    def test_delegates_once_to_a12_without_revalidating_a11_or_calling_v1(self):
        original = target_progression.calculate_target_progression
        with patch.object(target_progression, "calculate_target_progression", wraps=original) as calculate, \
                patch("apps.ecomotor.target_catalog_validation.validate_target_level_epoch_catalog", side_effect=AssertionError), \
                patch("apps.ecomotor.target_catalog_validation.TargetCatalogSnapshot.__post_init__", side_effect=AssertionError), \
                patch("apps.ecomotor.progression.calculate_progression", side_effect=AssertionError), \
                patch("apps.ecomotor.progression._validate_levels", side_effect=AssertionError):
            plan = self.plan(13, 39)
        calculate.assert_called_once_with(13, 52, self.catalog)
        self.assertEqual(plan.progression, original(13, 52, self.catalog))

    def test_retains_exact_a12_result_without_reconstruction(self):
        expected = target_progression.calculate_target_progression(0, 13, self.catalog)
        with patch.object(target_progression, "calculate_target_progression", return_value=expected):
            plan = self.plan(0, 13)
        self.assertIs(plan.progression, expected)

    def test_does_not_hide_errors_raised_by_calculation(self):
        for error in (InvalidTargetXPError("synthetic"), InvalidTargetCatalogError("synthetic"),
                      RuntimeError("synthetic-programming-error")):
            with self.subTest(error=type(error)), \
                    patch.object(target_progression, "calculate_target_progression", side_effect=error):
                with self.assertRaises(type(error)) as caught:
                    self.plan()
                self.assertIs(caught.exception, error)

    def test_plan_nested_result_and_transition_collections_immutable(self):
        plan = self.plan(0, self.catalog.levels[7].minimum_xp)
        with self.assertRaises(FrozenInstanceError):
            plan.amount = 999
        with self.assertRaises(FrozenInstanceError):
            plan.progression.xp_after = 999
        self.assertIsInstance(plan.progression.crossed_levels, tuple)
        self.assertIsInstance(plan.progression.crossed_epoch_codes, tuple)
        with self.assertRaises(TypeError):
            plan.progression.crossed_levels[0] = 99
        self.assertFalse(hasattr(plan, "__dict__"))

    def test_direct_plan_construction_requires_positive_amount_and_immutable_result(self):
        result = self.plan().progression
        for amount in (0, True, "1", -1):
            with self.subTest(amount=amount), self.assertRaises(InvalidTargetXPAmountError):
                TargetXPPlan(amount, result)
        for value in (None, [], {}, asdict(result)):
            with self.subTest(value=type(value)), self.assertRaises(TypeError):
                TargetXPPlan(1, value)

    def test_determinism_and_catalog_unchanged(self):
        before = asdict(self.catalog)
        first = self.plan(0, 900)
        for _ in range(10):
            self.assertEqual(self.plan(0, 900), first)
        self.assertEqual(asdict(self.catalog), before)

    def test_inherited_nonzero_stat_points_are_irrelevant(self):
        expected = self.plan(0, 900)
        for points in (0, 10**90):
            catalog = synthetic_catalog(points=points)
            self.assertEqual(plan_target_xp_grant(0, 900, catalog), expected)

    def test_only_amount_and_progression_no_identity_rewards_or_stats_balance(self):
        plan = self.plan(0, 900)
        self.assertEqual([field.name for field in fields(plan)], ["amount", "progression"])
        forbidden = {"profile_id", "user_id", "operation_key", "replayed", "xp_event_id",
                     "stat_points_awarded", "available_points_after", "writer", "applied"}
        self.assertTrue(forbidden.isdisjoint(asdict(plan)))
        self.assertTrue(forbidden.isdisjoint(asdict(plan.progression)))

    def test_version_text_is_preserved_but_does_not_select_a_writer(self):
        first = self.plan(0, 900)
        for version in ("a2-synthetic-old", "a2-synthetic-new", " a2-synthetic-opaque "):
            catalog = replace(self.catalog, catalog_version=version)
            plan = plan_target_xp_grant(0, 900, catalog)
            self.assertEqual(plan.progression.catalog_version, version)
            self.assertEqual(replace(plan.progression, catalog_version=first.progression.catalog_version),
                             first.progression)

    def test_no_file_network_database_or_clock_access(self):
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError), \
                patch("time.time", side_effect=AssertionError):
            self.assertEqual(self.plan().progression.xp_after, 1)

    def test_import_and_execution_without_django_in_isolated_interpreter(self):
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from apps.ecomotor.target_catalog_validation import validate_target_level_epoch_catalog; "
            "from apps.ecomotor.progression import LevelDefinition, StageDefinition; "
            "from apps.ecomotor.target_xp_plan import plan_target_xp_grant; "
            "codes=tuple('synthetic-'+str(i) for i in range(7)); "
            "catalog=validate_target_level_epoch_catalog([LevelDefinition(i+1,i*11,37) for i in range(9)],"
            "[StageDefinition(c,i+1,i*11) for i,c in enumerate(codes)],"
            "ordered_epoch_codes=codes,catalog_version='a2-synthetic'); "
            "plan=plan_target_xp_grant(0,88,catalog); "
            "assert plan.amount==88 and plan.progression.level_after==9; "
            "assert plan.progression.choice_newly_unlocked and len(plan.progression.crossed_epoch_codes)==6; "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules)"
        )
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


class TargetXPPlanV1IsolationTests(DatabaseTestCase):
    def setUp(self):
        from . import initialization_config
        from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
        create_xp_catalogs()
        self.profile = create_xp_profile(username="a2-synthetic-v1")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)

    def snapshot(self):
        from apps.users.models import UserProfileEcomotor
        from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent
        return [list(model.objects.order_by("pk").values()) for model in (
            UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent, LevelThreshold, EvolutionStage,
        )]

    def test_plan_and_direct_construction_do_not_query_or_change_persisted_state(self):
        from django.db import connection
        catalog = synthetic_catalog()
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            plan = plan_target_xp_grant(0, 900, catalog)
            self.assertEqual(TargetXPPlan(plan.amount, plan.progression), plan)
        self.assertEqual(len(queries), 0)
        self.assertEqual(self.snapshot(), before)

    def test_s3_keeps_points_replay_and_conflicts_without_calling_planner(self):
        from .models import CharacterStats, XPEvent
        from .xp_service import IdempotencyConflictError, grant_historical_xp
        with patch.object(planner, "plan_target_xp_grant", side_effect=AssertionError), \
                patch.object(planner, "TargetXPPlan", side_effect=AssertionError):
            first = grant_historical_xp(self.profile, 102, "a2-synthetic-v1-grant")
            before = self.snapshot()
            replay = grant_historical_xp(self.profile, 102, "a2-synthetic-v1-grant")
            with self.assertRaises(IdempotencyConflictError):
                grant_historical_xp(self.profile, 103, "a2-synthetic-v1-grant")
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(first.xp_event_id, replay.xp_event_id)
        self.assertEqual(first.stat_points_awarded, 7)
        self.assertEqual(first.available_points_after, 14)
        self.assertIsNone(replay.stat_points_awarded)
        self.assertEqual(CharacterStats.objects.get(profile=self.profile).available_points, 14)
        self.assertEqual(XPEvent.objects.filter(profile=self.profile).count(), 1)
        self.assertEqual(self.snapshot(), before)

    def test_v1_configuration_does_not_invoke_planner(self):
        from .configuration_checks import ReadinessStatus, check_ecomotor_readiness
        from .initialization_config import InitializationConfiguration
        from .test_runtime_configuration import candidate_data
        with patch.object(planner, "plan_target_xp_grant", side_effect=AssertionError):
            readiness = check_ecomotor_readiness(configuration=InitializationConfiguration(**candidate_data()))
        self.assertEqual(readiness.status, ReadinessStatus.TECHNICALLY_READY)
