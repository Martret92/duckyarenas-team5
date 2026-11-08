import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from apps.bank.services import adjust_wallet
class Command(BaseCommand):
    help='Ajusta DuckyCoins por el libro contable oficial, solo local.'
    def add_arguments(self,p):
        p.add_argument('--username',required=True)
        p.add_argument('--amount',type=int,required=True)
    def handle(self,*args,**o):
        if not getattr(settings,'TEAM5_LOCAL_ISOLATED',False): raise CommandError('Solo settings_team5_local')
        if not 0<o['amount']<=1000000: raise CommandError('Importe fuera de rango')
        user=get_user_model().objects.get(username=o['username'])
        adjust_wallet(user,o['amount'],operation_key='team5-local-coins:'+uuid.uuid4().hex,description='Crédito administrativo de prueba',source='team5-local',issuing_entity='Team5')
        self.stdout.write(self.style.SUCCESS('DuckyCoins concedidas mediante Bank.'))
