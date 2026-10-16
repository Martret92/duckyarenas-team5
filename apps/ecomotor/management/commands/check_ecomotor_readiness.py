from django.core.management.base import BaseCommand, CommandError
from django.utils.connection import ConnectionDoesNotExist

from apps.ecomotor.configuration_checks import ReadinessDatabaseError, check_ecomotor_readiness
from apps.ecomotor.initialization_config import (
    ConfigurationFileError, ConfigurationFileMissingError, ConfigurationStructureError,
    ConfigurationSyntaxError, load_initialization_configuration,
)


class Command(BaseCommand):
    help = "Diagnóstico técnico de Ecomotor, sin guardar ni activar configuración."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--config", metavar="PATH")
        parser.add_argument("--database", default="default", metavar="ALIAS")

    def handle(self, *args, **options):
        self.stdout.write("Aprobación funcional independiente. No se guarda ni activa configuración del servidor.")
        try:
            kwargs = {"using": options["database"]}
            if options["config"] is not None:
                kwargs["configuration"] = load_initialization_configuration(
                    options["config"], using=options["database"],
                )
            result = check_ecomotor_readiness(**kwargs)
        except ConfigurationFileMissingError:
            raise CommandError("CONFIGURATION_MISSING: fuente explícita ausente.", returncode=2) from None
        except (ConfigurationSyntaxError, ConfigurationStructureError):
            raise CommandError("INVALID_CONFIGURATION: JSON inválido.", returncode=2) from None
        except (ConfigurationFileError, ReadinessDatabaseError, ConnectionDoesNotExist):
            raise CommandError("Fallo operativo al leer archivo o base de datos.", returncode=3) from None
        self.stdout.write(result.status.value)
        for issue in result.issues:
            self.stdout.write(f"{issue.code}: {issue.message}")
        if not result.technically_consistent:
            raise CommandError("Diagnóstico no preparado; no se ha activado configuración.", returncode=2)
