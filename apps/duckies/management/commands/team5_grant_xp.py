import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from apps.duckies.integration_services import grant_xp_and_sync_outfit
class Command(BaseCommand):
    help='Concede XP mediante Ecomotor solo en entorno local.'
    def add_arguments(self,p):
        p.add_argument('--username',required=True)
        p.add_argument('--amount',type=int,required=True)
    def handle(self,*args,**o):
        if not getattr(settings,'TEAM5_LOCAL_ISOLATED',False): raise CommandError('Solo settings_team5_local')
        if not 0<o['amount']<=1000000: raise CommandError('Importe fuera de rango')
        user=get_user_model().objects.get(username=o['username'])
        grant_xp_and_sync_outfit(user,o['amount'],'team5-local-xp:'+uuid.uuid4().hex)
        self.stdout.write(self.style.SUCCESS('XP concedida mediante Ecomotor.'))
