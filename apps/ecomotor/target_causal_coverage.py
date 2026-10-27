"""INT-A2-T05-C1: compare supplied epoch observations with A1.2 crossings.

This is a pure sequence diagnostic, not proof that any event, cause, profile,
catalog version, or complete historical query exists in persistent storage.
The caller must independently establish those facts before using the result.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from .target_progression import calculate_target_progression


class InvalidCausalObservationError(ValueError):
    """The supplied observation is neither absent nor an explicit code sequence."""


class CausalCoverageStatus(str, Enum):
    OBSERVED_MATCH = "OBSERVED_MATCH"
    OBSERVED_MISMATCH = "OBSERVED_MISMATCH"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"


class CausalCoverageIssueCode(str, Enum):
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    MISSING_EPOCH = "MISSING_EPOCH"
    ADDITIONAL_EPOCH = "ADDITIONAL_EPOCH"
    DUPLICATE_EPOCH = "DUPLICATE_EPOCH"
    UNKNOWN_EPOCH = "UNKNOWN_EPOCH"
    WRONG_ORDER = "WRONG_ORDER"


@dataclass(frozen=True, slots=True)
class CausalCoverageIssue:
    code: CausalCoverageIssueCode
    epoch_code: str | None = None


@dataclass(frozen=True, slots=True)
class TargetCausalCoverageResult:
    catalog_version: str
    status: CausalCoverageStatus
    expected_epoch_codes: tuple[str, ...]
    observed_epoch_codes: tuple[str, ...] | None
    issues: tuple[CausalCoverageIssue, ...]
    evidence_limits: tuple[str, ...]


_EVIDENCE_LIMITS = (
    "OBSERVATION_SOURCE_AND_COMPLETENESS_UNVERIFIED",
    "OBSERVATION_ORDER_NOT_HISTORICALLY_ATTESTED",
    "PERSISTED_CAUSE_PROFILE_AND_CATALOG_NOT_VERIFIED",
    "HISTORICAL_CAUSAL_COVERAGE_NOT_CERTIFIED",
)


def _observations(values):
    # None means not supplied, whereas () is an explicitly empty observation.
    if values is None:
        return None
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise InvalidCausalObservationError("An ordered sequence of epoch codes is required.")
    copied = tuple(values)
    if any(type(code) is not str or not code.strip() for code in copied):
        raise InvalidCausalObservationError("Epoch codes must be nonempty exact strings.")
    return copied


def compare_target_causal_coverage(xp_before, xp_after, catalog, observed_epoch_codes):
    """Diagnose a supplied sequence, delegating all crossing calculation to A1.2.

    Missing/additional codes use multiplicity, so duplicates are not hidden.
    Wrong order is reported only when multisets agree, to avoid attributing a
    sequence mismatch to order while elements are missing or extra. Any exact
    match describes only the supplied observation, never historical completeness.
    """
    observed = _observations(observed_epoch_codes)
    progression = calculate_target_progression(xp_before, xp_after, catalog)
    expected = progression.crossed_epoch_codes

    if observed is None:
        return TargetCausalCoverageResult(
            progression.catalog_version, CausalCoverageStatus.EVIDENCE_UNAVAILABLE,
            expected, None,
            (CausalCoverageIssue(CausalCoverageIssueCode.EVIDENCE_UNAVAILABLE),),
            _EVIDENCE_LIMITS,
        )

    expected_counts = Counter(expected)
    observed_counts = Counter(observed)
    valid_codes = set(catalog.ordered_epoch_codes)
    issues = []
    for code in dict.fromkeys(expected):
        if observed_counts[code] < expected_counts[code]:
            issues.append(CausalCoverageIssue(CausalCoverageIssueCode.MISSING_EPOCH, code))
    for code in dict.fromkeys(observed):
        if observed_counts[code] > expected_counts[code]:
            issues.append(CausalCoverageIssue(CausalCoverageIssueCode.ADDITIONAL_EPOCH, code))
        if observed_counts[code] > 1:
            issues.append(CausalCoverageIssue(CausalCoverageIssueCode.DUPLICATE_EPOCH, code))
        if code not in valid_codes:
            issues.append(CausalCoverageIssue(CausalCoverageIssueCode.UNKNOWN_EPOCH, code))
    if expected_counts == observed_counts and expected != observed:
        issues.append(CausalCoverageIssue(CausalCoverageIssueCode.WRONG_ORDER))

    return TargetCausalCoverageResult(
        progression.catalog_version,
        CausalCoverageStatus.OBSERVED_MISMATCH if issues else CausalCoverageStatus.OBSERVED_MATCH,
        expected, observed, tuple(issues), _EVIDENCE_LIMITS,
    )
