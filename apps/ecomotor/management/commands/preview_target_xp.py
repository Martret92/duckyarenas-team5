"""Internal read-only simulation. Console output occurs after the transaction."""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from apps.ecomotor.models import TargetCatalogVersion
from apps.ecomotor.target_xp_preview import (
    InvalidTargetCatalogError, InvalidTargetXPAmountError, InvalidTargetXPError,
    TargetXPPreviewTransactionError, preview_target_xp,
)


class Command(BaseCommand):
    help = "Simular XP objetivo sobre catálogo persistido, sin conceder ni activar."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--catalog-version-id", required=True, type=int, metavar="PK")
        parser.add_argument("--database", required=True, metavar="ALIAS")
        parser.add_argument("--xp-before", required=True, type=int, metavar="XP")
        parser.add_argument("--amount", required=True, type=int, metavar="XP")

    def handle(self, *args, **options):
        try:
            result = preview_target_xp(
                options["catalog_version_id"], using=options["database"],
                xp_before=options["xp_before"], amount=options["amount"],
            )
        except (InvalidTargetCatalogError, InvalidTargetXPError, InvalidTargetXPAmountError):
            raise CommandError("Entrada o catálogo objetivo inválido; no se ha concedido XP.", returncode=2) from None
        except TargetCatalogVersion.DoesNotExist:
            raise CommandError("Versión de catálogo no encontrada; no se ha concedido XP.", returncode=2) from None
        except TargetXPPreviewTransactionError:
            raise CommandError("Frontera transaccional SQLite incompatible; simulación rechazada.", returncode=2) from None
        except DatabaseError:
            raise CommandError("Fallo de lectura o bloqueo de base de datos; no hay resultado de simulación.", returncode=3) from None
        progression = result.plan.progression
        self.stdout.write("SIMULACIÓN INTERNA — No se ha concedido XP real. El catálogo no queda autorizado ni activado por esta operación.")
        self.stdout.write(f"Catálogo PK: {result.catalog_version_id} | Versión: {progression.catalog_version}")
        self.stdout.write(f"XP: {progression.xp_before} → {progression.xp_after} | Importe simulado: {result.plan.amount}")
        self.stdout.write(f"Nivel: {progression.level_before} → {progression.level_after}")
        self.stdout.write(f"Época: {progression.epoch_before_code} → {progression.epoch_after_code}")
        self.stdout.write(f"Niveles cruzados: {', '.join(map(str, progression.crossed_levels)) or '(ninguno)'}")
        self.stdout.write(f"Épocas cruzadas: {', '.join(progression.crossed_epoch_codes) or '(ninguna)'}")
        self.stdout.write(f"Elección desbloqueada antes: {progression.choice_unlocked_before}")
        self.stdout.write(f"Elección desbloqueada después: {progression.choice_unlocked_after}")
        self.stdout.write(f"Elección recién desbloqueada: {progression.choice_newly_unlocked}")
