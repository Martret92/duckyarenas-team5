"""Consultas de solo lectura. Nunca conceden artículos ni modifican XP."""
from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor
from .models import Ducky, EvolutionItem, EquippedItem, InventoryItem, SpecializationItem


def get_ducky(user):
    return Ducky.objects.select_related('selected_outfit').filter(user=user).first()


def get_inventory(ducky):
    return InventoryItem.objects.filter(ducky=ducky).select_related('item', 'item_level', 'item__slot').order_by('item__name', 'item_level__level')


def get_equipment(ducky):
    return EquippedItem.objects.filter(ducky=ducky).select_related('slot', 'inventory_item__item', 'inventory_item__item_level')


def get_outfit_catalog(user):
    profile = UserProfileEcomotor.objects.filter(user=user).first()
    if profile is None:
        return [], []
    stage = EvolutionStage.objects.filter(code=profile.current_stage_code).first()
    current_ordinal = stage.ordinal if stage else 0
    historical = []
    for association in EvolutionItem.objects.select_related('stage', 'item').order_by('stage__ordinal'):
        allowed = (association.stage.ordinal <= current_ordinal if profile.active_specialization_code
                   else association.stage_id == (stage.pk if stage else None))
        historical.append({'item': association.item, 'stage': association.stage, 'allowed': bool(allowed and association.item.is_active)})
    specializations = []
    for association in SpecializationItem.objects.select_related('specialization', 'item').order_by('specialization__name'):
        allowed = association.specialization.code == profile.active_specialization_code
        specializations.append({'item': association.item, 'specialization': association.specialization, 'allowed': bool(allowed and association.item.is_active)})
    return historical, specializations
