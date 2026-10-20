"""Inventario y vestimenta; no aplica efectos de Quiz."""
from django.db import transaction
from apps.users.models import UserProfileEcomotor
from apps.ecomotor.models import EvolutionStage
from .models import Ducky,Item,ItemLevel,InventoryItem,ItemGrant,ItemUsage,EquippedItem,EquipmentHistory,EvolutionItem

def _positive(q):
    if type(q) is not int or q<=0: raise ValueError('Cantidad positiva requerida')

def _variant(item,level):
    if level is not None and level.item_id!=item.pk: raise ValueError('Nivel de otro artículo')

def initialize_ducky(user,sex):
    if sex not in ('male','female'): raise ValueError('Elige sexo masculino o femenino')
    with transaction.atomic():
        profile=UserProfileEcomotor.objects.get(user=user)
        existing=Ducky.objects.select_for_update().filter(user=user).first()
        if existing:
            if existing.sex!=sex: raise ValueError('Sexo de alta incompatible con Ducky existente')
            return existing
        outfit=EvolutionItem.objects.select_related('item').get(stage__code=profile.current_stage_code)
        return Ducky.objects.create(user=user,sex=sex,selected_historical_item=outfit.item)

def sync_historical_outfit(user,stage=None,operation_key=None):
    """Se basa en el estado actual, nunca en un evento atrasado."""
    with transaction.atomic():
        ducky=Ducky.objects.select_for_update().get(user=user)
        profile=UserProfileEcomotor.objects.get(user=user)
        latest=EvolutionItem.objects.get(stage__code=profile.current_stage_code)
        if stage is not None:
            code=stage.code if hasattr(stage,'code') else stage
            if code!=profile.current_stage_code: return ducky
        if profile.active_specialization_code:
            # Una selección histórica manual válida no debe sobrescribirse por un replay.
            return ducky
        if ducky.selected_historical_item_id!=latest.item_id:
            ducky.selected_historical_item_id=latest.item_id
            ducky.save(update_fields=['selected_historical_item'])
        return ducky

def select_historical_outfit(user,item):
    with transaction.atomic():
        ducky=Ducky.objects.select_for_update().get(user=user)
        profile=UserProfileEcomotor.objects.get(user=user)
        current=EvolutionStage.objects.get(code=profile.current_stage_code)
        association=EvolutionItem.objects.select_related('stage').get(item=item)
        if association.stage.ordinal>current.ordinal: raise ValueError('Vestimenta futura bloqueada')
        if not profile.active_specialization_code and association.stage_id!=current.pk:
            raise ValueError('Antes de especializarse solo puede vestir la época actual')
        ducky.selected_historical_item=item;ducky.save(update_fields=['selected_historical_item'])
        return ducky

def get_item_ownership(user,item,item_level=None):
    _variant(item,item_level)
    ducky=Ducky.objects.get(user=user)
    inv=InventoryItem.objects.filter(ducky=ducky,item=item,item_level=item_level).first()
    return inv.quantity if inv else 0

def grant_item(user,item,quantity,operation_key,*,item_level=None,reference_type='',reference_id=''):
    _positive(quantity);_variant(item,item_level)
    if not operation_key: raise ValueError('Clave obligatoria')
    if item.category==Item.HISTORICAL: raise ValueError('Las vestimentas se obtienen por evolución')
    if not item.is_active: raise ValueError('Objeto inactivo')
    with transaction.atomic():
        ducky=Ducky.objects.select_for_update().get(user=user)
        previous=ItemGrant.objects.filter(ducky=ducky,operation_key=operation_key).first()
        if previous:
            if (previous.item_id,previous.item_level_id,previous.quantity,previous.reference_type,previous.reference_id)!=(item.pk,item_level.pk if item_level else None,quantity,reference_type,reference_id):
                raise ValueError('Conflicto de idempotencia de entrega')
            return previous
        inv=InventoryItem.objects.filter(ducky=ducky,item=item,item_level=item_level).first()
        if not item.consumable and (quantity!=1 or inv): raise ValueError('Objeto permanente ya poseído o cantidad inválida')
        if inv:
            inv.quantity+=quantity;inv.save(update_fields=['quantity'])
        else: InventoryItem.objects.create(ducky=ducky,item=item,item_level=item_level,quantity=quantity)
        return ItemGrant.objects.create(ducky=ducky,item=item,item_level=item_level,quantity=quantity,operation_key=operation_key,reference_type=reference_type,reference_id=reference_id)

def equip_item(user,item,item_level=None):
    _variant(item,item_level)
    if item.category==Item.HISTORICAL: return select_historical_outfit(user,item)
    if not item.slot_id: raise ValueError('Objeto sin ranura equipable')
    with transaction.atomic():
        ducky=Ducky.objects.select_for_update().get(user=user)
        inv=InventoryItem.objects.get(ducky=ducky,item=item,item_level=item_level)
        existing=EquippedItem.objects.filter(ducky=ducky,slot=item.slot).first()
        if existing and existing.inventory_item_id==inv.pk: return existing
        if existing:
            EquipmentHistory.objects.create(ducky=ducky,slot=item.slot,item=existing.inventory_item.item,action='UNEQUIP')
            existing.delete()
        equipped=EquippedItem.objects.create(ducky=ducky,slot=item.slot,inventory_item=inv)
        EquipmentHistory.objects.create(ducky=ducky,slot=item.slot,item=item,action='EQUIP')
        return equipped

def consume_item(user,item,quantity,operation_key,*,game_reference,item_level=None,server_accepted=False):
    _positive(quantity);_variant(item,item_level)
    if not server_accepted or not game_reference: raise ValueError('Solo un servidor autorizado puede confirmar consumo')
    if not item.consumable: raise ValueError('Objeto no consumible')
    if not operation_key: raise ValueError('Clave obligatoria')
    with transaction.atomic():
        ducky=Ducky.objects.select_for_update().get(user=user)
        old=ItemUsage.objects.filter(ducky=ducky,operation_key=operation_key).first()
        if old:
            if (old.item_id,old.item_level_id,old.quantity,old.game_reference)!=(item.pk,item_level.pk if item_level else None,quantity,game_reference):
                raise ValueError('Conflicto de idempotencia de consumo')
            return old
        inv=InventoryItem.objects.select_for_update().get(ducky=ducky,item=item,item_level=item_level)
        if not EquippedItem.objects.filter(ducky=ducky,inventory_item=inv).exists():
            raise ValueError('El objeto debe estar equipado antes de la partida')
        if inv.quantity<quantity: raise ValueError('Inventario insuficiente')
        if inv.quantity==quantity:
            equipped=EquippedItem.objects.filter(ducky=ducky,inventory_item=inv).first()
            if equipped:
                EquipmentHistory.objects.create(ducky=ducky,slot=equipped.slot,item=item,action='UNEQUIP')
            inv.delete()
        else: inv.quantity-=quantity;inv.save(update_fields=['quantity'])
        return ItemUsage.objects.create(ducky=ducky,item=item,item_level=item_level,quantity=quantity,operation_key=operation_key,game_reference=game_reference)
