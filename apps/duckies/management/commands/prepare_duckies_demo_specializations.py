"""Catálogo de especializaciones para demo LOCAL; nunca altera XP ni perfiles."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.ecomotor.models import Specialization

DEMO_SPECIALIZATIONS = (
    ("DEVELOPER", "Developer"),
    ("GAMER", "Gamer"),
    ("CIBER", "Ciberseguridad"),
    ("SISTEMAS", "Sistemas"),
    ("DATA_IA", "Datos e IA"),
)

class Command(BaseCommand):
    help = "Crea solo las especializaciones ausentes para una demo con DEBUG=True."
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Solo disponible en DEBUG=True.")
        existing = dict(Specialization.objects.values_list("code", "name"))
        for code, name in DEMO_SPECIALIZATIONS:
            if code in existing:
                self.stdout.write(f"Ya existe {code} ({existing[code]}). Sin cambios.")
            elif options["dry_run"]:
                self.stdout.write(f"Se crearía {code}.")
            else:
                Specialization.objects.create(code=code, name=name)
                self.stdout.write(self.style.SUCCESS(f"Creada especialización DEMO {code}."))
        self.stdout.write("No se modificaron perfiles, XP, monedas ni especializaciones activas.")
