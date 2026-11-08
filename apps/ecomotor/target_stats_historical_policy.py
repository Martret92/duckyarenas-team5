"""Pure candidate policy for the seven historical target epochs (A4-45+5).

The 50-point originals were recovered from earlier project context, not from a
located primary source. Neither these values nor their calculated 45-point bases
are official or published catalog definitions. No persistence or authorization.
"""

from dataclasses import dataclass

from .target_stats_validation import (
    TARGET_STAT_CODES,
    TargetStatsResult,
    validate_target_stats,
)

# This order is for the Hamilton *tie break*, not the A4 result representation.
HISTORICAL_TABLE_ORDER = ("ATK", "DEF", "LOG", "VEL", "INT", "ESP")
HISTORICAL_ORIGINAL_TOTAL = 50
HISTORICAL_BASE_TOTAL = 45
HISTORICAL_ALLOCATION_BUDGET = 5

# Exact internal witnesses recovered for the seven historical epochs; values are
# in HISTORICAL_TABLE_ORDER, never in the different A4 canonical order.
_HISTORICAL_ORIGINALS_50 = (
    ("Prehistoria", (13, 8, 5, 12, 4, 8)),
    ("Grecia", (7, 8, 12, 7, 11, 5)),
    ("Roma", (11, 14, 7, 6, 7, 5)),
    ("Medieval", (12, 11, 5, 7, 5, 10)),
    ("Renacimiento", (7, 7, 11, 8, 13, 4)),
    ("Revolución Industrial", (8, 9, 10, 9, 8, 6)),
    ("Siglo XX", (10, 8, 9, 11, 8, 4)),
)


class HistoricalPolicyError(ValueError):
    """Invalid historical-policy request, unrelated to source authorization."""


class InvalidHistoricalEpochError(HistoricalPolicyError):
    """Epoch label is not one of the seven exact internal labels."""


class InvalidHistoricalVectorError(HistoricalPolicyError):
    """Structurally valid original does not have exactly 50 points."""


def derive_historical_bases_45(original_50):
    """Hamilton 50→45 with exact integers and historical-order tie-breaking.

    Input is an explicit list/tuple of six (code, int) pairs in any order.
    A4.1 rejects invalid shapes, duplicate/unknown codes and numeric values.
    The immutable return value is ordered by A4, never the historical table.
    """
    zero = tuple((code, 0) for code in TARGET_STAT_CODES)
    checked = validate_target_stats(original_50, zero, budget=0)
    values = dict(checked.bases)
    if sum(values.values()) != HISTORICAL_ORIGINAL_TOTAL:
        raise InvalidHistoricalVectorError("A historical original must total exactly 50 points.")

    quotients = {code: divmod(9 * values[code], 10) for code in HISTORICAL_TABLE_ORDER}
    allocated = {code: quotients[code][0] for code in HISTORICAL_TABLE_ORDER}
    missing = HISTORICAL_BASE_TOTAL - sum(allocated.values())
    priority = sorted(HISTORICAL_TABLE_ORDER,
                      key=lambda code: (-quotients[code][1], HISTORICAL_TABLE_ORDER.index(code)))
    for code in priority[:missing]:
        allocated[code] += 1
    return tuple((code, allocated[code]) for code in TARGET_STAT_CODES)


def _epoch_original(epoch_name):
    if type(epoch_name) is not str:
        raise InvalidHistoricalEpochError("An exact historical epoch label is required.")
    for name, values in _HISTORICAL_ORIGINALS_50:
        if epoch_name == name:
            return tuple(zip(HISTORICAL_TABLE_ORDER, values))
    raise InvalidHistoricalEpochError("Unknown historical epoch; no aliases are allowed.")


def historical_epoch_bases_45(epoch_name):
    """Immutable candidate bases, calculated from that epoch's 50-point vector."""
    return derive_historical_bases_45(_epoch_original(epoch_name))


@dataclass(frozen=True, slots=True)
class HistoricalEpochAllocation:
    """Pure, independent epoch calculation; neither published nor persisted."""

    epoch_name: str
    calculation: TargetStatsResult

    def __post_init__(self):
        expected_bases = historical_epoch_bases_45(self.epoch_name)
        if type(self.calculation) is not TargetStatsResult:
            raise HistoricalPolicyError("An exact A4 statistics result is required.")
        # Rebuild even on direct construction: reject forged derived values and
        # keep no references to mutable input collections.
        checked = validate_target_stats(self.calculation.bases,
                                        self.calculation.increments,
                                        budget=HISTORICAL_ALLOCATION_BUDGET)
        if checked.bases != expected_bases or checked != self.calculation:
            raise HistoricalPolicyError("Allocation contradicts the selected epoch or its budget.")
        object.__setattr__(self, "calculation", checked)


def prepare_historical_epoch_allocation(*, epoch_name, increments):
    """Allocate 0–5 independent points to one epoch via public pure A4.1."""
    bases = historical_epoch_bases_45(epoch_name)
    calculation = validate_target_stats(bases, increments,
                                        budget=HISTORICAL_ALLOCATION_BUDGET)
    return HistoricalEpochAllocation(epoch_name, calculation)
