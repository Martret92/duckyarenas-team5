"""A4.1: pure target stats validation, not configuration authorization.

NUM-01: exact nonnegative Python integers, without gameplay/storage maxima.
Each invocation concerns one independent configuration; no global balance, XP,
option selection, persistence or reinterpretation of V1 log_stat/spe data.
Explicit lists/tuples of pairs preserve duplicates until they can be rejected.
Duplicates discarded upstream cannot be detected retrospectively.
"""

from dataclasses import dataclass


TARGET_STAT_CODES = ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")


class InvalidTargetStatsError(ValueError):
    """Base error for invalid target statistics inputs or derived invariants."""


class InvalidTargetStatsStructureError(InvalidTargetStatsError):
    """Invalid pair representation, attribute coverage or duplicate code."""


class InvalidTargetStatsNumericError(InvalidTargetStatsError):
    """Not an exact nonnegative integer, or contradictory calculated values."""


class TargetStatsBudgetExceededError(InvalidTargetStatsError):
    """The sum of increments exceeds this configuration's explicit budget."""


def _number(value):
    if type(value) is not int or value < 0:
        raise InvalidTargetStatsNumericError("An exact nonnegative integer is required.")


def _pairs(values):
    if type(values) not in (list, tuple):
        raise InvalidTargetStatsStructureError("An explicit list or tuple of pairs is required.")
    observed = {}
    for pair in values:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise InvalidTargetStatsStructureError("Each attribute requires an explicit two-element pair.")
        code, value = pair
        if type(code) is not str or code not in TARGET_STAT_CODES:
            raise InvalidTargetStatsStructureError("A canonical target attribute code is required.")
        if code in observed:
            raise InvalidTargetStatsStructureError("Duplicate target attribute code.")
        _number(value)
        observed[code] = value
    if len(observed) != len(TARGET_STAT_CODES):
        raise InvalidTargetStatsStructureError("Exactly the six target attributes are required.")
    return tuple((code, observed[code]) for code in TARGET_STAT_CODES)


@dataclass(frozen=True, slots=True)
class TargetStatsResult:
    """Validated immutable values; direct construction also checks all invariants.

    List inputs, including their pairs, are defensively copied into canonical
    tuples. Construction does not establish official provenance or permission.
    """

    bases: tuple[tuple[str, int], ...]
    increments: tuple[tuple[str, int], ...]
    effective: tuple[tuple[str, int], ...]
    budget: int
    points_used: int
    points_remaining: int

    def __post_init__(self):
        bases, increments, effective = (_pairs(values) for values in
                                        (self.bases, self.increments, self.effective))
        for value in (self.budget, self.points_used, self.points_remaining):
            _number(value)
        used = sum(value for _, value in increments)
        if used > self.budget:
            raise TargetStatsBudgetExceededError("Increments exceed the configuration budget.")
        expected_effective = tuple((code, base + increment) for (code, base), (_, increment)
                                   in zip(bases, increments))
        if (self.points_used != used or self.points_remaining != self.budget - used
                or effective != expected_effective):
            raise InvalidTargetStatsNumericError("Calculated statistics or budget totals are inconsistent.")
        object.__setattr__(self, "bases", bases)
        object.__setattr__(self, "increments", increments)
        object.__setattr__(self, "effective", effective)


def validate_target_stats(bases, increments, *, budget: int) -> TargetStatsResult:
    """Validate six explicit pairs per input, calculate and freeze one allocation.

    Only result order is canonicalized. No input conversion, filling missing
    attributes, normalization, shared point consumption or authority check.
    """
    bases, increments = _pairs(bases), _pairs(increments)
    _number(budget)
    used = sum(value for _, value in increments)
    if used > budget:
        raise TargetStatsBudgetExceededError("Increments exceed the configuration budget.")
    effective = tuple((code, base + increment) for (code, base), (_, increment)
                      in zip(bases, increments))
    return TargetStatsResult(bases, increments, effective, budget, used, budget - used)
