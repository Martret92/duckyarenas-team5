"""Synthetic structural exercises; never tests of real sources or Core permission."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
import inspect
from pathlib import Path
import subprocess
import sys
from unittest import TestCase
from unittest.mock import patch

from . import target_stats_config_validation as definitions
from . import target_stats_preparation as preparation
from . import target_stats_resolution as resolution
from . import target_stats_validation as statistics


def pairs(value=1):
    return [[code, value] for code in statistics.TARGET_STAT_CODES]


def definition(**changes):
    return definitions.validate_target_stats_definition(**(dict(
        option_code="synthetic-option", catalog_id="synthetic-catalog",
        catalog_version="catalog-r2", definition_version="definition-r9",
        bases=pairs(3),
    ) | changes))


class TargetStatsResolutionTests(TestCase):
    def candidate(self, **changes):
        return resolution._prepare_untrusted_resolution_candidate(**(dict(
            option_code="synthetic-option", definition=definition(),
            increments=pairs(), budget=8,
        ) | changes))

    def test_real_entry_always_rejects_regardless_of_option_and_increments(self):
        for option in ("synthetic-option", "Developer", "unknown", "", None, True, {}, object()):
            for increments in (pairs(), pairs(0), pairs(-1), {}, None, True, iter(pairs())):
                with self.subTest(option=type(option), increments=type(increments)), \
                        self.assertRaises(resolution.TargetStatsSourceUnavailableError):
                    resolution.resolve_target_stats_configuration(option_code=option, increments=increments)

    def test_public_signature_has_only_two_required_keyword_arguments(self):
        parameters = inspect.signature(resolution.resolve_target_stats_configuration).parameters
        self.assertEqual(tuple(parameters), ("option_code", "increments"))
        self.assertTrue(all(p.kind is inspect.Parameter.KEYWORD_ONLY
                            and p.default is inspect.Parameter.empty for p in parameters.values()))

    def test_no_injected_source_authority_budget_definition_or_version(self):
        for name in ("provider", "source", "definition", "bases", "budget", "catalog_version",
                     "definition_version", "authorized", "trusted", "published", "profile_id", "role"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                resolution.resolve_target_stats_configuration(option_code="synthetic", increments=pairs(),
                                                             **{name: True})

    def test_rejection_does_not_invoke_preparation_or_private_exercise(self):
        with patch.object(preparation, "prepare_target_stats_configuration", side_effect=AssertionError), \
                patch.object(resolution, "_prepare_untrusted_resolution_candidate", side_effect=AssertionError), \
                self.assertRaises(resolution.TargetStatsSourceUnavailableError):
            resolution.resolve_target_stats_configuration(option_code="synthetic", increments=pairs())

    def test_rejection_does_not_even_inspect_untrusted_objects(self):
        class Hostile:
            def __iter__(self):
                raise AssertionError("iteration")

            def __str__(self):
                raise AssertionError("conversion")

            def __bool__(self):
                raise AssertionError("truth test")

        with self.assertRaises(resolution.TargetStatsSourceUnavailableError):
            resolution.resolve_target_stats_configuration(option_code=Hostile(), increments=Hostile())

    def test_no_private_values_in_public_or_mismatch_messages(self):
        secret = "synthetic-private-option"
        with self.assertRaises(resolution.TargetStatsSourceUnavailableError) as unavailable:
            resolution.resolve_target_stats_configuration(option_code=secret, increments=pairs())
        with self.assertRaises(resolution.TargetStatsResolutionOptionMismatchError) as mismatch:
            self.candidate(option_code=secret)
        self.assertNotIn(secret, str(unavailable.exception))
        self.assertNotIn(secret, str(mismatch.exception))

    def test_candidate_composition_preserves_values_and_independent_versions(self):
        original = definition()
        result = self.candidate(definition=original)
        self.assertIs(type(result), preparation.PreparedTargetStatsConfiguration)
        self.assertEqual(result.definition, original)
        self.assertEqual(result.calculation.increments, tuple(tuple(pair) for pair in pairs()))
        self.assertEqual(result.calculation.bases, original.bases)
        self.assertEqual(result.calculation.effective, tuple((code, 4) for code in statistics.TARGET_STAT_CODES))
        self.assertNotEqual(result.definition.definition_version, result.definition.catalog_version)
        self.assertEqual(tuple(f.name for f in fields(result)), ("definition", "calculation"))

    def test_candidate_full_partial_and_zero_spending(self):
        for budget, value, used, remaining in ((6, 1, 6, 0), (8, 1, 6, 2), (8, 0, 0, 8), (0, 0, 0, 0)):
            with self.subTest(budget=budget, value=value):
                result = self.candidate(budget=budget, increments=pairs(value))
                self.assertEqual((result.calculation.points_used, result.calculation.points_remaining),
                                 (used, remaining))

    def test_candidate_mismatching_option_is_rejected(self):
        for option in ("different", "Synthetic-option", " synthetic-option", "synthetic-option "):
            with self.subTest(option=option), self.assertRaises(resolution.TargetStatsResolutionOptionMismatchError):
                self.candidate(option_code=option)

    def test_option_exact_nonblank_text_without_normalization_or_length_maximum(self):
        class Text(str):
            pass
        for option in (None, True, 1, "", " \t", [], {}, Text("synthetic-option")):
            with self.subTest(option=option), self.assertRaises(resolution.InvalidTargetStatsResolutionRequestError):
                self.candidate(option_code=option)
        for option in (" synthetic MiXeD ", "x" * 10000):
            self.assertEqual(self.candidate(option_code=option, definition=definition(option_code=option))
                             .definition.option_code, option)

    def test_absent_incompatible_or_subclass_definition_rejected_by_a431(self):
        class Child(definitions.TargetStatsDefinitionSnapshot):
            pass
        original = definition()
        child = Child(**{f.name: getattr(original, f.name) for f in fields(original)})
        for value in (None, {}, object(), child):
            with self.subTest(value=value), self.assertRaises(preparation.InvalidTargetStatsPreparationError):
                self.candidate(definition=value)

    def test_manipulated_definition_is_revalidated_without_repair(self):
        for name, value, error in (
            ("catalog_version", "", definitions.InvalidTargetStatsDefinitionIdentityError),
            ("option_code", None, definitions.InvalidTargetStatsDefinitionIdentityError),
            ("bases", pairs(-1), definitions.InvalidTargetStatsDefinitionNumericError),
            ("bases", pairs()[:-1], definitions.InvalidTargetStatsDefinitionStructureError),
        ):
            damaged = definition()
            object.__setattr__(damaged, name, value)
            before = deepcopy(damaged)
            with self.subTest(name=name), self.assertRaises(error):
                self.candidate(definition=damaged)
            self.assertEqual(damaged, before)

    def test_catalog_context_matching_and_absent_are_only_structural(self):
        for context in (None, definitions.TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")):
            result = self.candidate(expected_catalog=context)
            self.assertEqual(result, self.candidate())
            self.assertFalse(hasattr(result, "authorized"))
            self.assertFalse(hasattr(result, "expected_catalog"))

    def test_catalog_identity_or_version_mismatch_and_bad_context(self):
        for context in (definitions.TargetStatsCatalogContext("different", "catalog-r2"),
                        definitions.TargetStatsCatalogContext("synthetic-catalog", "different")):
            with self.subTest(context=context), self.assertRaises(definitions.TargetStatsDefinitionCatalogMismatchError):
                self.candidate(expected_catalog=context)
        with self.assertRaises(definitions.InvalidTargetStatsDefinitionStructureError):
            self.candidate(expected_catalog={})

    def test_invalid_duplicate_or_noncanonical_increments(self):
        for increments in (None, {}, pairs()[:-1], pairs() + [pairs()[0]],
                           [["SPE", 1]] + pairs()[1:]):
            with self.subTest(increments=increments), self.assertRaises(statistics.InvalidTargetStatsStructureError):
                self.candidate(increments=increments)

    def test_invalid_numeric_increments(self):
        for value in (-1, True, 1.0, Decimal("1"), "1", None):
            with self.subTest(value=value), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                self.candidate(increments=pairs(value))

    def test_budget_must_be_present_and_exact_nonnegative_integer(self):
        with self.assertRaises(TypeError):
            resolution._prepare_untrusted_resolution_candidate(
                option_code="synthetic-option", definition=definition(), increments=pairs())
        for budget in (None, -1, True, 8.0, Decimal("8"), "8", {}):
            with self.subTest(budget=budget), self.assertRaises(statistics.InvalidTargetStatsNumericError):
                self.candidate(budget=budget)

    def test_excess_budget_uses_existing_error(self):
        with self.assertRaises(statistics.TargetStatsBudgetExceededError):
            self.candidate(budget=5)

    def test_public_preparer_really_called_with_explicit_original_arguments(self):
        original, increments = definition(), pairs()
        context = definitions.TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")
        with patch.object(preparation, "prepare_target_stats_configuration",
                          wraps=preparation.prepare_target_stats_configuration) as prepare:
            resolution._prepare_untrusted_resolution_candidate(
                option_code="synthetic-option", definition=original, increments=increments,
                budget=8, expected_catalog=context)
        prepare.assert_called_once_with(definition=original, increments=increments, budget=8,
                                        expected_catalog=context)
        self.assertIs(prepare.call_args.kwargs["definition"], original)
        self.assertIs(prepare.call_args.kwargs["increments"], increments)

    def test_original_exceptions_are_not_wrapped_or_reclassified(self):
        errors = (preparation.InvalidTargetStatsPreparationError("synthetic"),
                  definitions.InvalidTargetStatsDefinitionIdentityError("synthetic"),
                  definitions.InvalidTargetStatsDefinitionStructureError("synthetic"),
                  definitions.InvalidTargetStatsDefinitionNumericError("synthetic"),
                  definitions.TargetStatsDefinitionCatalogMismatchError("synthetic"),
                  statistics.InvalidTargetStatsStructureError("synthetic"),
                  statistics.InvalidTargetStatsNumericError("synthetic"),
                  statistics.TargetStatsBudgetExceededError("synthetic"))
        for error in errors:
            with self.subTest(error=error), patch.object(preparation, "prepare_target_stats_configuration",
                                                       side_effect=error), self.assertRaises(type(error)) as caught:
                self.candidate()
            self.assertIs(caught.exception, error)

    def test_immutable_result_and_independent_defensive_copies(self):
        original, increments = definition(), pairs()
        result = self.candidate(definition=original, increments=increments)
        self.assertIsNot(result.definition, original)
        increments[0][1] = 999
        self.assertEqual(result.calculation.increments[0], ("ATK", 1))
        for component in (result, result.definition, result.calculation):
            self.assertFalse(hasattr(component, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                setattr(component, fields(component)[0].name, None)
        self.assertIs(type(result.calculation.increments), tuple)
        self.assertTrue(all(type(pair) is tuple for pair in result.calculation.increments))

    def test_inputs_unchanged_on_success_mismatch_and_numeric_failure(self):
        original, increments = definition(), pairs()
        before = deepcopy((original, increments))
        self.candidate(definition=original, increments=increments)
        with self.assertRaises(resolution.TargetStatsResolutionOptionMismatchError):
            self.candidate(option_code="different", definition=original, increments=increments)
        with self.assertRaises(statistics.TargetStatsBudgetExceededError):
            self.candidate(definition=original, increments=increments, budget=5)
        with self.assertRaises(resolution.TargetStatsSourceUnavailableError):
            resolution.resolve_target_stats_configuration(option_code="synthetic-option", increments=increments)
        self.assertEqual((original, increments), before)

    def test_deterministic_independent_candidates_and_large_integers(self):
        first = self.candidate()
        other = self.candidate(option_code="synthetic-other", definition=definition(
            option_code="synthetic-other", catalog_version="r99"), budget=100)
        self.assertEqual(first, self.candidate())
        self.assertNotEqual(first, other)
        huge = 10 ** 100
        self.assertEqual(self.candidate(increments=pairs(huge), budget=7 * huge)
                         .calculation.points_remaining, huge)

    def test_no_io_network_clock_or_automatic_demo_imports(self):
        original = definition()
        with patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("socket.socket", side_effect=AssertionError("network")), \
                patch("time.time", side_effect=AssertionError("clock")):
            self.candidate(definition=original)
            with self.assertRaises(resolution.TargetStatsSourceUnavailableError):
                resolution.resolve_target_stats_configuration(option_code="synthetic-option", increments=pairs())

    def test_isolated_import_and_execution_without_django_demo_or_services(self):
        root = str(Path(__file__).resolve().parents[2])
        script = f"""
import sys
sys.path.insert(0, {root!r})
from apps.ecomotor import target_stats_resolution as r
from apps.ecomotor.target_stats_config_validation import validate_target_stats_definition
codes = ('ATK', 'DEF', 'VEL', 'INT', 'LOG', 'CUACK')
pairs = tuple((code, 1) for code in codes)
definition = validate_target_stats_definition(option_code='synthetic', catalog_id='synthetic', catalog_version='r1', definition_version='r2', bases=pairs)
try:
    r.resolve_target_stats_configuration(option_code='synthetic', increments=pairs)
except r.TargetStatsSourceUnavailableError:
    pass
else:
    raise AssertionError('Real resolution must reject')
result = r._prepare_untrusted_resolution_candidate(option_code='synthetic', definition=definition, increments=pairs, budget=8)
assert result.calculation.points_remaining == 2
assert not any(name == 'django' or name.startswith('django.') for name in sys.modules)
assert not any(name.endswith(('demo_forms', 'demo_views', 'demo_settings', 'models', 'xp_service', 'stat_allocation')) for name in sys.modules)
assert not any(name.startswith(('apps.users', 'apps.duckies', 'apps.rewards')) for name in sys.modules)
"""
        process = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
