"""Read-only technical audit, console output strictly after the observation."""

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from apps.ecomotor.target_catalog_audit import (
    CatalogAuditState, InvalidTargetCatalogAuditInputError,
    TargetCatalogAuditTransactionError, audit_target_catalog,
)


class Command(BaseCommand):
    help = "Auditoría técnica observada del catálogo objetivo, sin autorización ni reparaciones."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--catalog-version-id", required=True, type=int, metavar="PK")
        parser.add_argument("--database", required=True, metavar="ALIAS")

    def handle(self, *args, **options):
        try:
            result = audit_target_catalog(options["catalog_version_id"], using=options["database"])
        except InvalidTargetCatalogAuditInputError:
            raise CommandError("Entrada inválida: PK técnica positiva y alias configurado obligatorios.", returncode=2) from None
        except TargetCatalogAuditTransactionError:
            raise CommandError("Auditoría no completada: frontera SQLite incompatible.", returncode=3) from None
        except DatabaseError:
            raise CommandError("Auditoría no completada: fallo operativo de conexión, SQL o bloqueo.", returncode=3) from None
        self.stdout.write(f"Alias: {result.using} | Catálogo PK solicitado: {result.catalog_version_id}")
        self.stdout.write(f"Identidad observada: {result.catalog_id!r} | Versión: {result.version!r}")
        labels = {CatalogAuditState.PREPARATORY: "PREPARATORIA — no congelada",
                  CatalogAuditState.FROZEN: "CONGELADA — marca observada, sin acreditar aprobación",
                  CatalogAuditState.UNOBSERVED: "NO OBSERVADO — estructura insuficiente o versión ausente"}
        self.stdout.write(f"Estado: {labels[result.state]} | frozen_at: {result.frozen_at!r}")
        self.stdout.write("Preparatoria significa no congelada; congelada tampoco acredita autorización funcional.")
        for check in result.checks:
            self.stdout.write(f"{'OK' if check.passed else check.issue_code}: {check.name} — {check.subject}")
        if not result.technically_conformant:
            raise CommandError("Incumplimiento técnico observado; no constituye autorización funcional.", returncode=2)
        self.stdout.write("CONFORMIDAD TÉCNICA OBSERVADA — No constituye autorización funcional ni habilita concesiones XP.")
