"""Synthetic configurations only; no official option, version or budget."""

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
import inspect
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from . import target_stats_config_validation as definitions
from . import target_stats_validation as statistics
from . import target_stats_preparation as preparation
from .target_stats_preparation import (
    InvalidTargetStatsPreparationError,
    PreparedTargetStatsConfiguration,
    prepare_target_stats_configuration,
)


def pairs(value=1):
    return [[code, value] for code in statistics.TARGET_STAT_CODES]


def definition(**changes):
    return definitions.validate_target_stats_definition(**(dict(
        option_code="synthetic-option", catalog_id="synthetic-catalog",
        catalog_version="catalog-r2", definition_version="definition-r7",
        bases=pairs(3),
    ) | changes))


class TargetStatsPreparationTests(TestCase):
    def prepare(self, **changes):
        return prepare_target_stats_configuration(**(dict(
            definition=definition(), increments=pairs(), budget=9,
        ) | changes))

    def test_complete_calculation_and_original_identity(self):
        result = self.prepare()
        self.assertEqual(result.calculation.effective, tuple((c, 4) for c in statistics.TARGET_STAT_CODES))
        self.assertEqual((result.calculation.budget, result.calculation.points_used,
                          result.calculation.points_remaining), (9, 6, 3))
        self.assertEqual(result.definition, definition())
        self.assertNotEqual(result.definition.catalog_version, result.definition.definition_version)
        self.assertEqual(result.definition.bases, result.calculation.bases)

    def test_full_partial_zero_and_zero_budget(self):
        for budget, increment, used, remaining in ((6, 1, 6, 0), (9, 1, 6, 3),
                                                  (9, 0, 0, 9), (0, 0, 0, 0)):
            with self.subTest(budget=budget, increment=increment):
                calculation = self.prepare(budget=budget, increments=pairs(increment)).calculation
                self.assertEqual((calculation.points_used, calculation.points_remaining), (used, remaining))

    def test_budget_excess_including_one_unit(self):
        for budget in (0, 5):
            with self.subTest(budget=budget), self.assertRaises(statistics.TargetStatsBudgetExceededError):
                self.prepare(budget=budget)

    def test_arguments_are_keyword_only_and_budget_required(self):
        parameters = inspect.signature(prepare_target_stats_configuration).parameters
        self.assertEqual(tuple(parameters), ("definition", "increments", "budget", "expected_catalog"))
        self.assertTrue(all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters.values()))
        with self.assertRaises(TypeError):
            prepare_target_stats_configuration(definition(), pairs(), 9)
        with self.assertRaises(TypeError):
            prepare_target_stats_configuration(definition=definition(), increments=pairs())

    def test_structural_increment_errors_propagate(self):
        invalid = [pairs()[:-1], pairs() + [["EXTRA", 0]], pairs() + [pairs()[0]],
                   [["SPE", 0]] + pairs()[1:], [["atk", 0]] + pairs()[1:],
                   [[" ATK", 0]] + pairs()[1:], [[1, 0]] + pairs()[1:],
                   [["ATK"]] + pairs()[1:], dict(pairs()), iter(pairs()), None]
        for increments in invalid:
            with self.subTest(increments=repr(increments)), \
                    self.assertRaises(statistics.InvalidTargetStatsStructureError):
                self.prepare(increments=increments)

    def test_numeric_increment_errors_propagate(self):
        for value in (True, False, -1, 1.0, Decimal("1"), "1", None, []):
            with self.subTest(value=value), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                self.prepare(increments=[["ATK", value]] + pairs()[1:])

    def test_numeric_budget_errors_propagate(self):
        for value in (True, False, -1, 9.0, Decimal("9"), "9", None, []):
            with self.subTest(value=value), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                self.prepare(budget=value)

    def test_exact_definition_type_required(self):
        class Child(definitions.TargetStatsDefinitionSnapshot):
            pass
        original = definition()
        invalid = (None, {}, dict(option_code="synthetic-option"), SimpleNamespace(
            **{f.name: getattr(original, f.name) for f in fields(original)}),
            Child(original.option_code, original.catalog_id, original.catalog_version,
                  original.definition_version, original.bases))
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(InvalidTargetStatsPreparationError):
                self.prepare(definition=value)

    def test_manipulated_definition_identities_revalidated(self):
        for name in ("option_code", "catalog_id", "catalog_version", "definition_version"):
            for value in (None, "", " ", True, 7):
                damaged = definition()
                object.__setattr__(damaged, name, value)
                with self.subTest(name=name, value=value), \
                        self.assertRaises(definitions.InvalidTargetStatsDefinitionIdentityError):
                    self.prepare(definition=damaged)

    def test_manipulated_definition_bases_revalidated(self):
        for value, error in ((None, definitions.InvalidTargetStatsDefinitionStructureError),
                             (pairs()[:-1], definitions.InvalidTargetStatsDefinitionStructureError),
                             (pairs() + [pairs()[0]], definitions.InvalidTargetStatsDefinitionStructureError),
                             (pairs(True), definitions.InvalidTargetStatsDefinitionNumericError),
                             (pairs(-1), definitions.InvalidTargetStatsDefinitionNumericError)):
            damaged = definition()
            object.__setattr__(damaged, "bases", value)
            with self.subTest(value=value), self.assertRaises(error):
                self.prepare(definition=damaged)

    def test_missing_manipulated_definition_field_rejected(self):
        damaged = definition()
        object.__delattr__(damaged, "bases")
        with self.assertRaises(definitions.InvalidTargetStatsDefinitionStructureError):
            self.prepare(definition=damaged)

    def test_matching_or_absent_context_and_distinct_versions(self):
        for context in (None, definitions.TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")):
            result = self.prepare(expected_catalog=context)
            self.assertEqual(result.definition.definition_version, "definition-r7")
            self.assertEqual(tuple(f.name for f in fields(result)), ("definition", "calculation"))

    def test_context_identity_and_version_mismatch(self):
        for context in (definitions.TargetStatsCatalogContext("other", "catalog-r2"),
                        definitions.TargetStatsCatalogContext("synthetic-catalog", "other")):
            with self.subTest(context=context), self.assertRaises(definitions.TargetStatsDefinitionCatalogMismatchError):
                self.prepare(expected_catalog=context)

    def test_context_wrong_types_and_subclass(self):
        class Child(definitions.TargetStatsCatalogContext):
            pass
        for context in ({}, "catalog-r2", SimpleNamespace(catalog_id="synthetic-catalog"),
                        Child("synthetic-catalog", "catalog-r2")):
            with self.subTest(context=context), self.assertRaises(definitions.InvalidTargetStatsDefinitionStructureError):
                self.prepare(expected_catalog=context)

    def test_manipulated_context_revalidated(self):
        context = definitions.TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")
        object.__setattr__(context, "catalog_version", False)
        with self.assertRaises(definitions.InvalidTargetStatsDefinitionIdentityError):
            self.prepare(expected_catalog=context)

    def test_direct_construction_copies_valid_components(self):
        original = definition()
        calculation = statistics.validate_target_stats(original.bases, pairs(), budget=9)
        result = PreparedTargetStatsConfiguration(original, calculation)
        self.assertEqual(result, self.prepare())
        self.assertIsNot(result.definition, original)
        self.assertIsNot(result.calculation, calculation)
        self.assertIsNot(result.definition.bases, original.bases)
        self.assertIsNot(result.calculation.increments, calculation.increments)

    def test_direct_construction_exact_types(self):
        class Child(statistics.TargetStatsResult):
            pass
        valid = self.prepare()
        child = Child(**{f.name: getattr(valid.calculation, f.name) for f in fields(valid.calculation)})
        for value in (None, {}, child):
            with self.subTest(value=value), self.assertRaises(InvalidTargetStatsPreparationError):
                PreparedTargetStatsConfiguration(valid.definition, value)
        with self.assertRaises(InvalidTargetStatsPreparationError):
            PreparedTargetStatsConfiguration(None, valid.calculation)

    def test_direct_construction_bases_mismatch(self):
        with self.assertRaises(InvalidTargetStatsPreparationError):
            PreparedTargetStatsConfiguration(definition(bases=pairs(4)), self.prepare().calculation)

    def test_direct_construction_checks_every_calculation_field(self):
        for name, value in (("points_used", 5), ("points_remaining", 2), ("budget", True),
                            ("effective", pairs(999)), ("increments", pairs(-1))):
            damaged = self.prepare().calculation
            object.__setattr__(damaged, name, value)
            with self.subTest(name=name), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                PreparedTargetStatsConfiguration(definition(), damaged)

    def test_direct_construction_checks_nested_structure(self):
        for name in ("bases", "increments", "effective"):
            damaged = self.prepare().calculation
            object.__setattr__(damaged, name, [["ATK", []]])
            with self.subTest(name=name), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                PreparedTargetStatsConfiguration(definition(), damaged)

    def test_direct_construction_revalidates_definition(self):
        damaged = definition()
        object.__setattr__(damaged, "definition_version", "")
        with self.assertRaises(definitions.InvalidTargetStatsDefinitionIdentityError):
            PreparedTargetStatsConfiguration(damaged, self.prepare().calculation)

    def test_defensive_copies_even_after_frozen_objects_were_bypassed(self):
        original = definition()
        calculation = self.prepare().calculation
        mutable_bases = pairs(3)
        mutable_increments = pairs()
        object.__setattr__(original, "bases", mutable_bases)
        object.__setattr__(calculation, "bases", mutable_bases)
        object.__setattr__(calculation, "increments", mutable_increments)
        direct = PreparedTargetStatsConfiguration(original, calculation)
        prepared = self.prepare(definition=original, increments=mutable_increments)
        mutable_bases[0][1] = 999
        mutable_increments.clear()
        self.assertEqual(direct, prepared)
        self.assertEqual(direct.definition.bases[0], ("ATK", 3))
        self.assertEqual(direct.calculation.increments[0], ("ATK", 1))

    def test_frozen_slots_and_immutable_nested_collections(self):
        result = self.prepare()
        for component in (result, result.definition, result.calculation):
            self.assertFalse(hasattr(component, "__dict__"))
            name = fields(component)[0].name
            with self.assertRaises(FrozenInstanceError):
                setattr(component, name, None)
        for values in (result.definition.bases, result.calculation.bases,
                       result.calculation.increments, result.calculation.effective):
            self.assertIs(type(values), tuple)
            self.assertTrue(all(type(pair) is tuple for pair in values))
            with self.assertRaises(TypeError):
                values[0][1] = 99

    def test_inputs_unchanged_on_success_and_failure(self):
        original, increments = definition(), pairs()
        before = deepcopy((original, increments))
        self.prepare(definition=original, increments=increments)
        self.assertEqual((original, increments), before)
        with self.assertRaises(statistics.TargetStatsBudgetExceededError):
            self.prepare(definition=original, increments=increments, budget=5)
        self.assertEqual((original, increments), before)

    def test_canonical_order_and_determinism(self):
        expected = self.prepare()
        reversed_definition = definition(bases=list(reversed(pairs(3))))
        self.assertEqual(self.prepare(definition=reversed_definition, increments=list(reversed(pairs()))), expected)
        self.assertEqual(self.prepare(), expected)

    def test_independent_options_versions_and_budgets(self):
        first = self.prepare()
        second = self.prepare(definition=definition(option_code="synthetic-other", catalog_version="r99"), budget=20)
        self.assertEqual(first, self.prepare())
        self.assertEqual(second.calculation.points_remaining, 14)
        self.assertEqual(second.definition.catalog_version, "r99")
        self.assertNotEqual(first, second)

    def test_large_integers_without_artificial_limits(self):
        huge = 10 ** 100
        result = self.prepare(definition=definition(bases=pairs(huge)), increments=pairs(huge), budget=7 * huge)
        self.assertEqual(result.calculation.points_remaining, huge)
        self.assertEqual(result.calculation.effective[0][1], 2 * huge)

    def test_public_apis_are_really_called_with_original_inputs(self):
        original, increments = definition(), pairs()
        context = definitions.TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")
        with patch.object(definitions, "validate_target_stats_definition", wraps=definitions.validate_target_stats_definition) as validate_definition, \
                patch.object(statistics, "validate_target_stats", wraps=statistics.validate_target_stats) as validate_stats:
            prepare_target_stats_configuration(definition=original, increments=increments,
                                               budget=9, expected_catalog=context)
        self.assertGreaterEqual(validate_definition.call_count, 1)
        self.assertIs(validate_definition.call_args_list[0].kwargs["expected_catalog"], context)
        validate_stats.assert_called_once_with(original.bases, increments, budget=9)
        self.assertIs(validate_stats.call_args.args[1], increments)

    def test_existing_exception_instances_are_not_wrapped(self):
        for module, name, error in (
            (definitions, "validate_target_stats_definition", definitions.InvalidTargetStatsDefinitionIdentityError("synthetic")),
            (statistics, "validate_target_stats", statistics.TargetStatsBudgetExceededError("synthetic")),
        ):
            original = definition()
            with patch.object(module, name, side_effect=error), self.assertRaises(type(error)) as caught:
                self.prepare(definition=original)
            self.assertIs(caught.exception, error)

    def test_no_io_network_clock_or_other_service_calls_during_preparation(self):
        original, increments = definition(), pairs()
        with patch("builtins.open", side_effect=AssertionError("file I/O")), \
                patch("socket.socket", side_effect=AssertionError("network")), \
                patch("time.time", side_effect=AssertionError("clock")):
            self.prepare(definition=original, increments=increments)
        tree = ast.parse(inspect.getsource(preparation))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertEqual(imports, ["dataclasses", None, None, "target_stats_config_validation", "target_stats_validation"])
        self.assertFalse(any(isinstance(node, ast.Import) for node in ast.walk(tree)))

    def test_isolated_interpreter_without_django(self):
        root = str(Path(__file__).resolve().parents[2])
        script = f"""
import sys
sys.path.insert(0, {root!r})
from apps.ecomotor.target_stats_preparation import prepare_target_stats_configuration
from apps.ecomotor.target_stats_config_validation import validate_target_stats_definition
codes = ('ATK', 'DEF', 'VEL', 'INT', 'LOG', 'CUACK')
pairs = tuple((code, 0) for code in codes)
definition = validate_target_stats_definition(option_code='synthetic', catalog_id='synthetic', catalog_version='r1', definition_version='r2', bases=pairs)
result = prepare_target_stats_configuration(definition=definition, increments=pairs, budget=0)
assert result.calculation.points_remaining == 0
assert not any(name == 'django' or name.startswith('django.') for name in sys.modules)
assert not any(name.endswith(('xp_service', 'models', 'target_xp_plan', 'legacy_inventory_reader')) for name in sys.modules)
"""
        process = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
