"""A4.2.1: synthetic identities and quantities, never official configuration."""

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from fractions import Fraction
import inspect
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from . import target_stats_config_validation as definitions
from .target_stats_config_validation import (
    InvalidTargetStatsDefinitionError,
    InvalidTargetStatsDefinitionIdentityError,
    InvalidTargetStatsDefinitionNumericError,
    InvalidTargetStatsDefinitionStructureError,
    TargetStatsCatalogContext,
    TargetStatsDefinitionCatalogMismatchError,
    TargetStatsDefinitionSnapshot,
    validate_target_stats_definition,
)
from .target_stats_validation import TARGET_STAT_CODES, validate_target_stats


def synthetic_bases():
    return [[code, value] for code, value in zip(TARGET_STAT_CODES, (2, 3, 4, 5, 6, 7))]


def synthetic_definition(**changes):
    return dict(option_code="synthetic-option", catalog_id="synthetic-catalog",
                catalog_version="catalog-r2", definition_version="stats-r7",
                bases=synthetic_bases()) | changes


class TargetStatsDefinitionTests(TestCase):
    def validate(self, **changes):
        return validate_target_stats_definition(**synthetic_definition(**changes))

    def test_definition_preserves_all_dimensions_and_canonical_bases(self):
        result = self.validate()
        self.assertEqual((result.option_code, result.catalog_id, result.catalog_version,
                          result.definition_version),
                         ("synthetic-option", "synthetic-catalog", "catalog-r2", "stats-r7"))
        self.assertEqual(result.bases, tuple(tuple(pair) for pair in synthetic_bases()))

    def test_all_function_arguments_are_keyword_only(self):
        parameters = inspect.signature(validate_target_stats_definition).parameters
        self.assertEqual(tuple(parameters), ("option_code", "catalog_id", "catalog_version",
                                             "definition_version", "bases", "expected_catalog"))
        self.assertTrue(all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters.values()))
        with self.assertRaises(TypeError):
            validate_target_stats_definition("synthetic-option")

    def test_each_identity_rejects_blank_or_wrong_types_without_conversion(self):
        class Text(str):
            pass

        convertible = Mock()
        for name in ("option_code", "catalog_id", "catalog_version", "definition_version"):
            for value in (None, "", " ", "\t\n", 1, True, False, 1.0, Text("synthetic"),
                          [], {}, convertible):
                with self.subTest(field=name, value=repr(value)), \
                        self.assertRaises(InvalidTargetStatsDefinitionIdentityError):
                    self.validate(**{name: value})
        self.assertEqual(convertible.mock_calls, [])

    def test_valid_identity_text_is_exact_without_format_or_length_limits(self):
        for value in (" synthetic MiXeD ", "catalog/opaque:revision", "x" * 10000):
            result = self.validate(**{name: value for name in
                                     ("option_code", "catalog_id", "catalog_version", "definition_version")})
            for name in ("option_code", "catalog_id", "catalog_version", "definition_version"):
                self.assertEqual(getattr(result, name), value)

    def test_catalog_and_definition_versions_are_independent(self):
        context = TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")
        result = self.validate(definition_version="unrelated-stats-version", expected_catalog=context)
        self.assertNotEqual(result.definition_version, result.catalog_version)

    def test_lists_tuples_and_mixed_pairs_are_accepted_without_input_mutation(self):
        for bases in (synthetic_bases(), tuple(tuple(p) for p in synthetic_bases()),
                      [tuple(p) if i % 2 else p for i, p in enumerate(synthetic_bases())]):
            before = deepcopy(bases)
            with self.subTest(bases=bases):
                self.validate(bases=bases)
                self.assertEqual(bases, before)

    def test_arbitrary_order_is_canonicalized_only_in_result(self):
        bases = list(reversed(synthetic_bases()))
        before = deepcopy(bases)
        result = self.validate(bases=bases)
        self.assertEqual(tuple(code for code, _ in result.bases), TARGET_STAT_CODES)
        self.assertEqual(result.bases, tuple(tuple(p) for p in synthetic_bases()))
        self.assertEqual(bases, before)

    def test_zero_and_large_integers_have_no_speculative_maximum(self):
        for value in (0, 10**200):
            with self.subTest(value=value):
                result = self.validate(bases=[(code, value) for code in TARGET_STAT_CODES])
                self.assertEqual(tuple(v for _, v in result.bases), (value,) * 6)

    def test_every_missing_attribute_is_rejected(self):
        for index in range(6):
            with self.subTest(index=index), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=synthetic_bases()[:index] + synthetic_bases()[index + 1:])
        with self.assertRaises(InvalidTargetStatsDefinitionStructureError):
            self.validate(bases=[])

    def test_extra_attribute_and_seventh_spe_are_rejected(self):
        for code in ("SPE", "EXTRA", "LOGIC"):
            with self.subTest(code=code), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=synthetic_bases() + [[code, 0]])

    def test_duplicates_are_rejected_before_they_can_be_collapsed(self):
        for index in range(6):
            bases = synthetic_bases()
            bases.insert(index + 1, [bases[index][0], 99])
            with self.subTest(index=index), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=bases)
        bases = synthetic_bases()
        bases[-1] = [bases[0][0], 0]
        with self.assertRaises(InvalidTargetStatsDefinitionStructureError):
            self.validate(bases=bases)

    def test_noncanonical_codes_and_str_subclasses_are_rejected(self):
        class Text(str):
            pass

        for code in ("SPE", "atk", " ATK", "ATK ", "AtK", None, 1, True, Text("ATK")):
            bases = synthetic_bases()
            bases[0][0] = code
            with self.subTest(code=repr(code)), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=bases)

    def test_malformed_pairs_are_rejected(self):
        for pair in ([], ["ATK"], ["ATK", 0, "extra"], "ATK", {"ATK": 0}, None,
                     iter(("ATK", 0)), (item for item in ("ATK", 0))):
            with self.subTest(pair=repr(pair)), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=[pair] + synthetic_bases()[1:])

    def test_incompatible_outer_containers_are_rejected_without_iteration(self):
        for bases in (dict(synthetic_bases()), set(tuple(p) for p in synthetic_bases()),
                      iter(synthetic_bases()), (p for p in synthetic_bases()), "ATK", b"ATK", None):
            with self.subTest(bases=repr(bases)), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=bases)
        def forbidden_iterator():
            raise AssertionError("Iterator must not be consumed")
            yield
        with self.assertRaises(InvalidTargetStatsDefinitionStructureError):
            self.validate(bases=forbidden_iterator())

    def test_container_subclasses_are_rejected(self):
        class Sequence(list):
            pass

        class Pair(tuple):
            pass

        for bases in (Sequence(synthetic_bases()), [Pair(p) for p in synthetic_bases()]):
            with self.subTest(bases=bases), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(bases=bases)

    def test_all_bases_reject_nonexact_nonnegative_integers(self):
        class Number(int):
            pass

        class Convertible:
            def __int__(self):
                raise AssertionError("Must not convert")

        for index in range(6):
            for value in (True, False, -1, 0.0, 1.5, Decimal("2"), Fraction(2, 1),
                          "2", None, Number(2), Convertible()):
                bases = synthetic_bases()
                bases[index][1] = value
                with self.subTest(index=index, value=repr(value)), \
                        self.assertRaises(InvalidTargetStatsDefinitionNumericError):
                    self.validate(bases=bases)

    def test_failed_validation_does_not_mutate_inputs(self):
        for bases in (synthetic_bases()[:-1], synthetic_bases() + [["ATK", 9]],
                      [["ATK", -1]] + synthetic_bases()[1:]):
            before = deepcopy(bases)
            with self.assertRaises(InvalidTargetStatsDefinitionError):
                self.validate(bases=bases)
            self.assertEqual(bases, before)

    def test_snapshot_is_frozen_slotted_and_contains_no_player_budget(self):
        result = self.validate()
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual({f.name for f in fields(result)},
                         {"option_code", "catalog_id", "catalog_version", "definition_version", "bases"})
        with self.assertRaises(FrozenInstanceError):
            result.option_code = "other"
        with self.assertRaises(TypeError):
            result.bases[0][1] = 9

    def test_function_copies_outer_and_inner_mutable_input(self):
        bases = synthetic_bases()
        result = self.validate(bases=bases)
        bases[0][1] = 100
        bases[1].append("extra")
        bases.clear()
        self.assertEqual(result.bases, tuple(tuple(p) for p in synthetic_bases()))

    def test_direct_snapshot_construction_also_validates_and_copies(self):
        bases = list(reversed(synthetic_bases()))
        result = TargetStatsDefinitionSnapshot(**synthetic_definition(bases=bases))
        bases[0][1] = 999
        bases.clear()
        self.assertEqual(result.bases, tuple(tuple(p) for p in synthetic_bases()))
        for changes, error in (({"option_code": " "}, InvalidTargetStatsDefinitionIdentityError),
                               ({"bases": synthetic_bases()[:-1]}, InvalidTargetStatsDefinitionStructureError),
                               ({"bases": synthetic_bases() + [["ATK", 0]]}, InvalidTargetStatsDefinitionStructureError),
                               ({"bases": [["ATK", True]] + synthetic_bases()[1:]}, InvalidTargetStatsDefinitionNumericError)):
            with self.subTest(changes=changes), self.assertRaises(error):
                TargetStatsDefinitionSnapshot(**synthetic_definition(**changes))

    def test_direct_snapshot_validates_every_identity(self):
        for name in ("option_code", "catalog_id", "catalog_version", "definition_version"):
            with self.subTest(name=name), self.assertRaises(InvalidTargetStatsDefinitionIdentityError):
                TargetStatsDefinitionSnapshot(**synthetic_definition(**{name: None}))

    def test_optional_context_absent_or_matching(self):
        absent = self.validate(expected_catalog=None)
        matching = self.validate(expected_catalog=TargetStatsCatalogContext("synthetic-catalog", "catalog-r2"))
        self.assertEqual(absent, matching)

    def test_each_context_dimension_has_specific_mismatch_error(self):
        for context in (TargetStatsCatalogContext("different", "catalog-r2"),
                        TargetStatsCatalogContext("synthetic-catalog", "different")):
            with self.subTest(context=context), self.assertRaises(TargetStatsDefinitionCatalogMismatchError):
                self.validate(expected_catalog=context)

    def test_context_comparison_does_not_trim_or_casefold(self):
        for catalog_id in (" synthetic-catalog", "SYNTHETIC-CATALOG"):
            with self.subTest(catalog_id=catalog_id), self.assertRaises(TargetStatsDefinitionCatalogMismatchError):
                self.validate(expected_catalog=TargetStatsCatalogContext(catalog_id, "catalog-r2"))

    def test_incompatible_context_type_and_subclass_are_rejected(self):
        class DerivedContext(TargetStatsCatalogContext):
            pass

        for context in ({"catalog_id": "synthetic-catalog", "catalog_version": "catalog-r2"},
                        False, "catalog-r2", SimpleNamespace(catalog_id="synthetic-catalog"),
                        DerivedContext("synthetic-catalog", "catalog-r2")):
            with self.subTest(context=context), self.assertRaises(InvalidTargetStatsDefinitionStructureError):
                self.validate(expected_catalog=context)

    def test_direct_context_construction_rejects_invalid_identities(self):
        class Text(str):
            pass

        for field in ("catalog_id", "catalog_version"):
            for value in (None, "", " \t", 1, True, Text("catalog")):
                values = dict(catalog_id="synthetic-catalog", catalog_version="catalog-r2") | {field: value}
                with self.subTest(field=field, value=repr(value)), \
                        self.assertRaises(InvalidTargetStatsDefinitionIdentityError):
                    TargetStatsCatalogContext(**values)

    def test_context_is_frozen_slotted_and_not_an_authority_flag(self):
        context = TargetStatsCatalogContext(" synthetic-catalog ", " r2 ")
        self.assertEqual((context.catalog_id, context.catalog_version), (" synthetic-catalog ", " r2 "))
        self.assertEqual({f.name for f in fields(context)}, {"catalog_id", "catalog_version"})
        self.assertFalse(hasattr(context, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            context.catalog_version = "r3"

    def test_supplied_context_fields_are_revalidated(self):
        context = TargetStatsCatalogContext("synthetic-catalog", "catalog-r2")
        object.__setattr__(context, "catalog_version", None)
        with self.assertRaises(InvalidTargetStatsDefinitionIdentityError):
            self.validate(expected_catalog=context)

    def test_two_options_and_versions_are_independent_and_deterministic(self):
        first = self.validate()
        other = self.validate(option_code="synthetic-other", definition_version="stats-r8",
                              bases=[(code, 0) for code in TARGET_STAT_CODES])
        other_catalog = self.validate(catalog_version="catalog-r3")
        self.assertNotEqual(first, other)
        self.assertNotEqual(first, other_catalog)
        self.assertEqual(self.validate(), first)
        self.assertEqual(other.bases, tuple((code, 0) for code in TARGET_STAT_CODES))

    def test_interoperability_with_a41_requires_explicit_separate_budget(self):
        definition = self.validate()
        increments = [(code, 1) for code in TARGET_STAT_CODES]
        result = validate_target_stats(definition.bases, increments, budget=8)
        self.assertEqual(result.bases, definition.bases)
        self.assertEqual(result.effective, tuple((code, value + 1) for code, value in definition.bases))
        self.assertEqual((result.points_used, result.points_remaining), (6, 2))
        self.assertFalse(hasattr(definition, "budget"))

    def test_minimal_value_error_hierarchy_and_safe_messages(self):
        errors = (InvalidTargetStatsDefinitionIdentityError, InvalidTargetStatsDefinitionStructureError,
                  InvalidTargetStatsDefinitionNumericError, TargetStatsDefinitionCatalogMismatchError)
        self.assertTrue(issubclass(InvalidTargetStatsDefinitionError, ValueError))
        for error in errors:
            self.assertTrue(issubclass(error, InvalidTargetStatsDefinitionError))
        private_id = "synthetic-private-identifier"
        with self.assertRaises(TargetStatsDefinitionCatalogMismatchError) as caught:
            self.validate(catalog_id=private_id,
                          expected_catalog=TargetStatsCatalogContext("other", "catalog-r2"))
        self.assertNotIn(private_id, str(caught.exception))

    def test_no_external_access_or_clock_during_validation(self):
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError), \
                patch("time.time", side_effect=AssertionError):
            self.assertEqual(self.validate(), self.validate())

    def test_imports_and_public_api_exclude_orm_and_private_a41_helpers(self):
        tree = ast.parse(Path(definitions.__file__).read_text(encoding="utf-8"))
        imports = [(node.module, tuple(name.name for name in node.names))
                   for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertEqual(imports, [("dataclasses", ("dataclass",)),
                                   ("target_stats_validation", ("TARGET_STAT_CODES",))])
        self.assertFalse(any(isinstance(node, ast.Import) for node in tree.body))
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef)
                          and not node.name.startswith("_")], ["validate_target_stats_definition"])

    def test_no_calls_to_s3_or_other_domain_services(self):
        names = {"apps.ecomotor.xp_service": "grant_historical_xp",
                 "apps.ecomotor.stat_allocation": "allocate_stat_points",
                 "apps.ecomotor.specialization_service": "select_initial_specialization",
                 "apps.ecomotor.target_catalog_validation": "validate_target_level_epoch_catalog",
                 "apps.ecomotor.profile_classification_rules": "evaluate_classification_rules"}
        stubs = {module: SimpleNamespace(**{name: Mock(side_effect=AssertionError)})
                 for module, name in names.items()}
        with patch.dict(sys.modules, stubs):
            self.validate()
        for module, name in names.items():
            getattr(stubs[module], name).assert_not_called()

    def test_import_and_execution_without_django_configuration(self):
        code = (
            "import sys; sys.path.insert(0,sys.argv[1]); "
            "from apps.ecomotor.target_stats_config_validation import *; "
            "from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES; "
            "b=[(c,0) for c in TARGET_STAT_CODES]; "
            "r=validate_target_stats_definition(option_code='synthetic',catalog_id='c',"
            "catalog_version='v1',definition_version='different',bases=b,"
            "expected_catalog=TargetStatsCatalogContext('c','v1')); "
            "assert r.bases==tuple(b); "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules); "
            "assert not any(n.startswith('apps.ecomotor.') and n not in "
            "('apps.ecomotor.target_stats_validation','apps.ecomotor.target_stats_config_validation') "
            "for n in sys.modules)"
        )
        env = {key: value for key, value in os.environ.items() if key != "DJANGO_SETTINGS_MODULE"}
        completed = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                   env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
