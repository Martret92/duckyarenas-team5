"""Two explicit seed phases: preparation commit, then FREEZE's own transaction."""

from django.db import transaction

from apps.ecomotor import target_catalog_freeze
from apps.ecomotor.models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from apps.ecomotor.target_catalog_persistence import validate_target_catalog_version

from .data import CATALOG_ID, VERSION, CODES, NAMES, THRESHOLDS
from .isolation import demo_connection


class DemoCatalogError(ValueError):
    pass


def exact_catalog(pk, alias, *, frozen=True):
    version = TargetCatalogVersion.objects.using(alias).get(pk=pk)
    if (version.catalog_id, version.version) != (CATALOG_ID, VERSION):
        raise DemoCatalogError("Catálogo sintético incompatible.")
    if frozen and version.frozen_at is None:
        raise DemoCatalogError("El catálogo preparatorio no permite concesiones; repite seed.")
    levels = tuple(TargetLevelThreshold.objects.using(alias).filter(catalog=version).order_by("level")
                   .values_list("level", "minimum_xp"))
    epochs = tuple(TargetEpoch.objects.using(alias).filter(catalog=version).order_by("ordinal")
                   .values_list("code", "name", "ordinal", "minimum_xp"))
    if (levels != tuple(enumerate(THRESHOLDS, 1)) or epochs != tuple(
            (code, name, n, xp) for n, (code, name, xp)
            in enumerate(zip(CODES, NAMES, THRESHOLDS), 1))):
        raise DemoCatalogError("Contenido sintético diferente; no se repara.")
    return version, validate_target_catalog_version(pk, using=alias)


def seed_catalog():
    db = demo_connection()
    if db.in_atomic_block or not db.get_autocommit():
        raise DemoCatalogError("Seed necesita sus fronteras transaccionales propias.")
    alias = db.alias
    with transaction.atomic(using=alias):
        versions = tuple(TargetCatalogVersion.objects.using(alias).all())
        if not versions:
            version = TargetCatalogVersion.objects.using(alias).create(catalog_id=CATALOG_ID, version=VERSION)
            TargetLevelThreshold.objects.using(alias).bulk_create([
                TargetLevelThreshold(catalog=version, level=n, minimum_xp=xp)
                for n, xp in enumerate(THRESHOLDS, 1)])
            TargetEpoch.objects.using(alias).bulk_create([
                TargetEpoch(catalog=version, code=code, name=name, ordinal=n, minimum_xp=xp)
                for n, (code, name, xp) in enumerate(zip(CODES, NAMES, THRESHOLDS), 1)])
        elif len(versions) == 1:
            version = versions[0]
        else:
            raise DemoCatalogError("La demo solo admite su catálogo sintético exacto.")
        exact_catalog(version.pk, alias, frozen=False)
    # Intentionally outside atomic: FREEZE rejects a caller-owned transaction.
    # Failure here leaves a valid preparatory catalog; rerunning seed retries.
    target_catalog_freeze.freeze_target_catalog_version(version.pk, using=alias)
    with transaction.atomic(using=alias):
        exact_catalog(version.pk, alias)
    return version.pk
