"""Pruebas S1 sin base de datos; todas las cantidades y códigos son ficticios."""

from dataclasses import FrozenInstanceError, replace
import subprocess
import sys

from django.test import SimpleTestCase

from . import progression
from .progression import (
    InvalidCatalogError, InvalidXPError, LevelDefinition, StageDefinition,
    calculate_progression, resolve_level, resolve_stage,
)


class ProgressionTests(SimpleTestCase):
    def setUp(self):
        self.levels = [
            LevelDefinition(1, 0, 99), LevelDefinition(2, 11, 2),
            LevelDefinition(3, 23, 0), LevelDefinition(4, 47, 5),
        ]
        self.codes = [f"test-stage-{ordinal}" for ordinal in range(1, 8)]
        self.stages = [
            StageDefinition(code, ordinal, (ordinal - 1) * 17)
            for ordinal, code in enumerate(self.codes, 1)
        ]

    def calculate(self, before, after, levels=None, stages=None, codes=None):
        return calculate_progression(
            before, after, self.levels if levels is None else levels,
            self.stages if stages is None else stages,
            ordered_stage_codes=self.codes if codes is None else codes,
        )

    def test_zero_resolves_initial_level_and_stage(self):
        self.assertEqual(resolve_level(0, self.levels), 1)
        self.assertEqual(resolve_stage(0, self.stages, ordered_stage_codes=self.codes), self.codes[0])
        result = self.calculate(0, 0)
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_stages, ())
        self.assertEqual(result.total_stat_points_awarded, 0)

    def test_level_boundaries_before_exact_and_after(self):
        for index, definition in enumerate(self.levels[1:], 1):
            for offset, expected in [(-1, self.levels[index - 1].level), (0, definition.level), (1, definition.level)]:
                with self.subTest(level=definition.level, offset=offset):
                    self.assertEqual(resolve_level(definition.minimum_xp + offset, self.levels), expected)

    def test_stage_boundaries_before_exact_and_after(self):
        for index, definition in enumerate(self.stages[1:], 1):
            for offset, expected in [(-1, self.codes[index - 1]), (0, definition.code), (1, definition.code)]:
                with self.subTest(ordinal=definition.ordinal, offset=offset):
                    self.assertEqual(resolve_stage(definition.minimum_xp + offset, self.stages, ordered_stage_codes=self.codes), expected)

    def test_above_last_threshold_keeps_last_level_and_stage(self):
        result = self.calculate(103, 10**100)
        self.assertEqual((result.level_before, result.level_after), (4, 4))
        self.assertEqual((result.stage_before_code, result.stage_after_code), (self.codes[-1], self.codes[-1]))
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_stages, ())

    def test_single_level_crossing(self):
        result = self.calculate(10, 11)
        self.assertEqual((result.xp_before, result.xp_after), (10, 11))
        self.assertEqual((result.level_before, result.level_after), (1, 2))
        self.assertEqual(result.crossed_levels, (self.levels[1],))
        self.assertEqual(result.total_stat_points_awarded, 2)

    def test_multiple_levels_sum_each_award_excluding_initial_level(self):
        result = self.calculate(0, 47)
        self.assertEqual(result.crossed_levels, tuple(self.levels[1:]))
        self.assertEqual(result.total_stat_points_awarded, 7)

    def test_multiple_stage_crossings_exclude_initial_stage(self):
        result = self.calculate(17, 85)
        self.assertEqual(result.stage_before_code, self.codes[1])
        self.assertEqual(result.stage_after_code, self.codes[5])
        self.assertEqual(result.crossed_stages, tuple(self.stages[2:6]))

    def test_combined_level_and_stage_crossings(self):
        result = self.calculate(11, 51)
        self.assertEqual((result.level_before, result.level_after), (2, 4))
        self.assertEqual(result.crossed_levels, tuple(self.levels[2:]))
        self.assertEqual(result.crossed_stages, tuple(self.stages[1:4]))
        self.assertEqual(result.total_stat_points_awarded, 5)

    def test_equal_xp_has_no_transitions_or_points(self):
        for xp in [0, 11, 17, 51, 102, 999]:
            with self.subTest(xp=xp):
                result = self.calculate(xp, xp)
                self.assertEqual(result.level_before, result.level_after)
                self.assertEqual(result.stage_before_code, result.stage_after_code)
                self.assertEqual(result.crossed_levels, ())
                self.assertEqual(result.crossed_stages, ())
                self.assertEqual(result.total_stat_points_awarded, 0)

    def test_increase_without_crossing_threshold_has_no_award(self):
        result = self.calculate(2, 10)
        self.assertEqual(result.crossed_levels, ())
        self.assertEqual(result.crossed_stages, ())
        self.assertEqual(result.total_stat_points_awarded, 0)

    def test_invalid_xp_types_and_negative_values_rejected_by_all_interfaces(self):
        for xp in [-1, True, False, 1.0, "1", None]:
            with self.subTest(xp=xp):
                with self.assertRaises(InvalidXPError):
                    resolve_level(xp, self.levels)
                with self.assertRaises(InvalidXPError):
                    resolve_stage(xp, self.stages, ordered_stage_codes=self.codes)
                with self.assertRaises(InvalidXPError):
                    self.calculate(xp, 23)
                with self.assertRaises(InvalidXPError):
                    self.calculate(0, xp)

    def test_decreasing_xp_rejected(self):
        with self.assertRaises(InvalidXPError):
            self.calculate(24, 23)

    def test_invalid_level_catalog_shapes(self):
        for levels in [[], None, 1, "bad", [object()], self.levels[1:],
                       [self.levels[0], self.levels[2]], [self.levels[0]] * 2]:
            with self.subTest(levels=levels):
                with self.assertRaises(InvalidCatalogError):
                    resolve_level(0, levels)
                with self.assertRaises(InvalidCatalogError):
                    self.calculate(0, 0, levels=levels if levels is not None else [None])

    def test_invalid_level_fields(self):
        cases = [("level", value) for value in [0, -1, True, 1.0, "1", None]]
        cases += [("minimum_xp", value) for value in [-1, True, 0.0, "0", None, 1]]
        cases += [("stat_points_awarded", value) for value in [-1, True, 0.0, "0", None]]
        for field, value in cases:
            levels = self.levels.copy()
            levels[0] = replace(levels[0], **{field: value})
            with self.subTest(field=field, value=value), self.assertRaises(InvalidCatalogError):
                resolve_level(0, levels)

    def test_level_thresholds_must_increase_strictly(self):
        for xp in [11, 10]:
            levels = self.levels.copy()
            levels[2] = replace(levels[2], minimum_xp=xp)
            with self.subTest(xp=xp), self.assertRaises(InvalidCatalogError):
                resolve_level(0, levels)

    def test_single_level_catalog_is_valid(self):
        self.assertEqual(resolve_level(999, self.levels[:1]), 1)
        self.assertEqual(self.calculate(0, 99, levels=self.levels[:1]).total_stat_points_awarded, 0)

    def test_incomplete_or_invalid_stage_catalog_shapes(self):
        for stages in [[], None, 1, "bad", [object()] * 7, self.stages[:6],
                       self.stages + [self.stages[-1]], [self.stages[0]] * 7]:
            with self.subTest(stages=stages), self.assertRaises(InvalidCatalogError):
                resolve_stage(0, stages, ordered_stage_codes=self.codes)

    def test_invalid_stage_fields(self):
        cases = [("ordinal", value) for value in [0, 8, -1, True, 1.0, "1", None]]
        cases += [("minimum_xp", value) for value in [-1, True, 0.0, "0", None, 1]]
        cases += [("code", value) for value in ["", "x" * 33, True, 1, None, "wrong-code"]]
        for field, value in cases:
            stages = self.stages.copy()
            stages[0] = replace(stages[0], **{field: value})
            with self.subTest(field=field, value=value), self.assertRaises(InvalidCatalogError):
                resolve_stage(0, stages, ordered_stage_codes=self.codes)

    def test_duplicate_ordinals_and_codes_rejected(self):
        for fields in [dict(ordinal=1), dict(code=self.codes[0])]:
            stages = self.stages.copy()
            stages[1] = replace(stages[1], **fields)
            with self.subTest(fields=fields), self.assertRaises(InvalidCatalogError):
                self.calculate(0, 0, stages=stages)

    def test_swapped_functional_codes_rejected(self):
        codes = self.codes.copy()
        codes[0], codes[1] = codes[1], codes[0]
        with self.assertRaises(InvalidCatalogError):
            self.calculate(0, 0, codes=codes)

    def test_stage_thresholds_must_increase_strictly(self):
        for xp in [17, 16]:
            stages = self.stages.copy()
            stages[2] = replace(stages[2], minimum_xp=xp)
            with self.subTest(xp=xp), self.assertRaises(InvalidCatalogError):
                self.calculate(0, 0, stages=stages)

    def test_invalid_code_correspondence(self):
        cases = [[], None, 1, "abcdefg", self.codes[:6], self.codes + ["extra"], [self.codes[0]] * 7]
        cases += [[value] + self.codes[1:] for value in ["", "x" * 33, None, True, 7]]
        for codes in cases:
            with self.subTest(codes=codes), self.assertRaises(InvalidCatalogError):
                resolve_stage(0, self.stages, ordered_stage_codes=codes)

    def test_code_of_model_maximum_length_is_valid(self):
        codes = self.codes.copy()
        codes[0] = "x" * 32
        stages = self.stages.copy()
        stages[0] = replace(stages[0], code=codes[0])
        self.assertEqual(resolve_stage(0, stages, ordered_stage_codes=codes), codes[0])

    def test_unordered_inputs_remain_unchanged_and_transitions_are_sorted(self):
        levels = list(reversed(self.levels))
        stages = list(reversed(self.stages))
        original = (levels.copy(), stages.copy(), self.codes.copy())
        self.assertEqual(resolve_level(47, levels), 4)
        self.assertEqual(resolve_stage(102, stages, ordered_stage_codes=self.codes), self.codes[-1])
        result = self.calculate(0, 102, levels=levels, stages=stages)
        self.assertEqual(result.crossed_levels, tuple(self.levels[1:]))
        self.assertEqual(result.crossed_stages, tuple(self.stages[1:]))
        self.assertEqual((levels, stages, self.codes), original)
        levels.clear()
        stages.clear()
        self.assertEqual(result.crossed_levels, tuple(self.levels[1:]))
        self.assertEqual(result.crossed_stages, tuple(self.stages[1:]))

    def test_definitions_and_results_are_frozen(self):
        result = self.calculate(0, 102)
        for instance, field, value in [(self.levels[0], "level", 2),
                                       (self.stages[0], "code", "changed"),
                                       (result, "xp_after", 0),
                                       (result.crossed_levels[0], "stat_points_awarded", 999)]:
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(instance, field, value)
        self.assertIsInstance(result.crossed_levels, tuple)
        self.assertIsInstance(result.crossed_stages, tuple)

    def test_progression_composes_across_consecutive_segments(self):
        complete = self.calculate(0, 102)
        segments = [self.calculate(0, 23), self.calculate(23, 51), self.calculate(51, 102)]
        levels = tuple(level for segment in segments for level in segment.crossed_levels)
        stages = tuple(stage for segment in segments for stage in segment.crossed_stages)

        self.assertEqual(levels, complete.crossed_levels)
        self.assertEqual(stages, complete.crossed_stages)
        self.assertEqual(levels, tuple(sorted(levels, key=lambda level: level.level)))
        self.assertEqual(stages, tuple(sorted(stages, key=lambda stage: stage.ordinal)))
        self.assertEqual(
            sum(segment.total_stat_points_awarded for segment in segments),
            complete.total_stat_points_awarded,
        )
        self.assertEqual(
            (segments[0].xp_before, segments[0].level_before, segments[0].stage_before_code),
            (complete.xp_before, complete.level_before, complete.stage_before_code),
        )
        self.assertEqual(
            (segments[-1].xp_after, segments[-1].level_after, segments[-1].stage_after_code),
            (complete.xp_after, complete.level_after, complete.stage_after_code),
        )
        for previous, following in zip(segments, segments[1:]):
            with self.subTest(cut=previous.xp_after):
                self.assertEqual(
                    (previous.xp_after, previous.level_after, previous.stage_after_code),
                    (following.xp_before, following.level_before, following.stage_before_code),
                )

    def test_exact_threshold_segments_and_zero_increment_do_not_repeat_awards(self):
        cuts = [0, 11, 17, 17, 47, 51, 102]
        segments = [self.calculate(before, after) for before, after in zip(cuts, cuts[1:])]
        complete = self.calculate(0, 102)

        self.assertEqual(segments[0].crossed_levels, (self.levels[1],))
        self.assertEqual(segments[0].total_stat_points_awarded, self.levels[1].stat_points_awarded)
        self.assertEqual(segments[1].crossed_stages, (self.stages[1],))
        self.assertEqual(segments[2].crossed_levels, ())
        self.assertEqual(segments[2].crossed_stages, ())
        self.assertEqual(segments[2].total_stat_points_awarded, 0)
        # Continuar desde 17 no repite la etapa alcanzada; los cortes posteriores
        # tampoco repiten el nivel de 47 ni la etapa de 51.
        self.assertEqual(segments[3].crossed_levels, tuple(self.levels[2:]))
        self.assertEqual(segments[3].crossed_stages, (self.stages[2],))
        self.assertEqual(segments[4].crossed_levels, ())
        self.assertEqual(segments[4].crossed_stages, (self.stages[3],))
        self.assertEqual(segments[5].crossed_levels, ())
        self.assertEqual(segments[5].crossed_stages, tuple(self.stages[4:]))

        levels = tuple(level for segment in segments for level in segment.crossed_levels)
        stages = tuple(stage for segment in segments for stage in segment.crossed_stages)
        self.assertEqual(levels, complete.crossed_levels)
        self.assertEqual(stages, complete.crossed_stages)
        self.assertEqual(levels, tuple(self.levels[1:]))
        self.assertEqual(stages, tuple(self.stages[1:]))
        self.assertEqual(
            sum(segment.total_stat_points_awarded for segment in segments),
            complete.total_stat_points_awarded,
        )

    def test_module_runs_in_isolated_python_without_importing_django(self):
        code = (
            "import runpy, sys; module = runpy.run_path(sys.argv[1]); "
            "level = module['LevelDefinition'](1, 0, 0); "
            "assert module['resolve_level'](0, [level]) == 1; "
            "assert not any(name == 'django' or name.startswith('django.') for name in sys.modules)"
        )
        completed = subprocess.run(
            [sys.executable, "-I", "-c", code, progression.__file__],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
