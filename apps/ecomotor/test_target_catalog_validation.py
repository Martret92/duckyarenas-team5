"""A1.1: todos los códigos, versiones, XP y puntos son exclusivamente sintéticos."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
from unittest import TestCase
from unittest.mock import patch

from django.test import TestCase as DatabaseTestCase

from . import target_catalog_validation as target
from .progression import LevelDefinition, StageDefinition, calculate_progression
from .target_catalog_validation import (
    InvalidTargetCatalogError, TargetCatalogSnapshot, validate_target_level_epoch_catalog,
)


def synthetic_catalogs(count=8):
    codes = [f"a11-synthetic-epoch-{n}" for n in range(1, 8)]
    levels = [LevelDefinition(n, (n - 1) ** 2 * 13, n % 3) for n in range(1, count + 1)]
    epochs = [StageDefinition(code, n, levels[n - 1].minimum_xp) for n, code in enumerate(codes, 1)]
    return levels, epochs, codes


class TargetCatalogTests(TestCase):
    def setUp(self):
        self.levels, self.epochs, self.codes = synthetic_catalogs()

    def validate(self, **changes):
        return validate_target_level_epoch_catalog(**(dict(
            levels=self.levels, epochs=self.epochs, ordered_epoch_codes=self.codes,
            catalog_version="a11-synthetic-v1",
        ) | changes))

    def test_complete_correspondence_and_version(self):
        snapshot = self.validate()
        self.assertIsInstance(snapshot, TargetCatalogSnapshot)
        self.assertEqual(snapshot.catalog_version, "a11-synthetic-v1")
        self.assertEqual(snapshot.levels, tuple(self.levels))
        self.assertEqual(snapshot.epochs, tuple(self.epochs))
        self.assertEqual(snapshot.ordered_epoch_codes, tuple(self.codes))
        self.assertEqual([row.minimum_xp for row in snapshot.levels[:7]],
                         [row.minimum_xp for row in snapshot.epochs])

    def test_level_eight_has_own_threshold_without_eighth_epoch(self):
        snapshot = self.validate()
        self.assertEqual(snapshot.levels[-1].level, 8)
        self.assertGreater(snapshot.levels[7].minimum_xp, snapshot.epochs[-1].minimum_xp)
        self.assertEqual(len(snapshot.epochs), 7)

    def test_levels_after_eight_are_allowed(self):
        levels, epochs, codes = synthetic_catalogs(12)
        snapshot = self.validate(levels=levels, epochs=epochs, ordered_epoch_codes=codes)
        self.assertEqual(snapshot.levels[-1].level, 12)
        self.assertEqual(len(snapshot.epochs), 7)

    def test_unordered_inputs_sorted_without_changing_originals(self):
        levels, epochs = self.levels[::-1], self.epochs[3:] + self.epochs[:3]
        before = (levels[:], epochs[:], self.codes[:])
        snapshot = self.validate(levels=levels, epochs=epochs)
        self.assertEqual(snapshot, self.validate())
        self.assertEqual((levels, epochs, self.codes), before)

    def test_unordered_sets_of_definitions_can_be_sorted_by_identity(self):
        self.assertEqual(self.validate(levels=set(self.levels), epochs=set(self.epochs)), self.validate())

    def test_explicit_codes_are_preserved_without_names_or_normalization(self):
        codes = [f" a11-synthetic-CODE-{n} " for n in range(1, 8)]
        epochs = [replace(row, code=code) for row, code in zip(self.epochs, codes)]
        snapshot = self.validate(epochs=epochs, ordered_epoch_codes=codes,
                                 catalog_version=" a11-synthetic-version ")
        self.assertEqual(snapshot.ordered_epoch_codes, tuple(codes))
        self.assertEqual(snapshot.catalog_version, " a11-synthetic-version ")

    def test_frozen_snapshot_and_rows(self):
        snapshot = self.validate()
        for obj, name, value in ((snapshot, "catalog_version", "other"),
                                 (snapshot.levels[0], "minimum_xp", 999),
                                 (snapshot.epochs[0], "code", "other")):
            with self.subTest(name=name), self.assertRaises(FrozenInstanceError):
                setattr(obj, name, value)
        with self.assertRaises(TypeError):
            snapshot.levels[0] = self.levels[1]

    def test_defensive_copies_of_collections_and_rows(self):
        snapshot = self.validate()
        self.assertIsNot(snapshot.levels[0], self.levels[0])
        self.assertIsNot(snapshot.epochs[0], self.epochs[0])
        self.levels.clear()
        self.epochs.clear()
        self.codes.clear()
        self.assertEqual(len(snapshot.levels), 8)
        self.assertEqual(len(snapshot.epochs), 7)
        self.assertEqual(len(snapshot.ordered_epoch_codes), 7)

    def test_direct_snapshot_construction_also_validates_and_copies(self):
        snapshot = TargetCatalogSnapshot(self.levels, self.epochs, self.codes, "a11-synthetic-v1")
        self.assertEqual(snapshot, self.validate())
        self.codes.clear()
        self.assertEqual(len(snapshot.ordered_epoch_codes), 7)
        with self.assertRaises(InvalidTargetCatalogError):
            TargetCatalogSnapshot([], [], [], "a11-synthetic-v1")

    def test_deterministic_with_same_data_and_different_input_order(self):
        expected = self.validate()
        for _ in range(5):
            self.assertEqual(self.validate(), expected)
            self.assertEqual(self.validate(levels=self.levels[::-1], epochs=self.epochs[::-1]), expected)

    def test_nonzero_points_are_preserved_not_removed_by_target_validator(self):
        levels = [replace(row, stat_points_awarded=19) for row in self.levels]
        self.assertTrue(all(row.stat_points_awarded == 19 for row in self.validate(levels=levels).levels))

    def test_no_invented_orm_limits_on_xp_or_points(self):
        levels = [LevelDefinition(n, (n - 1) * 10**100, 10**90) for n in range(1, 9)]
        epochs = [replace(row, minimum_xp=levels[n].minimum_xp) for n, row in enumerate(self.epochs)]
        self.assertEqual(self.validate(levels=levels, epochs=epochs).levels[-1].stat_points_awarded, 10**90)

    def test_missing_level_eight(self):
        with self.assertRaises(InvalidTargetCatalogError):
            self.validate(levels=self.levels[:7])

    def test_empty_levels_or_epochs(self):
        for field in ("levels", "epochs", "ordered_epoch_codes"):
            with self.subTest(field=field), self.assertRaises(InvalidTargetCatalogError):
                self.validate(**{field: []})

    def test_missing_earlier_levels_even_with_later_levels(self):
        levels, _, _ = synthetic_catalogs(9)
        for missing in range(1, 8):
            with self.subTest(missing=missing), self.assertRaises(InvalidTargetCatalogError):
                self.validate(levels=[row for row in levels if row.level != missing])

    def test_duplicate_levels_or_gaps(self):
        for replacement in (3, 10):
            levels = self.levels[:]
            levels[3] = replace(levels[3], level=replacement)
            with self.subTest(replacement=replacement), self.assertRaises(InvalidTargetCatalogError):
                self.validate(levels=levels)

    def test_nonincreasing_level_thresholds_including_level_eight(self):
        for index in range(1, 8):
            for xp in (self.levels[index - 1].minimum_xp, 0):
                levels = self.levels[:]
                levels[index] = replace(levels[index], minimum_xp=xp)
                with self.subTest(index=index, xp=xp), self.assertRaises(InvalidTargetCatalogError):
                    self.validate(levels=levels)

    def test_incomplete_epochs_and_eighth_epoch(self):
        for epochs in (self.epochs[:-1], self.epochs + [StageDefinition("a11-extra", 8, 9999)]):
            with self.subTest(count=len(epochs)), self.assertRaises(InvalidTargetCatalogError):
                self.validate(epochs=epochs)

    def test_duplicate_and_invalid_epoch_ordinals(self):
        for ordinal in (0, 8, 2, -1, True, 1.5, "3"):
            epochs = self.epochs[:]
            epochs[2] = replace(epochs[2], ordinal=ordinal)
            with self.subTest(ordinal=ordinal), self.assertRaises(InvalidTargetCatalogError):
                self.validate(epochs=epochs)

    def test_nonincreasing_epoch_thresholds(self):
        for index in range(1, 7):
            epochs = self.epochs[:]
            epochs[index] = replace(epochs[index], minimum_xp=epochs[index - 1].minimum_xp)
            with self.subTest(index=index), self.assertRaises(InvalidTargetCatalogError):
                self.validate(epochs=epochs)

    def test_invalid_duplicate_or_incompatible_epoch_codes(self):
        for code in ("", "  ", None, True, 12, ["a11-nested"], self.codes[0], "a11-not-configured"):
            epochs = self.epochs[:]
            epochs[1] = replace(epochs[1], code=code)
            with self.subTest(code=code), self.assertRaises(InvalidTargetCatalogError):
                self.validate(epochs=epochs)

    def test_explicit_code_sequence_required_and_must_match_order(self):
        for codes in (self.codes[:-1], self.codes + ["a11-extra"], self.codes[::-1],
                      [self.codes[0]] * 7, [None] * 7, [["nested"]] * 7,
                      "abcdefg", set(self.codes), {code: i for i, code in enumerate(self.codes)}):
            with self.subTest(codes=codes), self.assertRaises(InvalidTargetCatalogError):
                self.validate(ordered_epoch_codes=codes)

    def test_mismatch_at_every_position_one_through_seven(self):
        for index in range(7):
            epochs = self.epochs[:]
            epochs[index] = replace(epochs[index], minimum_xp=epochs[index].minimum_xp + 1)
            with self.subTest(position=index + 1), self.assertRaises(InvalidTargetCatalogError):
                self.validate(epochs=epochs)

    def test_both_initial_thresholds_must_be_zero(self):
        for field in ("levels", "epochs"):
            rows = getattr(self, field)[:]
            rows[0] = replace(rows[0], minimum_xp=1)
            with self.subTest(field=field), self.assertRaises(InvalidTargetCatalogError):
                self.validate(**{field: rows})
        with self.assertRaises(InvalidTargetCatalogError):
            self.validate(levels=[replace(self.levels[0], minimum_xp=1), *self.levels[1:]],
                          epochs=[replace(self.epochs[0], minimum_xp=1), *self.epochs[1:]])

    def test_strict_integer_fields_reject_bool_negative_fraction_and_types(self):
        for field, name in (("levels", "level"), ("levels", "minimum_xp"),
                            ("levels", "stat_points_awarded"), ("epochs", "ordinal"),
                            ("epochs", "minimum_xp")):
            for value in (True, False, -1, 1.5, 1.0, "1", None, Decimal("1"), []):
                rows = getattr(self, field)[:]
                rows[1] = replace(rows[1], **{name: value})
                with self.subTest(field=field, name=name, value=value), self.assertRaises(InvalidTargetCatalogError):
                    self.validate(**{field: rows})

    def test_invalid_or_missing_catalog_version(self):
        for version in (None, "", "  ", True, 1, [], {}):
            with self.subTest(version=version), self.assertRaises(InvalidTargetCatalogError):
                self.validate(catalog_version=version)
        with self.assertRaises(TypeError):
            validate_target_level_epoch_catalog(self.levels, self.epochs, ordered_epoch_codes=self.codes)

    def test_incompatible_containers_and_rows(self):
        for field in ("levels", "epochs"):
            for value in (None, 3, True, "rows", b"rows", {}, iter(())):
                with self.subTest(field=field, value=value), self.assertRaises(InvalidTargetCatalogError):
                    self.validate(**{field: value})
            for row in (None, object(), {}, [], (1, 0, 0), self.levels[0] if field == "epochs" else self.epochs[0]):
                rows = getattr(self, field)[:]
                rows[0] = row
                with self.subTest(field=field, row=row), self.assertRaises(InvalidTargetCatalogError):
                    self.validate(**{field: rows})

    def test_v1_independent_thresholds_remain_valid_but_fail_target(self):
        epochs = [replace(row, minimum_xp=(row.ordinal - 1) * 17) for row in self.epochs]
        before = (self.levels[:], epochs[:], self.codes[:])
        v1 = calculate_progression(0, 102, self.levels, epochs, ordered_stage_codes=self.codes)
        self.assertEqual(v1.stage_after_code, self.codes[-1])
        self.assertGreater(v1.total_stat_points_awarded, 0)
        with self.assertRaises(InvalidTargetCatalogError):
            self.validate(epochs=epochs)
        self.assertEqual((self.levels, epochs, self.codes), before)

    def test_does_not_call_v1_validation_even_for_compatible_inputs(self):
        with patch("apps.ecomotor.progression._validate_levels", side_effect=AssertionError), \
                patch("apps.ecomotor.progression._validate_stages", side_effect=AssertionError):
            self.assertEqual(self.validate().catalog_version, "a11-synthetic-v1")

    def test_module_imports_and_executes_without_django_in_isolated_python(self):
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from apps.ecomotor.target_catalog_validation import validate_target_level_epoch_catalog; "
            "from apps.ecomotor.progression import LevelDefinition, StageDefinition; "
            "codes=tuple('synthetic-'+str(i) for i in range(7)); "
            "levels=[LevelDefinition(i+1,i*11,3) for i in range(8)]; "
            "epochs=[StageDefinition(c,i+1,i*11) for i,c in enumerate(codes)]; "
            "s=validate_target_level_epoch_catalog(levels,epochs,ordered_epoch_codes=codes,catalog_version='synthetic'); "
            "assert len(s.levels)==8 and len(s.epochs)==7; "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules)"
        )
        result = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_file_network_or_database_access_during_validation(self):
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError):
            self.assertEqual(len(self.validate().levels), 8)


class TargetNotActivatedInV1Tests(DatabaseTestCase):
    def test_s3_and_readiness_keep_independent_catalogs_without_target_validation(self):
        from . import initialization_config
        from .configuration_checks import ReadinessStatus, check_ecomotor_readiness
        from .models import CharacterStats
        from .test_runtime_configuration import candidate_data
        from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
        from .xp_service import grant_historical_xp

        create_xp_catalogs()  # V1 synthetic fixture: four levels and independent stage thresholds.
        profile = create_xp_profile(username="a11-synthetic-v1-user")
        configuration = initialization_config.InitializationConfiguration(**candidate_data())
        with patch.object(target, "validate_target_level_epoch_catalog", side_effect=AssertionError), \
                patch.object(target, "TargetCatalogSnapshot", side_effect=AssertionError), \
                patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
            result = grant_historical_xp(profile, 102, "a11-synthetic-v1-grant")
            readiness = check_ecomotor_readiness(configuration=configuration)
        self.assertFalse(result.replayed)
        self.assertEqual(result.xp_after, 102)
        self.assertEqual(result.stat_points_awarded, 7)
        self.assertEqual(CharacterStats.objects.get(profile=profile).available_points, 14)
        self.assertEqual(readiness.status, ReadinessStatus.TECHNICALLY_READY)
