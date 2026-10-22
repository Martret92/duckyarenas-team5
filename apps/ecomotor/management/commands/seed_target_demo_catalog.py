"""Explicit synthetic catalog installation, exclusively in the target demo DB."""

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.ecomotor.models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from apps.ecomotor.target_catalog_persistence import validate_target_catalog_version
from apps.ecomotor.target_catalog_validation import InvalidTargetCatalogError
from apps.ecomotor.target_demo_data import (
    CATALOG_ID, CATALOG_VERSION, EPOCH_CODES, EPOCH_NAMES, THRESHOLDS, demo_database,
)


class Command(BaseCommand):
    help = "Instala explícitamente el único catálogo sintético de la demo objetivo aislada."
    requires_system_checks = []

    def handle(self, *args, **options):
        try:
            alias = demo_database()
            with transaction.atomic(using=alias):
                versions = tuple(TargetCatalogVersion.objects.using(alias).all())
                if not versions:
                    version = TargetCatalogVersion.objects.using(alias).create(
                        catalog_id=CATALOG_ID, version=CATALOG_VERSION)
                    TargetLevelThreshold.objects.using(alias).bulk_create([
                        TargetLevelThreshold(catalog=version, level=n, minimum_xp=xp)
                        for n, xp in enumerate(THRESHOLDS, 1)])
                    TargetEpoch.objects.using(alias).bulk_create([
                        TargetEpoch(catalog=version, code=code, name=name, ordinal=n, minimum_xp=xp)
                        for n, (code, name, xp) in enumerate(zip(EPOCH_CODES, EPOCH_NAMES, THRESHOLDS), 1)])
                elif (len(versions) == 1 and versions[0].catalog_id == CATALOG_ID
                      and versions[0].version == CATALOG_VERSION and versions[0].frozen_at is None):
                    version = versions[0]
                else:
                    raise CommandError("Hay datos incompatibles; no se reparan ni sustituyen.")
                levels = tuple(TargetLevelThreshold.objects.using(alias).filter(catalog=version)
                               .order_by("level").values_list("level", "minimum_xp"))
                epochs = tuple(TargetEpoch.objects.using(alias).filter(catalog=version).order_by("ordinal")
                               .values_list("code", "name", "ordinal", "minimum_xp"))
                if (levels != tuple(enumerate(THRESHOLDS, 1)) or epochs != tuple(
                        (code, name, n, xp) for n, (code, name, xp)
                        in enumerate(zip(EPOCH_CODES, EPOCH_NAMES, THRESHOLDS), 1))):
                    raise CommandError("El catálogo existente difiere del sintético esperado; sin cambios.")
                validate_target_catalog_version(version.pk, using=alias)
        except (ImproperlyConfigured, DatabaseError, InvalidTargetCatalogError) as error:
            raise CommandError("No se pudo instalar la demo aislada; revisa settings, migraciones y catálogo.") from error
        self.stdout.write("Catálogo SINTÉTICO preparado (idempotente). No congelado, publicado ni autorizado.")
