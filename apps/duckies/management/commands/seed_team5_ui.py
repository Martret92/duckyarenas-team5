"""Populate only a dedicated, empty local demo database.

Usage: python manage.py seed_team5_ui
Never run against real project data.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from apps.duckies.team5_ui.demo_services import seed_local_catalog

class Command(BaseCommand):
    help="Prepara catálogo sintético para la interfaz Team 5 en una BD local de desarrollo"
    def handle(self,*args,**kwargs):
        if not settings.DEBUG:
            raise CommandError("Solo permitido con DEBUG=True")
        try:
            seed_local_catalog()
            call_command("seed_shop_catalog")
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Catálogos locales preparados. Abre http://127.0.0.1:8000/team5/"))
