"""A4.3.1: pure composition, never authorization or persistent confirmation.

Catalog context is only caller-supplied structural comparison. Neither versions
nor a prepared proposal certify official values, eligibility or permission.
"""

from dataclasses import dataclass

from . import target_stats_config_validation as definitions
from . import target_stats_validation as statistics
from .target_stats_config_validation import (
    TargetStatsCatalogContext,
    TargetStatsDefinitionSnapshot,
)
from .target_stats_validation import TargetStatsResult


class InvalidTargetStatsPreparationError(ValueError):
    """Incompatible component types or contradictory component bases."""


def _definition_copy(definition, expected_catalog=None):
    if type(definition) is not TargetStatsDefinitionSnapshot:
        raise InvalidTargetStatsPreparationError("An exact definition snapshot is required.")
    return definitions.validate_target_stats_definition(
        option_code=getattr(definition, "option_code", None),
        catalog_id=getattr(definition, "catalog_id", None),
        catalog_version=getattr(definition, "catalog_version", None),
        definition_version=getattr(definition, "definition_version", None),
        bases=getattr(definition, "bases", None),
        expected_catalog=expected_catalog,
    )


@dataclass(frozen=True, slots=True)
class PreparedTargetStatsConfiguration:
    """Independent validated copies, including when constructed directly.

Frozen inputs are revalidated because callers can bypass their constructors.
The proposal contains no player identity, authority or persistence state.
"""

    definition: TargetStatsDefinitionSnapshot
    calculation: TargetStatsResult

    def __post_init__(self):
        if type(self.calculation) is not TargetStatsResult:
            raise InvalidTargetStatsPreparationError("An exact statistics result is required.")
        definition = _definition_copy(self.definition)
        calculation = TargetStatsResult(
            bases=getattr(self.calculation, "bases", None),
            increments=getattr(self.calculation, "increments", None),
            effective=getattr(self.calculation, "effective", None),
            budget=getattr(self.calculation, "budget", None),
            points_used=getattr(self.calculation, "points_used", None),
            points_remaining=getattr(self.calculation, "points_remaining", None),
        )
        if definition.bases != calculation.bases:
            raise InvalidTargetStatsPreparationError("Definition and calculation bases differ.")
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "calculation", calculation)


def prepare_target_stats_configuration(
    *,
    definition: TargetStatsDefinitionSnapshot,
    increments,
    budget: int,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> PreparedTargetStatsConfiguration:
    """Prepare one independent proposal using the public A4.2.1/A4.1 APIs.

Existing validation exceptions propagate unchanged. No defaults, resolution of
trusted configuration, side effects or selection/redistribution are performed.
"""
    validated = _definition_copy(definition, expected_catalog)
    calculation = statistics.validate_target_stats(validated.bases, increments, budget=budget)
    return PreparedTargetStatsConfiguration(validated, calculation)
