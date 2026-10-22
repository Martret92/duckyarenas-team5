from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from apps.ecomotor.models import TargetCatalogVersion
from apps.ecomotor.target_catalog_freeze import TargetCatalogFreezeTransactionError
from apps.ecomotor.target_catalog_validation import InvalidTargetCatalogError

from ...catalog import DemoCatalogError, seed_catalog


class Command(BaseCommand):
    help = "Prepara y congela el catálogo ficticio, exclusivamente en la SQLite persistente de demo."
    requires_system_checks = []

    def handle(self, *args, **options):
        try:
            seed_catalog()
        except (ImproperlyConfigured, DatabaseError, DemoCatalogError, InvalidTargetCatalogError,
                TargetCatalogVersion.DoesNotExist, TargetCatalogFreezeTransactionError) as error:
            raise CommandError("Seed no completado. Si quedó preparatorio, corrige el fallo y repite seed; XP sigue bloqueada.") from error
        self.stdout.write("Catálogo SINTÉTICO exacto y congelado. No publicado ni autorizado funcionalmente.")
