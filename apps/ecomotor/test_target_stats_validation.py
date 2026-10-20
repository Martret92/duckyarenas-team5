"""A4.1: all codes' quantities and budgets below are synthetic, never official."""

import ast
from collections import UserDict
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, fields, replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from . import target_stats_validation as stats
from .target_stats_validation import (
    InvalidTargetStatsError, InvalidTargetStatsNumericError,
    InvalidTargetStatsStructureError, TargetStatsBudgetExceededError,
    TARGET_STAT_CODES, TargetStatsResult, validate_target_stats,
)


def synthetic_pairs(values=(10, 8, 6, 7, 9, 5)):
    return list(zip(TARGET_STAT_CODES, values))


class TargetStatsValidationTests(TestCase):
    def setUp(self):
        self.bases = synthetic_pairs()
        self.increments = synthetic_pairs((1, 2, 0, 3, 0, 1))

    def validate(self, **changes):
        return validate_target_stats(**(dict(bases=self.bases, increments=self.increments, budget=11) | changes))

    def test_exact_six_codes_and_effective_calculation(self):
        result = self.validate()
        self.assertEqual(TARGET_STAT_CODES, ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK"))
        self.assertEqual(result.bases, tuple(self.bases))
        self.assertEqual(result.increments, tuple(self.increments))
        self.assertEqual(result.effective, tuple(synthetic_pairs((11, 10, 6, 10, 9, 6))))
        self.assertEqual((result.budget, result.points_used, result.points_remaining), (11, 7, 4))

    def test_full_budget_spent(self):
        result = self.validate(budget=7)
        self.assertEqual((result.points_used, result.points_remaining), (7, 0))

    def test_partial_budget_allowed(self):
        result = self.validate(budget=12)
        self.assertEqual((result.points_used, result.points_remaining), (7, 5))

    def test_zero_increments_preserve_all_points(self):
        result = self.validate(increments=synthetic_pairs((0,) * 6))
        self.assertEqual(result.effective, tuple(self.bases))
        self.assertEqual((result.points_used, result.points_remaining), (0, 11))

    def test_zero_budget_and_zero_increments(self):
        result = self.validate(increments=synthetic_pairs((0,) * 6), budget=0)
        self.assertEqual((result.points_used, result.points_remaining), (0, 0))

    def test_all_zero_bases_are_valid(self):
        result = self.validate(bases=synthetic_pairs((0,) * 6))
        self.assertEqual(result.effective, tuple(self.increments))

    def test_zero_budget_with_one_positive_increment_is_exceeded(self):
        with self.assertRaises(TargetStatsBudgetExceededError):
            self.validate(increments=synthetic_pairs((0, 0, 0, 0, 0, 1)), budget=0)

    def test_budget_exceeded_by_one_or_more(self):
        for budget in (6, 1):
            with self.subTest(budget=budget), self.assertRaises(TargetStatsBudgetExceededError):
                self.validate(budget=budget)

    def test_any_order_and_mixed_explicit_pair_containers_yield_canonical_result(self):
        expected = self.validate()
        for offset in range(6):
            with self.subTest(offset=offset):
                bases = [list(pair) for pair in self.bases[offset:] + self.bases[:offset]]
                increments = tuple(self.increments[::-1])
                self.assertEqual(self.validate(bases=bases, increments=increments), expected)

    def test_budget_is_explicit_mandatory_keyword_only(self):
        with self.assertRaises(TypeError):
            validate_target_stats(self.bases, self.increments)
        with self.assertRaises(TypeError):
            validate_target_stats(self.bases, self.increments, 11)

    def test_invalid_numeric_types_and_negative_values_in_every_input_position(self):
        class IntegerSubclass(int):
            pass

        invalid = (-1, True, False, 0.0, 1.0, 1.5, float("nan"), float("inf"),
                   Decimal("1"), Fraction(1, 1), "1", None, [], {}, object(), IntegerSubclass(1))
        for value in invalid:
            for name in ("bases", "increments"):
                for index in range(6):
                    pairs = getattr(self, name).copy()
                    pairs[index] = (pairs[index][0], value)
                    with self.subTest(input=name, index=index, kind=type(value)), self.assertRaises(InvalidTargetStatsNumericError):
                        self.validate(**{name: pairs})
            with self.subTest(input="budget", kind=type(value)), self.assertRaises(InvalidTargetStatsNumericError):
                self.validate(budget=value)

    def test_no_implicit_numeric_conversion_methods_called(self):
        class Convertible:
            def __int__(self):
                raise AssertionError("No integer conversion is permitted.")

        for name in ("bases", "increments", "budget"):
            value = Convertible()
            changes = {name: value if name == "budget" else [("ATK", value)] + getattr(self, name)[1:]}
            with self.subTest(name=name), self.assertRaises(InvalidTargetStatsNumericError):
                self.validate(**changes)

    def test_missing_attributes_rejected_separately_for_bases_and_increments(self):
        for name in ("bases", "increments"):
            for index in range(6):
                pairs = getattr(self, name)
                with self.subTest(name=name, missing=index), self.assertRaises(InvalidTargetStatsStructureError):
                    self.validate(**{name: pairs[:index] + pairs[index + 1:]})

    def test_additional_attributes_rejected(self):
        for name in ("bases", "increments"):
            with self.subTest(name=name), self.assertRaises(InvalidTargetStatsStructureError):
                self.validate(**{name: getattr(self, name) + [("EXTRA", 0)]})

    def test_duplicates_detected_before_mapping_collapses_keys(self):
        for name in ("bases", "increments"):
            for duplicate in (("ATK", 0), ("ATK", 999)):
                pairs = getattr(self, name) + [duplicate]
                before = deepcopy(pairs)
                with self.subTest(name=name, duplicate=duplicate), self.assertRaisesRegex(InvalidTargetStatsStructureError, "Duplicate"):
                    self.validate(**{name: pairs})
                self.assertEqual(pairs, before)
            with self.assertRaisesRegex(InvalidTargetStatsStructureError, "Duplicate"):
                self.validate(**{name: getattr(self, name)[:-1] + [("ATK", 0)]})

    def test_invalid_noncanonical_codes_in_each_collection(self):
        for name in ("bases", "increments"):
            for code in ("SPE", "atk", "ATK ", " ATK", "Cuack", "CUAK", "", "LOGISTICA"):
                with self.subTest(name=name, code=code), self.assertRaises(InvalidTargetStatsStructureError):
                    self.validate(**{name: [(code, 0)] + getattr(self, name)[1:]})

    def test_codes_require_exact_string(self):
        class CodeSubclass(str):
            pass

        for name in ("bases", "increments"):
            for code in (None, 1, True, b"ATK", [], {}, CodeSubclass("ATK")):
                with self.subTest(name=name, kind=type(code)), self.assertRaises(InvalidTargetStatsStructureError):
                    self.validate(**{name: [(code, 0)] + getattr(self, name)[1:]})

    def test_pairs_require_exactly_two_elements(self):
        for name in ("bases", "increments"):
            for pair in ([], ["ATK"], ("ATK", 0, "extra"), "ATK", b"ATK", {"ATK": 0}, None, iter(("ATK", 0))):
                with self.subTest(name=name, kind=type(pair)), self.assertRaises(InvalidTargetStatsStructureError):
                    self.validate(**{name: [pair] + getattr(self, name)[1:]})

    def test_external_containers_mappings_and_iterators_rejected(self):
        for name in ("bases", "increments"):
            pairs = getattr(self, name)
            for values in (None, "ATK", b"ATK", bytearray(b"ATK"), {}, dict(pairs),
                           UserDict(dict(pairs)), MappingProxyType(dict(pairs)), set(pairs),
                           iter(pairs), (pair for pair in pairs), 1, SimpleNamespace(pairs=pairs)):
                with self.subTest(name=name, kind=type(values)), self.assertRaises(InvalidTargetStatsStructureError):
                    self.validate(**{name: values})

    def test_generators_are_rejected_without_being_consumed(self):
        consumed = []

        def rows():
            consumed.append(True)
            yield from self.bases

        with self.assertRaises(InvalidTargetStatsStructureError):
            self.validate(bases=rows())
        with self.assertRaises(InvalidTargetStatsStructureError):
            self.validate(increments=[rows()] + self.increments[1:])
        self.assertEqual(consumed, [])

    def test_inputs_remain_unchanged_after_success_and_failure(self):
        bases, increments = [list(pair) for pair in self.bases], [list(pair) for pair in self.increments]
        before = deepcopy((bases, increments))
        self.validate(bases=bases, increments=increments)
        self.assertEqual((bases, increments), before)
        with self.assertRaises(TargetStatsBudgetExceededError):
            self.validate(bases=bases, increments=increments, budget=6)
        self.assertEqual((bases, increments), before)

    def test_defensive_copy_survives_later_mutations_to_input_lists(self):
        bases, increments = [list(pair) for pair in self.bases], [list(pair) for pair in self.increments]
        result = self.validate(bases=bases, increments=increments)
        expected = deepcopy(asdict(result))
        bases[0][1] = 999
        increments[1][0] = "SPE"
        increments.clear()
        bases.append(["EXTRA", []])
        self.assertEqual(asdict(result), expected)

    def test_result_frozen_slots_and_nested_tuples(self):
        result = self.validate()
        self.assertFalse(hasattr(result, "__dict__"))
        for field in fields(result):
            with self.subTest(field=field.name), self.assertRaises(FrozenInstanceError):
                setattr(result, field.name, None)
        for values in (result.bases, result.increments, result.effective):
            self.assertIs(type(values), tuple)
            self.assertEqual(tuple(code for code, _ in values), TARGET_STAT_CODES)
            for pair in values:
                self.assertIs(type(pair), tuple)
                with self.assertRaises(TypeError):
                    pair[1] = 999

    def test_direct_construction_validates_and_copies_all_collections(self):
        expected = self.validate()
        values = {field.name: getattr(expected, field.name) for field in fields(expected)}
        for name in ("bases", "increments", "effective"):
            values[name] = [list(pair) for pair in values[name][::-1]]
        result = TargetStatsResult(**values)
        self.assertEqual(result, expected)
        for name in ("bases", "increments", "effective"):
            values[name][0][1] = 999
            values[name].clear()
        self.assertEqual(result, expected)

    def test_direct_construction_rejects_contradictory_derived_values(self):
        result = self.validate()
        for changes in ({"points_used": 6}, {"points_remaining": 3}, {"budget": 12},
                        {"effective": synthetic_pairs((12, 10, 6, 10, 9, 6))},
                        {"increments": synthetic_pairs((0,) * 6)},
                        {"bases": synthetic_pairs((0,) * 6)}):
            with self.subTest(changes=changes), self.assertRaises(InvalidTargetStatsNumericError):
                replace(result, **changes)

    def test_direct_construction_rejects_invalid_numbers_including_boolean_equivalents(self):
        result = self.validate()
        for name in ("budget", "points_used", "points_remaining"):
            for value in (-1, True, False, 0.0, "0", None, Decimal("0")):
                with self.subTest(name=name, kind=type(value)), self.assertRaises(InvalidTargetStatsNumericError):
                    replace(result, **{name: value})
        with self.assertRaises(TargetStatsBudgetExceededError):
            replace(result, budget=6, points_remaining=0)

    def test_direct_construction_rejects_invalid_structure_and_nested_mutable_values(self):
        result = self.validate()
        for name in ("bases", "increments", "effective"):
            for values in (dict(result.bases), result.bases[:-1], result.bases + (("ATK", 1),), iter(result.bases)):
                with self.subTest(name=name, kind=type(values)), self.assertRaises(InvalidTargetStatsStructureError):
                    replace(result, **{name: values})
            with self.subTest(name=name), self.assertRaises(InvalidTargetStatsNumericError):
                replace(result, **{name: [("ATK", [])] + list(result.bases[1:])})

    def test_deterministic_for_repeated_inputs(self):
        self.assertEqual(self.validate(), self.validate())
        self.assertEqual(asdict(self.validate()), asdict(self.validate()))

    def test_configurations_and_budgets_independent_without_shared_balance(self):
        first = self.validate(budget=7)
        second = self.validate(bases=synthetic_pairs((2, 1, 0, 3, 0, 4)),
                               increments=synthetic_pairs((0, 0, 0, 0, 0, 2)), budget=20)
        self.assertEqual((first.points_used, first.points_remaining), (7, 0))
        self.assertEqual((second.points_used, second.points_remaining), (2, 18))
        self.assertEqual(first, self.validate(budget=7))
        with self.assertRaises(TargetStatsBudgetExceededError):
            self.validate(budget=1)
        self.assertEqual(first, self.validate(budget=7))

    def test_large_integers_without_functional_or_storage_maximum(self):
        large = 10**200
        result = self.validate(bases=synthetic_pairs((large,) * 6),
                               increments=synthetic_pairs((large,) * 6), budget=large * 9)
        self.assertEqual(result.effective, tuple(synthetic_pairs((large * 2,) * 6)))
        self.assertEqual((result.points_used, result.points_remaining), (large * 6, large * 3))

    def test_minimal_error_hierarchy_and_no_partial_result(self):
        for error in (InvalidTargetStatsStructureError, InvalidTargetStatsNumericError, TargetStatsBudgetExceededError):
            self.assertTrue(issubclass(error, InvalidTargetStatsError))
        self.assertTrue(issubclass(InvalidTargetStatsError, ValueError))
        with patch.object(stats, "TargetStatsResult", side_effect=AssertionError):
            with self.assertRaises(TargetStatsBudgetExceededError):
                self.validate(budget=0)

    def test_result_contains_no_authorization_identity_or_persisted_state(self):
        self.assertEqual({field.name for field in fields(TargetStatsResult)},
                         {"bases", "increments", "effective", "budget", "points_used", "points_remaining"})

    def test_no_external_access_or_clock_dependency_during_validation(self):
        with patch("builtins.open", side_effect=AssertionError), patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError), patch("time.time", side_effect=AssertionError):
            self.assertEqual(self.validate(), self.validate())

    def test_no_calls_to_previous_services_and_only_standard_library_imports(self):
        names = {"apps.ecomotor.xp_service": "grant_historical_xp",
                 "apps.ecomotor.stat_allocation": "allocate_stat_points",
                 "apps.ecomotor.target_catalog_validation": "validate_target_level_epoch_catalog",
                 "apps.ecomotor.target_progression": "calculate_target_progression",
                 "apps.ecomotor.target_xp_plan": "plan_target_xp_grant",
                 "apps.ecomotor.legacy_transition_audit": "audit_legacy_transition",
                 "apps.ecomotor.legacy_inventory_reader": "extract_legacy_audit_snapshot",
                 "apps.ecomotor.profile_classification_rules": "evaluate_classification_rules"}
        stubs = {module: SimpleNamespace(**{name: Mock(side_effect=AssertionError)}) for module, name in names.items()}
        with patch.dict(sys.modules, stubs):
            self.validate()
        for module, name in names.items():
            getattr(stubs[module], name).assert_not_called()
        tree = ast.parse(Path(stats.__file__).read_text(encoding="utf-8"))
        self.assertEqual([node.module for node in tree.body if isinstance(node, ast.ImportFrom)], ["dataclasses"])
        self.assertFalse(any(isinstance(node, ast.Import) for node in tree.body))
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")],
                         ["validate_target_stats"])

    def test_import_and_execution_in_isolated_python_without_django(self):
        code = (
            "import sys; sys.path.insert(0,sys.argv[1]); "
            "from apps.ecomotor.target_stats_validation import *; "
            "b=[(c,2) for c in TARGET_STAT_CODES]; i=[(c,1) for c in TARGET_STAT_CODES]; "
            "r=validate_target_stats(b,i,budget=9); "
            "assert r.points_used==6 and r.points_remaining==3; "
            "assert all(value==3 for code,value in r.effective); "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules); "
            "assert not any(n.startswith('apps.ecomotor.') and n!='apps.ecomotor.target_stats_validation' for n in sys.modules)"
        )
        completed = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
