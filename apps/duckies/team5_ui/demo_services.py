"""Demo aislada: catálogo sintético explícito y aprovisionamiento local.
Nunca se debe activar en producción ni con DEBUG=False.
"""
from contextlib import contextmanager
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.bank.models import Wallet
from apps.bank.services import credit_coins
from apps.duckies.integration_services import initialize_player_ducky
from apps.ecomotor import initialization_config
from apps.ecomotor.models import EvolutionStage, LevelThreshold, Specialization
from apps.duckies.models import EvolutionItem, SpecializationItem, Item
from apps.duckies.services import grant_item

STAGES = (("PREHISTORICO","Prehistoria"),("GRIEGO","Antigua Grecia"),("ROMANO","Roma Imperial"),("MEDIEVAL","Edad Medieval"),("RENACENTISTA","Renacimiento"),("REVOLUCION_INDUSTRIAL","Revolución Industrial"),("SIGLO_XX","Siglo XX"))
SPECS = (("DEVELOPER","Developer"),("GAMER","Gamer"),("CIBER","Ciberseguridad"),("SISTEMAS","Sistemas"),("DATA_IA","Data / IA"))

@contextmanager
def local_initialization_config():
    config = initialization_config.InitializationConfiguration(atk=1,def_stat=1,log_stat=1,spe=1,vel=1,int_stat=1,ordered_stage_codes=tuple(c for c,_ in STAGES))
    with patch.object(initialization_config,"INITIAL_CONFIGURATION",config):
        yield

def seed_local_catalog():
    """Sólo crea catálogo si la base de datos está vacía; nunca reescribe catálogo real."""
    with transaction.atomic():
        if EvolutionStage.objects.exists() or LevelThreshold.objects.exists() or Specialization.objects.exists():
            if not (EvolutionStage.objects.count()==7 and LevelThreshold.objects.exists() and Specialization.objects.exists()):
                raise ValueError("Catálogo Ecomotor parcial/externo. No se modifica automáticamente; usa una BD demo limpia.")
            return
        for n,(code,name) in enumerate(STAGES,1):
            stage=EvolutionStage.objects.create(code=code,name=name,ordinal=n,minimum_xp=(n-1)*500)
            item=Item.objects.create(code=f"ui_hist_{code.lower()}",name=f"Vestimenta {name}",category=Item.HISTORICAL,description=f"Vestimenta de {name}")
            EvolutionItem.objects.create(stage=stage,item=item)
        for n in range(1,51):
            LevelThreshold.objects.create(level=n,minimum_xp=(n-1)*100,stat_points_awarded=2)
        for code,name in SPECS:
            spec=Specialization.objects.create(code=code,name=name)
            item=Item.objects.create(code=f"ui_spec_{code.lower()}",name=f"Traje {name}",category=Item.SPECIALIZATION)
            SpecializationItem.objects.create(specialization=spec,item=item)

def demo_user():
    user,_=get_user_model().objects.get_or_create(username="team5_demo_local",defaults={"is_active":True})
    return user

def provision(user,sex):
    with local_initialization_config():
        ducky=initialize_player_ducky(user,sex)
    Wallet.objects.get_or_create(user=user)
    return ducky

def credit_demo(user,amount,operation_key):
    return credit_coins(user,amount,source="TEAM5_LOCAL_DEMO",issuing_entity="Team5 Demo",operation_key=operation_key,description="Crédito manual de pruebas")


def grant_demo_hint(user, operation_key):
    """Entrega local de prueba: NO es Rewards ni usa el laboratorio de Jaime.

    Solo invocable desde la interfaz protegida por localhost y DEBUG.
    La operación de inventario utiliza el servicio público idempotente de Duckies.
    """
    item, _ = Item.objects.get_or_create(
        code="team5_local_hint",
        defaults={
            "name": "Pista de prueba (HINT)",
            "description": "Objeto de prueba local; no representa un premio de Rewards.",
            "category": Item.HINT,
            "consumable": True,
        },
    )
    if item.category != Item.HINT or not item.consumable:
        raise ValueError("El código de HINT local pertenece a un objeto incompatible")
    return grant_item(
        user, item, 1, operation_key,
        reference_type="TEAM5_LOCAL_DEMO", reference_id="manual-hint",
    )
