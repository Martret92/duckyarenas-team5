"""A4.2.1: pure structural definitions, never catalog authorization.

Exact opaque identities and separate versions are caller-supplied values. Matching
a supplied context does not prove publication, provenance, eligibility or trust.
No player budget, persistence, official option codes or speculative storage limits.
"""

from dataclasses import dataclass

from .target_stats_validation import TARGET_STAT_CODES


class InvalidTargetStatsDefinitionError(ValueError):
    """Base error for structurally invalid target statistics definitions."""


class InvalidTargetStatsDefinitionIdentityError(InvalidTargetStatsDefinitionError):
    """An option, catalog or version is not exact nonblank text."""


class InvalidTargetStatsDefinitionStructureError(InvalidTargetStatsDefinitionError):
    """Invalid pairs, coverage, codes, duplicates or contextual representation."""


class InvalidTargetStatsDefinitionNumericError(InvalidTargetStatsDefinitionError):
    """A base is not an exact nonnegative Python integer."""


class TargetStatsDefinitionCatalogMismatchError(InvalidTargetStatsDefinitionError):
    """The definition differs from the explicitly supplied catalog context."""


def _identity(value):
    if type(value) is not str or not value.strip():
        raise InvalidTargetStatsDefinitionIdentityError("Exact nonblank identity text is required.")


def _bases(values):
    if type(values) not in (list, tuple):
        raise InvalidTargetStatsDefinitionStructureError("An explicit sequence of pairs is required.")
    observed = {}
    for pair in values:
        if type(pair) not in (list, tuple) or len(pair) != 2:
            raise InvalidTargetStatsDefinitionStructureError("Each base requires a two-element pair.")
        code, value = pair
        if type(code) is not str or code not in TARGET_STAT_CODES:
            raise InvalidTargetStatsDefinitionStructureError("A canonical attribute code is required.")
        if code in observed:
            raise InvalidTargetStatsDefinitionStructureError("Duplicate attribute code.")
        if type(value) is not int or value < 0:
            raise InvalidTargetStatsDefinitionNumericError("An exact nonnegative base is required.")
        observed[code] = value
    if len(observed) != len(TARGET_STAT_CODES):
        raise InvalidTargetStatsDefinitionStructureError("Exactly six canonical bases are required.")
    return tuple((code, observed[code]) for code in TARGET_STAT_CODES)


@dataclass(frozen=True, slots=True)
class TargetStatsCatalogContext:
    """Caller-supplied comparison scope, not a trusted catalog certificate."""

    catalog_id: str
    catalog_version: str

    def __post_init__(self):
        _identity(self.catalog_id)
        _identity(self.catalog_version)


@dataclass(frozen=True, slots=True)
class TargetStatsDefinitionSnapshot:
    """Validated immutable original values; direct construction also copies bases."""

    option_code: str
    catalog_id: str
    catalog_version: str
    definition_version: str
    bases: tuple[tuple[str, int], ...]

    def __post_init__(self):
        for value in (self.option_code, self.catalog_id, self.catalog_version, self.definition_version):
            _identity(value)
        object.__setattr__(self, "bases", _bases(self.bases))


def validate_target_stats_definition(
    *,
    option_code: str,
    catalog_id: str,
    catalog_version: str,
    definition_version: str,
    bases,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> TargetStatsDefinitionSnapshot:
    """Validate one definition, optionally compare exact catalog identity/version.

    No normalization, conversion, authority check or inferred option membership.
    Duplicates lost upstream cannot be detected retrospectively.
    """
    result = TargetStatsDefinitionSnapshot(
        option_code, catalog_id, catalog_version, definition_version, bases,
    )
    if expected_catalog is not None:
        if type(expected_catalog) is not TargetStatsCatalogContext:
            raise InvalidTargetStatsDefinitionStructureError("An exact catalog context is required.")
        context_id = getattr(expected_catalog, "catalog_id", None)
        context_version = getattr(expected_catalog, "catalog_version", None)
        _identity(context_id)
        _identity(context_version)
        if result.catalog_id != context_id or result.catalog_version != context_version:
            raise TargetStatsDefinitionCatalogMismatchError("Catalog identity or version differs.")
    return result
