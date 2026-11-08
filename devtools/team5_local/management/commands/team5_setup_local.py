from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from devtools.team5_local.seed import seed

class Command(BaseCommand):
    help = 'Carga SOLO catálogos sintéticos de la base local aislada.'
    def handle(self,*args,**kwargs):
        if not getattr(settings,'TEAM5_LOCAL_ISOLATED',False):
            raise CommandError('Requiere --settings=config.settings_team5_local')
        seed()
        self.stdout.write(self.style.SUCCESS('Catálogo sintético local preparado.'))
