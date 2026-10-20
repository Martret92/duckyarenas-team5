"""A1.2: umbrales, puntos, códigos y versiones exclusivamente sintéticos."""

from dataclasses import FrozenInstanceError, asdict, replace
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from django.test import TestCase as DatabaseTestCase
from django.test.utils import CaptureQueriesContext

from . import target_progression as target
from .progression import LevelDefinition, StageDefinition, calculate_progression
from .target_catalog_validation import validate_target_level_epoch_catalog
from .target_progression import (
    InvalidTargetCatalogError, InvalidTargetXPError, TargetProgressionResult,
    calculate_target_progression,
)


def synthetic_catalog(count=10, points=37):
    levels = [LevelDefinition(n, (n - 1) ** 2 * 13, points) for n in range(1, count + 1)]
    codes = [f"a12-synthetic-epoch-{n}" for n in range(1, 8)]
    epochs = [StageDefinition(code, n, levels[n - 1].minimum_xp) for n, code in enumerate(codes, 1)]
    return validate_target_level_epoch_catalog(
        levels, epochs, ordered_epoch_codes=codes, catalog_version="a12-synthetic-v1",
    )


class TargetProgressionTests(TestCase):
    def setUp(self):
        self.catalog = synthetic_catalog()

    def calculate(self, before, after):
        return calculate_target_progression(before, after, self.catalog)

    def test_zero_initial_state_and_no_initial_transitions(self):
        result = self.calculate(0, 0)
        self.assertEqual((result.level_before, result.level_after), (1, 1))
        self.assertEqual((result.epoch_before_code, result.epoch_after_code),
                         (self.catalog.ordered_epoch_codes[0],) * 2)
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_epoch_codes, ())
        self.assertEqual((result.choice_unlocked_before, result.choice_unlocked_after,
                          result.choice_newly_unlocked), (False, False, False))

    def test_positive_xp_without_threshold_crossing(self):
        result = self.calculate(1, 12)
        self.assertEqual((result.level_before, result.level_after), (1, 1))
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_epoch_codes, ())

    def test_every_level_boundary_before_exact_and_after(self):
        for row in self.catalog.levels[1:]:
            for offset, expected in ((-1, row.level - 1), (0, row.level), (1, row.level)):
                with self.subTest(level=row.level, offset=offset):
                    result = self.calculate(row.minimum_xp + offset, row.minimum_xp + offset)
                    self.assertEqual((result.level_before, result.level_after), (expected, expected))

    def test_every_epoch_boundary_before_exact_and_after(self):
        for row in self.catalog.epochs[1:]:
            for offset, ordinal in ((-1, row.ordinal - 1), (0, row.ordinal), (1, row.ordinal)):
                with self.subTest(ordinal=row.ordinal, offset=offset):
                    result = self.calculate(row.minimum_xp + offset, row.minimum_xp + offset)
                    self.assertEqual(result.epoch_after_code, self.catalog.ordered_epoch_codes[ordinal - 1])
                    self.assertEqual(result.epoch_before_code, result.epoch_after_code)

    def test_single_level_and_corresponding_epoch_crossing(self):
        threshold = self.catalog.levels[3].minimum_xp
        result = self.calculate(threshold - 1, threshold)
        self.assertEqual((result.level_before, result.level_after), (3, 4))
        self.assertEqual(result.crossed_levels, (4,))
        self.assertEqual(result.crossed_epoch_codes, (self.catalog.ordered_epoch_codes[3],))

    def test_many_transitions_ordered_unique_and_initial_excluded(self):
        result = self.calculate(0, self.catalog.levels[-1].minimum_xp)
        self.assertEqual(result.crossed_levels, tuple(range(2, 11)))
        self.assertEqual(result.crossed_epoch_codes, self.catalog.ordered_epoch_codes[1:])
        self.assertEqual(len(set(result.crossed_levels)), len(result.crossed_levels))
        self.assertEqual(len(set(result.crossed_epoch_codes)), len(result.crossed_epoch_codes))

    def test_equal_totals_never_cross_or_newly_unlock(self):
        for xp in (0, 13, self.catalog.levels[6].minimum_xp, self.catalog.levels[7].minimum_xp, 10**80):
            with self.subTest(xp=xp):
                result = self.calculate(xp, xp)
                self.assertEqual(result.crossed_levels, ())
                self.assertEqual(result.crossed_epoch_codes, ())
                self.assertFalse(result.choice_newly_unlocked)
                self.assertEqual(result.choice_unlocked_before, result.choice_unlocked_after)

    def test_level_seven_does_not_unlock(self):
        result = self.calculate(0, self.catalog.levels[6].minimum_xp)
        self.assertEqual(result.level_after, 7)
        self.assertFalse(result.choice_unlocked_after)
        self.assertFalse(result.choice_newly_unlocked)

    def test_just_before_level_eight_not_unlocked(self):
        result = self.calculate(0, self.catalog.levels[7].minimum_xp - 1)
        self.assertEqual(result.level_after, 7)
        self.assertFalse(result.choice_unlocked_after)
        self.assertFalse(result.choice_newly_unlocked)

    def test_exact_level_eight_crossing_unlocks_without_epoch(self):
        threshold = self.catalog.levels[7].minimum_xp
        result = self.calculate(threshold - 1, threshold)
        self.assertEqual((result.level_before, result.level_after), (7, 8))
        self.assertEqual(result.crossed_levels, (8,))
        self.assertEqual(result.crossed_epoch_codes, ())
        self.assertEqual(result.epoch_before_code, self.catalog.ordered_epoch_codes[-1])
        self.assertEqual(result.epoch_after_code, self.catalog.ordered_epoch_codes[-1])
        self.assertEqual((result.choice_unlocked_before, result.choice_unlocked_after,
                          result.choice_newly_unlocked), (False, True, True))

    def test_jump_from_initial_to_eight_has_all_seven_levels_and_six_epochs(self):
        result = self.calculate(0, self.catalog.levels[7].minimum_xp)
        self.assertEqual(result.crossed_levels, (2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(result.crossed_epoch_codes, self.catalog.ordered_epoch_codes[1:])
        self.assertTrue(result.choice_newly_unlocked)

    def test_jump_above_eight_still_unlocks_only_once(self):
        result = self.calculate(0, self.catalog.levels[9].minimum_xp)
        self.assertEqual(result.level_after, 10)
        self.assertTrue(result.choice_newly_unlocked)
        self.assertEqual(result.epoch_after_code, self.catalog.ordered_epoch_codes[-1])
        self.assertEqual(len(result.crossed_epoch_codes), 6)

    def test_already_eight_no_second_unlock(self):
        threshold = self.catalog.levels[7].minimum_xp
        result = self.calculate(threshold, threshold + 1)
        self.assertEqual((result.choice_unlocked_before, result.choice_unlocked_after,
                          result.choice_newly_unlocked), (True, True, False))
        self.assertEqual(result.crossed_levels, ())

    def test_eight_to_nine_only_crosses_level_not_epoch_or_unlock(self):
        result = self.calculate(self.catalog.levels[7].minimum_xp, self.catalog.levels[8].minimum_xp)
        self.assertEqual((result.level_before, result.level_after), (8, 9))
        self.assertEqual(result.crossed_levels, (9,))
        self.assertEqual(result.crossed_epoch_codes, ())
        self.assertFalse(result.choice_newly_unlocked)

    def test_above_last_configured_level_no_functional_xp_limit(self):
        result = self.calculate(10**100, 10**150)
        self.assertEqual((result.level_before, result.level_after), (10, 10))
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_epoch_codes, ())
        self.assertEqual(result.epoch_after_code, self.catalog.ordered_epoch_codes[-1])
        self.assertTrue(result.choice_unlocked_before)
        self.assertFalse(result.choice_newly_unlocked)

    def test_catalog_with_exactly_eight_levels(self):
        catalog = synthetic_catalog(count=8)
        result = calculate_target_progression(0, 10**50, catalog)
        self.assertEqual(result.level_after, 8)
        self.assertEqual(result.epoch_after_code, catalog.ordered_epoch_codes[-1])
        self.assertTrue(result.choice_newly_unlocked)

    def test_invalid_xp_types_and_negative_totals(self):
        for value in (-1, True, False, 1.0, 1.5, "1", None, Decimal("1"), [], {}):
            for before, after in ((value, 10), (0, value)):
                with self.subTest(before=before, after=after), self.assertRaises(InvalidTargetXPError):
                    self.calculate(before, after)

    def test_decreasing_xp_rejected_without_conversion_or_repair(self):
        for before, after in ((1, 0), (100, 99), (10**100, 10**100 - 1)):
            with self.subTest(before=before), self.assertRaises(InvalidTargetXPError):
                self.calculate(before, after)

    def test_missing_or_incompatible_snapshot_rejected(self):
        for catalog in (None, {}, [], object(), "catalog", self.catalog.levels,
                        SimpleNamespace(**asdict(self.catalog))):
            with self.subTest(catalog=type(catalog)), self.assertRaises(InvalidTargetCatalogError):
                calculate_target_progression(0, 13, catalog)

    def test_snapshot_is_consumed_without_revalidating_a11_or_v1(self):
        with patch("apps.ecomotor.target_catalog_validation.validate_target_level_epoch_catalog", side_effect=AssertionError), \
                patch("apps.ecomotor.target_catalog_validation.TargetCatalogSnapshot.__post_init__", side_effect=AssertionError), \
                patch("apps.ecomotor.progression._validate_levels", side_effect=AssertionError), \
                patch("apps.ecomotor.progression._validate_stages", side_effect=AssertionError):
            self.assertEqual(self.calculate(0, 13).level_after, 2)

    def test_version_and_snapshots_are_reflected_exactly(self):
        result = self.calculate(13, 52)
        self.assertEqual(result.catalog_version, self.catalog.catalog_version)
        self.assertEqual((result.xp_before, result.xp_after), (13, 52))

    def test_result_is_frozen_and_collections_are_tuples(self):
        result = self.calculate(0, 52)
        self.assertIsInstance(result, TargetProgressionResult)
        with self.assertRaises(FrozenInstanceError):
            result.xp_after = 999
        with self.assertRaises(TypeError):
            result.crossed_levels[0] = 999
        self.assertIsInstance(result.crossed_epoch_codes, tuple)

    def test_direct_result_construction_defensively_copies_collections(self):
        levels, codes = [2, 3], [self.catalog.ordered_epoch_codes[1]]
        result = replace(self.calculate(0, 52), crossed_levels=levels, crossed_epoch_codes=codes)
        levels.clear()
        codes.clear()
        self.assertEqual(result.crossed_levels, (2, 3))
        self.assertEqual(result.crossed_epoch_codes, (self.catalog.ordered_epoch_codes[1],))

    def test_result_rejects_strings_invalid_elements_and_nested_mutables(self):
        result = self.calculate(0, 0)
        for field, bad_values in (("crossed_levels", ("23", [True], [1.5], [[2]], [0], [-1], {})),
                                  ("crossed_epoch_codes", ("epoch", [3], [["epoch"]], [""], ["  "]))):
            for value in bad_values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    replace(result, **{field: value})

    def test_catalog_unchanged_and_deterministic(self):
        before = asdict(self.catalog)
        expected = self.calculate(0, 1000)
        for _ in range(10):
            self.assertEqual(self.calculate(0, 1000), expected)
        self.assertEqual(asdict(self.catalog), before)

    def test_segment_composition_preserves_all_transitions_and_single_unlock(self):
        cuts = [0, 13, 117, self.catalog.levels[6].minimum_xp,
                self.catalog.levels[7].minimum_xp, self.catalog.levels[8].minimum_xp, 10**60]
        segments = [self.calculate(a, b) for a, b in zip(cuts, cuts[1:])]
        complete = self.calculate(cuts[0], cuts[-1])
        self.assertEqual(tuple(n for segment in segments for n in segment.crossed_levels), complete.crossed_levels)
        self.assertEqual(tuple(code for segment in segments for code in segment.crossed_epoch_codes),
                         complete.crossed_epoch_codes)
        self.assertEqual(sum(segment.choice_newly_unlocked for segment in segments), 1)
        self.assertEqual(segments[0].level_before, complete.level_before)
        self.assertEqual(segments[-1].level_after, complete.level_after)

    def test_exact_segment_cut_does_not_repeat_level_epoch_or_unlock(self):
        for row in self.catalog.levels[1:]:
            with self.subTest(level=row.level):
                first = self.calculate(0, row.minimum_xp)
                second = self.calculate(row.minimum_xp, 10**60)
                self.assertIn(row.level, first.crossed_levels)
                self.assertNotIn(row.level, second.crossed_levels)
                if row.level <= 7:
                    code = self.catalog.ordered_epoch_codes[row.level - 1]
                    self.assertIn(code, first.crossed_epoch_codes)
                    self.assertNotIn(code, second.crossed_epoch_codes)
                if row.level == 8:
                    self.assertTrue(first.choice_newly_unlocked)
                    self.assertFalse(second.choice_newly_unlocked)

    def test_stat_points_do_not_affect_calculation_or_appear_in_result(self):
        expected = self.calculate(0, 1000)
        catalog = synthetic_catalog(points=10**100)
        self.assertEqual(calculate_target_progression(0, 1000, catalog), expected)
        self.assertEqual(calculate_target_progression(0, 1000, synthetic_catalog(points=0)), expected)
        self.assertEqual(set(asdict(expected)), {
            "catalog_version", "xp_before", "xp_after", "level_before", "level_after",
            "epoch_before_code", "epoch_after_code", "crossed_levels", "crossed_epoch_codes",
            "choice_unlocked_before", "choice_unlocked_after", "choice_newly_unlocked",
        })  # Sin puntos, premios, eventos, Ducky elegido ni estadísticas configuradas.

    def test_v1_keeps_independent_thresholds_and_stat_points(self):
        epochs = [replace(row, minimum_xp=(row.ordinal - 1) * 17) for row in self.catalog.epochs]
        before = calculate_progression(0, 102, self.catalog.levels, epochs,
                                       ordered_stage_codes=self.catalog.ordered_epoch_codes)
        self.calculate(0, 102)
        after = calculate_progression(0, 102, self.catalog.levels, epochs,
                                      ordered_stage_codes=self.catalog.ordered_epoch_codes)
        self.assertEqual(before, after)
        self.assertEqual(after.stage_after_code, self.catalog.ordered_epoch_codes[-1])
        self.assertEqual(after.total_stat_points_awarded, 74)

    def test_no_io_during_calculation(self):
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError):
            self.assertEqual(self.calculate(0, 13).level_after, 2)

    def test_module_imports_and_runs_without_django(self):
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from apps.ecomotor.target_catalog_validation import validate_target_level_epoch_catalog; "
            "from apps.ecomotor.progression import LevelDefinition, StageDefinition; "
            "from apps.ecomotor.target_progression import calculate_target_progression; "
            "codes=tuple('synthetic-'+str(i) for i in range(7)); "
            "catalog=validate_target_level_epoch_catalog([LevelDefinition(i+1,i*11,37) for i in range(9)],"
            "[StageDefinition(c,i+1,i*11) for i,c in enumerate(codes)],"
            "ordered_epoch_codes=codes,catalog_version='synthetic'); "
            "result=calculate_target_progression(0,88,catalog); "
            "assert result.level_after==9 and result.choice_newly_unlocked; "
            "assert result.epoch_after_code==codes[-1] and len(result.crossed_epoch_codes)==6; "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules)"
        )
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


class TargetProgressionV1IsolationTests(DatabaseTestCase):
    def test_pure_calculation_does_not_query_or_change_persisted_data(self):
        from django.db import connection
        from apps.users.models import UserProfileEcomotor
        from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent
        from .test_xp_service import create_xp_catalogs, create_xp_profile

        create_xp_catalogs()
        create_xp_profile(username="a12-synthetic-read-only")
        models = (UserProfileEcomotor, CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent)
        before = [list(model.objects.order_by("pk").values()) for model in models]
        catalog = synthetic_catalog()
        with CaptureQueriesContext(connection) as queries:
            self.assertTrue(calculate_target_progression(0, 10**100, catalog).choice_newly_unlocked)
        self.assertEqual(len(queries), 0)
        self.assertEqual([list(model.objects.order_by("pk").values()) for model in models], before)

    def test_s3_and_readiness_do_not_call_target_calculation(self):
        from . import initialization_config
        from .configuration_checks import ReadinessStatus, check_ecomotor_readiness
        from .models import CharacterStats
        from .test_runtime_configuration import candidate_data
        from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
        from .xp_service import grant_historical_xp

        create_xp_catalogs()
        profile = create_xp_profile(username="a12-synthetic-v1")
        configuration = initialization_config.InitializationConfiguration(**candidate_data())
        with patch.object(target, "calculate_target_progression", side_effect=AssertionError), \
                patch.object(target, "TargetProgressionResult", side_effect=AssertionError), \
                patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
            result = grant_historical_xp(profile, 102, "a12-synthetic-v1-operation")
            readiness = check_ecomotor_readiness(configuration=configuration)
        self.assertEqual(result.stat_points_awarded, 7)
        self.assertEqual(CharacterStats.objects.get(profile=profile).available_points, 14)
        self.assertEqual(readiness.status, ReadinessStatus.TECHNICALLY_READY)
