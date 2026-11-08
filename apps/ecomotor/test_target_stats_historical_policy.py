"""Pure unit tests for internally approved 45-base + 5-point epoch candidates."""

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
import inspect
from pathlib import Path
import subprocess
import sys
from unittest import TestCase
from unittest.mock import patch

from . import target_stats_historical_policy as policy
from . import target_stats_validation as a4


# Independent expectations in HISTORICAL TABLE ORDER, not A4 order. These
# original inputs were recovered from earlier project context; source unknown.
ORIGINALS_AND_EXPECTED_45 = (
    ("Prehistoria", (13, 8, 5, 12, 4, 8), (12, 7, 4, 11, 4, 7)),
    ("Grecia", (7, 8, 12, 7, 11, 5), (6, 7, 11, 6, 10, 5)),
    ("Roma", (11, 14, 7, 6, 7, 5), (10, 13, 6, 5, 6, 5)),
    ("Medieval", (12, 11, 5, 7, 5, 10), (11, 10, 5, 6, 4, 9)),
    ("Renacimiento", (7, 7, 11, 8, 13, 4), (6, 6, 10, 7, 12, 4)),
    ("Revolución Industrial", (8, 9, 10, 9, 8, 6), (7, 8, 9, 8, 7, 6)),
    ("Siglo XX", (10, 8, 9, 11, 8, 4), (9, 7, 8, 10, 7, 4)),
)


def table_pairs(values):
    return list(zip(("ATK", "DEF", "LOG", "VEL", "INT", "ESP"), values))


def a4_pairs(values):
    return tuple(zip(("ATK", "DEF", "VEL", "INT", "LOG", "ESP"), values))


class HistoricalHamiltonTests(TestCase):
    def test_all_seven_recovered_originals_and_approved_45_results(self):
        for name, original, approved in ORIGINALS_AND_EXPECTED_45:
            with self.subTest(epoch=name):
                self.assertEqual(sum(original), 50)
                self.assertEqual(sum(approved), 45)
                expected_by_code = dict(table_pairs(approved))
                expected = tuple((code, expected_by_code[code]) for code in a4.TARGET_STAT_CODES)
                self.assertEqual(policy.derive_historical_bases_45(table_pairs(original)), expected)
                self.assertEqual(policy.historical_epoch_bases_45(name), expected)
                self.assertEqual(sum(v for _, v in expected), 45)

    def test_table_order_and_a4_order_are_distinct(self):
        self.assertEqual(policy.HISTORICAL_TABLE_ORDER, ("ATK", "DEF", "LOG", "VEL", "INT", "ESP"))
        self.assertEqual(a4.TARGET_STAT_CODES, ("ATK", "DEF", "VEL", "INT", "LOG", "ESP"))
        result = policy.historical_epoch_bases_45("Grecia")
        self.assertEqual(result, a4_pairs((6, 7, 6, 10, 11, 5)))

    def test_hamilton_log_vel_tie_uses_table_order(self):
        source = table_pairs((10, 10, 5, 5, 10, 10))
        result = policy.derive_historical_bases_45(source)
        self.assertEqual(result, a4_pairs((9, 9, 4, 9, 5, 9)))
        self.assertNotEqual(dict(result)["LOG"], dict(result)["VEL"])

    def test_any_equal_remainder_tie_follows_historical_priority(self):
        codes = policy.HISTORICAL_TABLE_ORDER
        for index in range(5):
            values = [10] * 6
            values[index] = values[index + 1] = 5
            expected = [9] * 6
            expected[index], expected[index + 1] = 5, 4
            result = dict(policy.derive_historical_bases_45(table_pairs(values)))
            with self.subTest(index=index):
                self.assertEqual(tuple(result[code] for code in codes), tuple(expected))

    def test_concentrated_vector_rounds_exactly(self):
        for index in range(6):
            vector = [0] * 6
            vector[index] = 50
            result = dict(policy.derive_historical_bases_45(table_pairs(vector)))
            with self.subTest(index=index):
                self.assertEqual(result[policy.HISTORICAL_TABLE_ORDER[index]], 45)
                self.assertEqual(sum(result.values()), 45)

    def test_reordered_and_repeated_inputs_return_same_result(self):
        original = [list(pair) for pair in table_pairs(ORIGINALS_AND_EXPECTED_45[0][1])]
        unchanged = deepcopy(original)
        first = policy.derive_historical_bases_45(original)
        self.assertEqual(first, policy.derive_historical_bases_45(list(reversed(original))))
        self.assertEqual(first, policy.derive_historical_bases_45(original))
        self.assertEqual(original, unchanged)
        original[0][1] = 999
        self.assertEqual(first[0], ("ATK", 12))
        self.assertIs(type(first), tuple)
        self.assertTrue(all(type(pair) is tuple for pair in first))

    def test_wrong_total_rejected_without_mutation(self):
        for vector in ((49, 0, 0, 0, 0, 0), (51, 0, 0, 0, 0, 0)):
            original = [list(pair) for pair in table_pairs(vector)]
            before = deepcopy(original)
            with self.subTest(total=sum(vector)), self.assertRaises(policy.InvalidHistoricalVectorError):
                policy.derive_historical_bases_45(original)
            self.assertEqual(original, before)

    def test_strict_structure_and_unknown_codes(self):
        original = table_pairs(ORIGINALS_AND_EXPECTED_45[0][1])
        bad_vectors = (original[:-1], original + [("ESP", 0)],
                       original[:-1] + [("ATK", 8)],
                       [("CUACK", 13)] + original[1:],
                       [("SPE", 13)] + original[1:],
                       [("esp", 13)] + original[1:],
                       [("EXTRA", 13)] + original[1:],
                       dict(original), iter(original), None,
                       [("ATK", 13, 0)] + original[1:])
        for bad in bad_vectors:
            with self.subTest(bad=repr(bad)), self.assertRaises(a4.InvalidTargetStatsStructureError):
                policy.derive_historical_bases_45(bad)

    def test_strict_numbers_including_bools_and_subclasses(self):
        class IntSubclass(int):
            pass
        for value in (-1, True, False, 0.0, 1.0, Fraction(1), Decimal(1), "1", None, IntSubclass(1)):
            original = table_pairs(ORIGINALS_AND_EXPECTED_45[0][1])
            original[0] = ("ATK", value)
            with self.subTest(value=repr(value)), self.assertRaises(a4.InvalidTargetStatsNumericError):
                policy.derive_historical_bases_45(original)

    def test_epoch_labels_exact_no_aliases(self):
        for name in (None, True, 1, "", "prehistoria", "Prehistórico", "Grecia ", "Greece", "Gamer"):
            with self.subTest(name=repr(name)), self.assertRaises(policy.InvalidHistoricalEpochError):
                policy.historical_epoch_bases_45(name)


class HistoricalAllocationTests(TestCase):
    def test_zero_one_three_five_points_and_effectives(self):
        choices = (((0, 0, 0, 0, 0, 0), 0), ((0, 0, 0, 0, 0, 1), 1),
                   ((1, 0, 0, 2, 0, 0), 3), ((1, 0, 2, 2, 0, 0), 5))
        bases = dict(policy.historical_epoch_bases_45("Roma"))
        for increments, spent in choices:
            with self.subTest(spent=spent):
                actual = policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs(increments))
                c = actual.calculation
                self.assertEqual(actual.epoch_name, "Roma")
                self.assertEqual((c.budget, c.points_used, c.points_remaining), (5, spent, 5 - spent))
                self.assertEqual(sum(value for _, value in c.effective), 45 + spent)
                self.assertEqual(dict(c.effective), {code: bases[code] + inc for code, inc in a4_pairs(increments)})

    def test_six_points_rejected_by_existing_a4_error(self):
        with self.assertRaises(a4.TargetStatsBudgetExceededError):
            policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 6)))

    def test_allocation_rejects_bad_codes_and_numeric_types(self):
        for code in ("CUACK", "SPE", "EXTRA", "esp"):
            values = list(a4_pairs((0, 0, 0, 0, 0, 0)))
            values[-1] = (code, 0)
            with self.subTest(code=code), self.assertRaises(a4.InvalidTargetStatsStructureError):
                policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=values)
        for invalid in (-1, True, 1.0, "1", None):
            values = list(a4_pairs((0, 0, 0, 0, 0, 0)))
            values[-1] = ("ESP", invalid)
            with self.subTest(value=repr(invalid)), self.assertRaises(a4.InvalidTargetStatsNumericError):
                policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=values)

    def test_result_is_frozen_and_defensively_copied(self):
        values = [list(pair) for pair in a4_pairs((0, 0, 0, 0, 0, 3))]
        before = deepcopy(values)
        result = policy.prepare_historical_epoch_allocation(epoch_name="Grecia", increments=values)
        self.assertEqual(values, before)
        with self.assertRaises(FrozenInstanceError):
            result.epoch_name = "Roma"
        with self.assertRaises(FrozenInstanceError):
            result.calculation = None
        values[-1][1] = 5
        self.assertEqual(result.calculation.points_used, 3)
        self.assertIs(type(result.calculation.increments), tuple)

    def test_direct_construction_rejects_wrong_epoch_bases(self):
        result = policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 0)))
        with self.assertRaises(policy.HistoricalPolicyError):
            policy.HistoricalEpochAllocation("Grecia", result.calculation)

    def test_direct_construction_rejects_wrong_budget(self):
        bases = policy.historical_epoch_bases_45("Roma")
        c = a4.validate_target_stats(bases, a4_pairs((0, 0, 0, 0, 0, 0)), budget=45)
        with self.assertRaises(policy.HistoricalPolicyError):
            policy.HistoricalEpochAllocation("Roma", c)

    def test_direct_construction_rejects_wrong_type_and_bad_epoch(self):
        result = policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 0)))
        with self.assertRaises(policy.HistoricalPolicyError):
            policy.HistoricalEpochAllocation("Roma", None)
        with self.assertRaises(policy.InvalidHistoricalEpochError):
            policy.HistoricalEpochAllocation("roma", result.calculation)

    def test_direct_construction_rejects_contradictory_derived_values(self):
        result = policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 1)))
        # A caller can explicitly bypass A4's dataclass constructor; the epoch
        # policy still must not accept forged or contradictory derived fields.
        fake = object.__new__(a4.TargetStatsResult)
        for field in ("bases", "increments", "effective", "budget", "points_used", "points_remaining"):
            object.__setattr__(fake, field, getattr(result.calculation, field))
        object.__setattr__(fake, "points_remaining", 5)
        with self.assertRaises(policy.HistoricalPolicyError):
            policy.HistoricalEpochAllocation("Roma", fake)

    def test_seven_epochs_are_independent(self):
        early = policy.prepare_historical_epoch_allocation(epoch_name="Prehistoria", increments=a4_pairs((3, 0, 0, 0, 0, 0)))
        later = policy.prepare_historical_epoch_allocation(epoch_name="Grecia", increments=a4_pairs((0, 0, 0, 0, 0, 5)))
        third = policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 0)))
        self.assertEqual((early.calculation.points_remaining, later.calculation.points_remaining,
                          third.calculation.points_remaining), (2, 0, 5))
        self.assertNotEqual(early.calculation.bases, later.calculation.bases)
        self.assertEqual(early.calculation.points_used, 3)

    def test_a4_delegation_is_explicit_and_budget_five(self):
        original = a4.validate_target_stats
        with patch.object(policy, "validate_target_stats", wraps=original) as spy:
            policy.prepare_historical_epoch_allocation(epoch_name="Roma", increments=a4_pairs((0, 0, 0, 0, 0, 0)))
        self.assertTrue(any(kwargs.get("budget") == 5 for _, kwargs in spy.call_args_list))

    def test_does_not_touch_django_or_database_or_services(self):
        text = inspect.getsource(policy)
        tree = ast.parse(text)
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertEqual(imports, ["dataclasses", "target_stats_validation"])
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))
        for forbidden in ("django", "sqlite3", "transaction", ".objects", "open(", "services", "rewards"):
            self.assertNotIn(forbidden, text.lower())

    def test_isolated_interpreter_without_django(self):
        root = str(Path(__file__).resolve().parents[2])
        script = "\n".join((
            "import sys",
            f"sys.path.insert(0, {root!r})",
            "from apps.ecomotor.target_stats_historical_policy import historical_epoch_bases_45",
            "assert historical_epoch_bases_45('Roma') == (('ATK',10),('DEF',13),('VEL',5),('INT',6),('LOG',6),('ESP',5))",
            "assert not any(k == 'django' or k.startswith('django.') for k in sys.modules)",
        ))
        process = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
