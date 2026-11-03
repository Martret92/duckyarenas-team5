"""Datos sintéticos aislados; no sobrescribe catálogos existentes."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.bank.models import Wallet
from apps.duckies.models import Item, EvolutionItem, SpecializationItem
from apps.ecomotor.models import EvolutionStage, LevelThreshold, Specialization
from apps.ecomotor.initialization import ensure_ecomotor_initialized
from apps.shop.management.commands.seed_shop_catalog import Command as ShopSeed

STAGES = (
    ('PREHISTORIA', 'Prehistoria'),
    ('GRECIA', 'Grecia'),
    ('ROMA', 'Roma'),
    ('MEDIEVAL', 'Medieval'),
    ('RENACIMIENTO', 'Renacimiento'),
    ('REVOLUCION_INDUSTRIAL', 'Revolución Industrial'),
    ('SIGLO_XX', 'Siglo XX'),
)
SPECS=(('GAMER','Gamer'),('DEVELOPER','Developer'),('CIBER','Ciberseguridad'),('SISTEMAS','Sistemas'),('DATA_IA','Datos e IA'))
class Command(BaseCommand):
    help='Prepara la BD LOCAL y SINTÉTICA del Equipo 5 sin borrar datos.'
    def handle(self,*args,**options):
        if not settings.DEBUG or not str(settings.DATABASES['default']['NAME']).endswith('db_team5_demo.sqlite3'):
            raise CommandError('Solo se permite con settings_team5_demo y BD aislada.')
        with transaction.atomic():
            if EvolutionStage.objects.exists() or LevelThreshold.objects.exists() or Specialization.objects.exists():
                if (list(EvolutionStage.objects.order_by('ordinal').values_list('code',flat=True))!=[x[0] for x in STAGES]
                    or list(LevelThreshold.objects.order_by('level').values_list('minimum_xp',flat=True))!=[0,100,250,450,700,1000,1400,1900]
                    or list(Specialization.objects.order_by('code').values_list('code',flat=True))!=sorted(x[0] for x in SPECS)):
                    raise CommandError('Catálogo existente incompatible; no se sobrescribe.')
            else:
                for n,(code,name) in enumerate(STAGES,1):
                    EvolutionStage.objects.create(code=code,name=name,ordinal=n,minimum_xp=[0,250,450,700,1000,1400,1900][n-1])
                for n,xp in enumerate((0,100,250,450,700,1000,1400,1900),1):
                    LevelThreshold.objects.create(level=n,minimum_xp=xp,stat_points_awarded=3 if n>1 else 0)
                for code,name in SPECS: Specialization.objects.create(code=code,name=name)
            for stage in EvolutionStage.objects.all():
                item,_=Item.objects.get_or_create(code='outfit_'+stage.code.lower(),defaults={'name':'Vestimenta '+stage.name,'category':Item.HISTORICAL,'is_active':True})
                EvolutionItem.objects.get_or_create(stage=stage,defaults={'item':item})
            for spec in Specialization.objects.all():
                item,_=Item.objects.get_or_create(code='outfit_'+spec.code.lower(),defaults={'name':'Vestimenta '+spec.name,'category':Item.SPECIALIZATION,'is_active':True})
                SpecializationItem.objects.get_or_create(specialization=spec,defaults={'item':item})
            user,_=get_user_model().objects.get_or_create(username='team5_demo_local',defaults={'is_active':False})
            ensure_ecomotor_initialized(user)
            Wallet.objects.get_or_create(user=user)
        ShopSeed().handle()
        self.stdout.write(self.style.SUCCESS('Demo local preparada. Visita /team5/ y crea tu Ducky.'))
