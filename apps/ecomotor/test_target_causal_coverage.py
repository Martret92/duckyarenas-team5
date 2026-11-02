"""INT-A2-T05-C1: synthetic catalogs and supplied observations; no database."""

from dataclasses import FrozenInstanceError, asdict
from unittest import TestCase
from unittest.mock import patch

from . import target_progression
from .target_causal_coverage import (
    CausalCoverageIssue, CausalCoverageIssueCode, CausalCoverageStatus,
    InvalidCausalObservationError, TargetCausalCoverageResult,
    compare_target_causal_coverage,
)
from .test_target_progression import synthetic_catalog


class TargetCausalCoverageTests(TestCase):
    def setUp(self):
        self.catalog = synthetic_catalog()
        self.codes = self.catalog.ordered_epoch_codes

    def diagnose(self, before, after, observed):
        return compare_target_causal_coverage(before, after, self.catalog, observed)

    def test_zero_crossings_with_explicitly_empty_observation(self):
        result = self.diagnose(0, 1, ())
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MATCH)
        self.assertEqual((result.expected_epoch_codes, result.observed_epoch_codes, result.issues),
                         ((), (), ()))
        self.assertIn("HISTORICAL_CAUSAL_COVERAGE_NOT_CERTIFIED", result.evidence_limits)

    def test_single_epoch_exact_match(self):
        threshold = self.catalog.levels[3].minimum_xp
        result = self.diagnose(threshold - 1, threshold, (self.codes[3],))
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MATCH)
        self.assertEqual(result.expected_epoch_codes, (self.codes[3],))
        self.assertEqual(result.catalog_version, self.catalog.catalog_version)

    def test_six_crossings_with_no_eighth_epoch(self):
        result = self.diagnose(0, self.catalog.levels[7].minimum_xp, self.codes[1:])
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MATCH)
        self.assertEqual(result.expected_epoch_codes, self.codes[1:])
        self.assertEqual(len(result.expected_epoch_codes), 6)

    def test_missing_epoch_is_diagnosed_not_silently_accepted(self):
        expected = self.codes[1:4]
        result = self.diagnose(0, self.catalog.levels[3].minimum_xp, (expected[0], expected[2]))
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MISMATCH)
        self.assertEqual(result.issues, (
            CausalCoverageIssue(CausalCoverageIssueCode.MISSING_EPOCH, expected[1]),
        ))

    def test_additional_known_epoch_is_not_labeled_unknown(self):
        result = self.diagnose(0, 1, (self.codes[1],))
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MISMATCH)
        self.assertEqual(result.issues, (
            CausalCoverageIssue(CausalCoverageIssueCode.ADDITIONAL_EPOCH, self.codes[1]),
        ))

    def test_duplicate_epoch_reports_both_duplicate_and_additional(self):
        threshold = self.catalog.levels[1].minimum_xp
        result = self.diagnose(0, threshold, (self.codes[1], self.codes[1]))
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MISMATCH)
        self.assertEqual(result.issues, (
            CausalCoverageIssue(CausalCoverageIssueCode.ADDITIONAL_EPOCH, self.codes[1]),
            CausalCoverageIssue(CausalCoverageIssueCode.DUPLICATE_EPOCH, self.codes[1]),
        ))

    def test_wrong_order_is_reported_only_when_multiset_matches(self):
        result = self.diagnose(0, self.catalog.levels[2].minimum_xp,
                               (self.codes[2], self.codes[1]))
        self.assertEqual(result.issues, (CausalCoverageIssue(CausalCoverageIssueCode.WRONG_ORDER),))
        result_with_missing = self.diagnose(0, self.catalog.levels[2].minimum_xp, (self.codes[2],))
        self.assertNotIn(CausalCoverageIssueCode.WRONG_ORDER,
                         {issue.code for issue in result_with_missing.issues})

    def test_foreign_code_is_additional_and_unknown(self):
        result = self.diagnose(0, self.catalog.levels[1].minimum_xp,
                               (self.codes[1], "not-in-historical-catalog"))
        self.assertEqual(result.status, CausalCoverageStatus.OBSERVED_MISMATCH)
        self.assertEqual(result.issues, (
            CausalCoverageIssue(CausalCoverageIssueCode.ADDITIONAL_EPOCH, "not-in-historical-catalog"),
            CausalCoverageIssue(CausalCoverageIssueCode.UNKNOWN_EPOCH, "not-in-historical-catalog"),
        ))

    def test_missing_observation_is_not_an_empty_observation(self):
        result = self.diagnose(0, self.catalog.levels[7].minimum_xp, None)
        self.assertEqual(result.status, CausalCoverageStatus.EVIDENCE_UNAVAILABLE)
        self.assertIsNone(result.observed_epoch_codes)
        self.assertEqual(result.expected_epoch_codes, self.codes[1:])
        self.assertEqual(result.issues, (CausalCoverageIssue(CausalCoverageIssueCode.EVIDENCE_UNAVAILABLE),))
        empty = self.diagnose(0, self.catalog.levels[7].minimum_xp, ())
        self.assertEqual(empty.status, CausalCoverageStatus.OBSERVED_MISMATCH)
        self.assertEqual(len(empty.issues), 6)
        self.assertTrue(all(issue.code is CausalCoverageIssueCode.MISSING_EPOCH for issue in empty.issues))

    def test_matching_observations_still_cannot_prove_historical_completeness(self):
        match = self.diagnose(0, self.catalog.levels[1].minimum_xp, (self.codes[1],))
        unavailable = self.diagnose(0, self.catalog.levels[1].minimum_xp, None)
        self.assertEqual(match.evidence_limits, unavailable.evidence_limits)
        self.assertIn("OBSERVATION_SOURCE_AND_COMPLETENESS_UNVERIFIED", match.evidence_limits)
        self.assertIn("OBSERVATION_ORDER_NOT_HISTORICALLY_ATTESTED", match.evidence_limits)
        self.assertIn("PERSISTED_CAUSE_PROFILE_AND_CATALOG_NOT_VERIFIED", match.evidence_limits)
        self.assertNotIn("COMPLETE", match.status.value)

    def test_invalid_inputs_are_not_coerced_or_sorted(self):
        invalid = ("epoch", b"epoch", {self.codes[1]}, iter((self.codes[1],)),
                   [1], [True], [None], [""], ["  "], [[self.codes[1]]],
                   {"epoch": self.codes[1]})
        for observed in invalid:
            with self.subTest(kind=type(observed)), self.assertRaises(InvalidCausalObservationError):
                self.diagnose(0, 1, observed)
        for before, after in ((True, 1), (-1, 1), (1, 0)):
            with self.subTest(before=before, after=after), self.assertRaises(
                    target_progression.InvalidTargetXPError):
                self.diagnose(before, after, ())
        with self.assertRaises(target_progression.InvalidTargetCatalogError):
            compare_target_causal_coverage(0, 1, None, ())

    def test_delegates_crossings_once_to_a12_not_v1_or_second_algorithm(self):
        original = target_progression.calculate_target_progression
        with patch("apps.ecomotor.target_causal_coverage.calculate_target_progression", wraps=original) as call, \
                patch("apps.ecomotor.progression.calculate_progression", side_effect=AssertionError):
            result = self.diagnose(0, self.catalog.levels[7].minimum_xp, self.codes[1:])
        call.assert_called_once_with(0, self.catalog.levels[7].minimum_xp, self.catalog)
        self.assertEqual(result.expected_epoch_codes, original(0, self.catalog.levels[7].minimum_xp,
                                                               self.catalog).crossed_epoch_codes)

    def test_result_copies_observations_and_is_deeply_immutable(self):
        observed = [self.codes[1]]
        result = self.diagnose(0, self.catalog.levels[1].minimum_xp, observed)
        observed.clear()
        self.assertIs(type(result), TargetCausalCoverageResult)
        self.assertEqual(result.observed_epoch_codes, (self.codes[1],))
        with self.assertRaises(FrozenInstanceError):
            result.status = CausalCoverageStatus.OBSERVED_MISMATCH
        with self.assertRaises(FrozenInstanceError):
            result.issues = ()
        self.assertIsInstance(result.issues, tuple)
        self.assertIsInstance(result.evidence_limits, tuple)
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertNotIn("profile_id", asdict(result))
        self.assertNotIn("operation_key", asdict(result))

    def test_no_database_network_or_writes(self):
        with patch("builtins.open", side_effect=AssertionError), \
                patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError):
            self.assertEqual(self.diagnose(0, 1, ()).status, CausalCoverageStatus.OBSERVED_MATCH)
