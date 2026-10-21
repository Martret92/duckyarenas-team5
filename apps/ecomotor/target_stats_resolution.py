"""A4.4.1: real resolution is closed until an approved source is integrated.

The private composition exercise checks untrusted caller-supplied values only.
Its success is never authorization, publication, eligibility or confirmation.
No provider registry, demo fallback, configuration, I/O or persistence exists here.
"""

from . import target_stats_preparation
from .target_stats_config_validation import (
    TargetStatsCatalogContext,
    TargetStatsDefinitionSnapshot,
)
from .target_stats_preparation import PreparedTargetStatsConfiguration


class TargetStatsResolutionError(ValueError):
    """Base error for the minimal resolution boundary."""


class TargetStatsSourceUnavailableError(TargetStatsResolutionError):
    """No approved trustworthy source has been integrated."""


class InvalidTargetStatsResolutionRequestError(TargetStatsResolutionError):
    """The private exercise received an invalid requested option identity."""


class TargetStatsResolutionOptionMismatchError(TargetStatsResolutionError):
    """Requested option and structurally validated definition differ."""


def resolve_target_stats_configuration(
    *, option_code: str, increments,
) -> PreparedTargetStatsConfiguration:
    """Always reject: supplied Python objects cannot establish a trusted source.

    Deliberately do not inspect inputs, invoke preparation, classify publication
    or eligibility, or use the private exercise as a fallback. This signature
    offers no injectable provider, budget, definition, authority flag or version.
    """
    raise TargetStatsSourceUnavailableError("No approved statistics source is available.")


def _prepare_untrusted_resolution_candidate(
    *,
    option_code: str,
    definition: TargetStatsDefinitionSnapshot,
    increments,
    budget: int,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> PreparedTargetStatsConfiguration:
    """Private structural exercise, disconnected from the real entry point.

    Reuse public A4.3.1 validation and defensive copying; propagate its errors.
    Catalog context only compares supplied values. No defaults or trust result.
    """
    if type(option_code) is not str or not option_code.strip():
        raise InvalidTargetStatsResolutionRequestError("Exact nonblank option text is required.")
    prepared = target_stats_preparation.prepare_target_stats_configuration(
        definition=definition, increments=increments, budget=budget,
        expected_catalog=expected_catalog,
    )
    if option_code != prepared.definition.option_code:
        raise TargetStatsResolutionOptionMismatchError("Requested option differs from the definition.")
    return prepared
