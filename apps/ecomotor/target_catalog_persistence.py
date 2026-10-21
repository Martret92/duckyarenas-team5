"""Read and validate preparatory rows, never publish, freeze or activate them.

Each query uses the caller's explicit alias and one technical version PK. Reads
are not a stable concurrent catalog snapshot: rows may change between queries
or after return. The immutable pure result is not a frozen/authorized DB version.
"""

from django.core.exceptions import ValidationError
from django.db import connections

from . import target_catalog_validation
from .models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from .progression import LevelDefinition, StageDefinition
from .target_catalog_validation import InvalidTargetCatalogError, TargetCatalogSnapshot


def _text(value, model, field_name):
    # Validate observed text without ORM coercion or normalization. SQLite does
    # not enforce CharField max_length or reject every whitespace-only string.
    if type(value) is not str or not value.strip():
        raise InvalidTargetCatalogError("Catalog text must be nonblank.")
    try:
        model._meta.get_field(field_name).run_validators(value)
    except ValidationError as error:
        raise InvalidTargetCatalogError("Catalog text exceeds its field limits.") from error


def validate_target_catalog_version(catalog_version_id: int, *, using: str) -> TargetCatalogSnapshot:
    """Read one exact version PK and delegate whole-catalog invariants to A1.1.

    Invalid input/observed structure raises InvalidTargetCatalogError. Missing
    versions raise TargetCatalogVersion.DoesNotExist; real DatabaseError escapes
    unchanged. No repairs, writes, locks, authority checks or XP service calls.
    """
    if (type(catalog_version_id) is not int or not 1 <= catalog_version_id <= 2**63 - 1
            or type(using) is not str or not using or using not in connections):
        raise InvalidTargetCatalogError("An exact positive version PK and configured alias are required.")
    version = TargetCatalogVersion.objects.using(using).get(pk=catalog_version_id)
    _text(version.catalog_id, TargetCatalogVersion, "catalog_id")
    _text(version.version, TargetCatalogVersion, "version")
    levels = tuple(LevelDefinition(row.level, row.minimum_xp, stat_points_awarded=0)
                   for row in TargetLevelThreshold.objects.using(using)
                   .filter(catalog_id=version.pk).order_by("level"))
    epochs = []
    for row in TargetEpoch.objects.using(using).filter(catalog_id=version.pk).order_by("ordinal"):
        _text(row.code, TargetEpoch, "code")
        _text(row.name, TargetEpoch, "name")
        epochs.append(StageDefinition(row.code, row.ordinal, row.minimum_xp))
    return target_catalog_validation.validate_target_level_epoch_catalog(
        levels, tuple(epochs), ordered_epoch_codes=tuple(row.code for row in epochs),
        catalog_version=version.version,
    )
