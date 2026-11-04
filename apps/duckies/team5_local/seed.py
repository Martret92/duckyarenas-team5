"""Datos SINTÉTICOS, solo para la BD aislada de Team5; no son valores oficiales."""
from django.core.management.base import CommandError
from django.db import transaction
from apps.ecomotor.models import EvolutionStage, LevelThreshold, Specialization
from apps.duckies.models import Item, EvolutionItem, SpecializationItem

LOCAL_CODES = tuple(f'team5-local-stage-{i}' for i in range(1, 8))
LOCAL_NAMES = ('Prehistoria', 'Grecia', 'Roma', 'Edad Media', 'Renacimiento', 'Revolución Industrial', 'Siglo XX')
LOCAL_SPECS = (('team5-local-developer','Developer'),('team5-local-ciber','Ciberseguridad'),('team5-local-sistemas','Sistemas'),('team5-local-data','Datos e IA'),('team5-local-gamer','Gamer'))

def seed():
    with transaction.atomic():
        if EvolutionStage.objects.exclude(code__in=LOCAL_CODES).exists() or LevelThreshold.objects.exclude(level__range=(1,21)).exists():
            raise CommandError('Existen etapas ajenas al catálogo local; no se sobrescriben.')
        for i,(code,name) in enumerate(zip(LOCAL_CODES,LOCAL_NAMES),1):
            stage, created = EvolutionStage.objects.get_or_create(code=code, defaults={'name':name,'ordinal':i,'minimum_xp':(i-1)*300})
            if (stage.ordinal,stage.minimum_xp)!=(i,(i-1)*300):
                raise CommandError('Etapa local incompatible; no se sobrescribe.')
            item, _ = Item.objects.get_or_create(code=f'team5_local_outfit_{i}',defaults={'name':f'Vestimenta {name}','category':Item.HISTORICAL,'is_active':True})
            EvolutionItem.objects.get_or_create(stage=stage,defaults={'item':item})
        for level in range(1,22):
            row,_=LevelThreshold.objects.get_or_create(level=level,defaults={'minimum_xp':(level-1)*100,'stat_points_awarded':0})
            if row.minimum_xp!=(level-1)*100: raise CommandError('Nivel incompatible.')
        for code,name in LOCAL_SPECS:
            spec,_=Specialization.objects.get_or_create(code=code,defaults={'name':name})
            item,_=Item.objects.get_or_create(code=f'outfit_{code}',defaults={'name':f'Vestimenta {name}','category':Item.SPECIALIZATION,'is_active':True})
            SpecializationItem.objects.get_or_create(specialization=spec,defaults={'item':item})
