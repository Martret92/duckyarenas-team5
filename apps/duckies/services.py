"""Servicios de Duckies: apariencia, inventario y equipamiento.

No concede XP, no modifica la Wallet y no aplica efectos de Quiz.
Las operaciones entre apps deben coordinarse desde una transacción exterior.
"""

from django.db import transaction

from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor

from .models import (
    Ducky,
    EquipmentHistory,
    EquippedItem,
    EvolutionItem,
    InventoryItem,
    Item,
    ItemGrant,
    ItemUsage,
    SpecializationItem,
)


def _positive(quantity):
    if type(quantity) is not int or quantity <= 0:
        raise ValueError("Cantidad positiva requerida")


def _variant(item, item_level):
    if item_level is None:
        return
    if item_level.item_id != item.pk:
        raise ValueError("Nivel de otro artículo")
    if item.category in (Item.HISTORICAL, Item.SPECIALIZATION):
        raise ValueError("Las vestimentas no tienen nivel táctico")
    if not 1 <= item_level.level <= 3:
        raise ValueError("Nivel táctico fuera del rango 1-3")


def _active_item(item, *, expected_category=None):
    if expected_category is not None and item.category != expected_category:
        raise ValueError("Categoría de artículo incompatible")
    if not item.is_active:
        raise ValueError("Objeto inactivo")


def _historical_association(stage_code):
    association = (
        EvolutionItem.objects.select_related("item", "stage")
        .get(stage__code=stage_code)
    )
    _active_item(association.item, expected_category=Item.HISTORICAL)
    return association


def _specialization_association(specialization_code):
    association = (
        SpecializationItem.objects.select_related("item", "specialization")
        .get(specialization__code=specialization_code)
    )
    _active_item(association.item, expected_category=Item.SPECIALIZATION)
    return association


def initialize_ducky(user, sex):
    """Alta idempotente: nunca reinicia la apariencia de un Ducky existente."""
    if sex not in ("male", "female"):
        raise ValueError("Elige sexo masculino o femenino")

    with transaction.atomic():
        profile = UserProfileEcomotor.objects.get(user=user)
        existing = Ducky.objects.select_for_update().filter(user=user).first()
        if existing:
            if existing.sex != sex:
                raise ValueError("Sexo de alta incompatible con Ducky existente")
            return existing

        if profile.active_specialization_code:
            raise ValueError("No se puede inicializar tarde un Ducky ya especializado")
        if not profile.current_stage_code:
            raise ValueError("El perfil no tiene etapa histórica inicial")

        outfit = _historical_association(profile.current_stage_code)
        return Ducky.objects.create(
            user=user, sex=sex, selected_outfit=outfit.item
        )


def sync_historical_outfit(user, stage=None, operation_key=None):
    """Sincroniza desde la etapa ACTUAL, no desde eventos antiguos.

    operation_key se conserva por compatibilidad; la idempotencia es por estado.
    """
    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        profile = UserProfileEcomotor.objects.get(user=user)
        if stage is not None:
            code = stage.code if hasattr(stage, "code") else stage
            if code != profile.current_stage_code:
                return ducky

        # Una vez especializado, no sobrescribir la apariencia manual.
        if profile.active_specialization_code:
            return ducky

        outfit = _historical_association(profile.current_stage_code)
        if ducky.selected_outfit_id != outfit.item_id:
            ducky.selected_outfit_id = outfit.item_id
            ducky.save(update_fields=["selected_outfit"])
        return ducky


def select_historical_outfit(user, item):
    _active_item(item, expected_category=Item.HISTORICAL)
    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        profile = UserProfileEcomotor.objects.get(user=user)
        current = EvolutionStage.objects.get(code=profile.current_stage_code)
        association = EvolutionItem.objects.select_related("stage").get(item=item)
        if association.stage.ordinal > current.ordinal:
            raise ValueError("Vestimenta futura bloqueada")
        if not profile.active_specialization_code and association.stage_id != current.pk:
            raise ValueError("Antes de especializarse solo puede vestir la época actual")
        if ducky.selected_outfit_id != item.pk:
            ducky.selected_outfit = item
            ducky.save(update_fields=["selected_outfit"])
        return ducky


def select_specialization_outfit(user, item):
    _active_item(item, expected_category=Item.SPECIALIZATION)
    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        profile = UserProfileEcomotor.objects.get(user=user)
        active_code = profile.active_specialization_code
        if not active_code:
            raise ValueError("El usuario todavía no tiene especialización")
        association = (
            SpecializationItem.objects.select_related("specialization")
            .filter(item=item)
            .first()
        )
        if association is None:
            raise ValueError("La vestimenta no tiene especialización asociada")
        if association.specialization.code != active_code:
            raise ValueError("No puedes utilizar una vestimenta de otra especialización")
        if ducky.selected_outfit_id != item.pk:
            ducky.selected_outfit = item
            ducky.save(update_fields=["selected_outfit"])
        return ducky


def select_outfit(user, item):
    if item.category == Item.HISTORICAL:
        return select_historical_outfit(user, item)
    if item.category == Item.SPECIALIZATION:
        return select_specialization_outfit(user, item)
    raise ValueError("Este objeto no es una vestimenta seleccionable")


def _validate_selected_outfit_locked(ducky, profile):
    """Valida la apariencia frente al progreso real de Ecomotor.

    Se invoca con el Ducky bloqueado dentro de una transacción. No escribe.
    """
    selected = ducky.selected_outfit
    if selected is None:
        raise ValueError("El Ducky no tiene vestimenta seleccionada")

    _active_item(selected)
    if selected.category == Item.HISTORICAL:
        association = EvolutionItem.objects.select_related("stage").get(item=selected)
        current = EvolutionStage.objects.get(code=profile.current_stage_code)
        if association.stage.ordinal > current.ordinal:
            raise ValueError("Vestimenta histórica futura bloqueada")
        if not profile.active_specialization_code and association.stage_id != current.pk:
            raise ValueError("Antes de especializarse solo puede vestir la época actual")
        return selected

    if selected.category == Item.SPECIALIZATION:
        if not profile.active_specialization_code:
            raise ValueError("Vestimenta especializada sin especialización activa")
        association = SpecializationItem.objects.select_related("specialization").get(
            item=selected
        )
        if association.specialization.code != profile.active_specialization_code:
            raise ValueError("Vestimenta de una especialización inactiva")
        return selected

    raise ValueError("La apariencia seleccionada no es una vestimenta válida")


def validate_selected_outfit(user):
    """Comprueba la coherencia de la apariencia; no altera el estado."""
    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().select_related(
            "selected_outfit"
        ).get(user=user)
        profile = UserProfileEcomotor.objects.get(user=user)
        _validate_selected_outfit_locked(ducky, profile)
        return ducky


def sync_specialization_outfit(
    user, previous_specialization_code, new_specialization_code, *, first_selection=False
):
    """Sincroniza la apariencia tras una selección/cambio REAL en Ecomotor.

    Debe llamarse en la misma transacción exterior que S11-A o S14-A.
    El coordinador no debe tratar un replay/UNCHANGED como un cambio nuevo.
    """
    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().select_related(
            "selected_outfit"
        ).get(user=user)
        profile = UserProfileEcomotor.objects.get(user=user)
        if (
            not new_specialization_code
            or profile.active_specialization_code != new_specialization_code
        ):
            raise ValueError("La especialización nueva no coincide con Ecomotor")

        target = _specialization_association(new_specialization_code)

        if first_selection:
            if previous_specialization_code:
                raise ValueError("La primera selección no admite especialización anterior")
            # S11-A debe haber confirmado una primera selección efectiva.
            # Validar el estado previo antes de sustituirlo.
            if ducky.selected_outfit is None or ducky.selected_outfit.category != Item.HISTORICAL:
                raise ValueError("La primera selección requiere una apariencia histórica")
            _active_item(ducky.selected_outfit, expected_category=Item.HISTORICAL)
            ducky.selected_outfit_id = target.item_id
            ducky.save(update_fields=["selected_outfit"])
            return ducky

        if not previous_specialization_code:
            raise ValueError("Falta la especialización anterior del cambio")

        if previous_specialization_code == new_specialization_code:
            # Un replay coherente no debe sobrescribir una elección manual.
            _validate_selected_outfit_locked(ducky, profile)
            return ducky

        selected = ducky.selected_outfit
        if selected is None:
            raise ValueError("El Ducky no tiene vestimenta seleccionada")
        _active_item(selected)

        if selected.category == Item.HISTORICAL:
            # Tras S14-A, la histórica debe seguir desbloqueada.
            _validate_selected_outfit_locked(ducky, profile)
            return ducky

        if selected.category != Item.SPECIALIZATION:
            raise ValueError("La apariencia actual no es válida")

        previous = _specialization_association(previous_specialization_code)
        if selected.pk != previous.item_id:
            raise ValueError("La apariencia no corresponde a la especialización anterior")

        ducky.selected_outfit_id = target.item_id
        ducky.save(update_fields=["selected_outfit"])
        return ducky


def get_item_ownership(user, item, item_level=None):
    _variant(item, item_level)
    ducky = Ducky.objects.get(user=user)
    inventory = InventoryItem.objects.filter(
        ducky=ducky, item=item, item_level=item_level
    ).first()
    return inventory.quantity if inventory else 0


def grant_item(
    user, item, quantity, operation_key, *, item_level=None,
    reference_type="", reference_id=""
):
    _positive(quantity)
    _variant(item, item_level)
    if not operation_key:
        raise ValueError("Clave obligatoria")
    if item.category in (Item.HISTORICAL, Item.SPECIALIZATION):
        raise ValueError("Las vestimentas no se entregan mediante inventario")

    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        previous = ItemGrant.objects.filter(
            ducky=ducky, operation_key=operation_key
        ).first()
        if previous:
            expected = (
                item.pk, item_level.pk if item_level else None,
                quantity, reference_type, reference_id,
            )
            actual = (
                previous.item_id, previous.item_level_id,
                previous.quantity, previous.reference_type, previous.reference_id,
            )
            if actual != expected:
                raise ValueError("Conflicto de idempotencia de entrega")
            return previous

        _active_item(item)
        inventory = InventoryItem.objects.select_for_update().filter(
            ducky=ducky, item=item, item_level=item_level
        ).first()
        if not item.consumable and (quantity != 1 or inventory):
            raise ValueError("Objeto permanente ya poseído o cantidad inválida")
        if inventory:
            inventory.quantity += quantity
            inventory.save(update_fields=["quantity"])
        else:
            InventoryItem.objects.create(
                ducky=ducky, item=item, item_level=item_level, quantity=quantity
            )
        return ItemGrant.objects.create(
            ducky=ducky, item=item, item_level=item_level,
            quantity=quantity, operation_key=operation_key,
            reference_type=reference_type, reference_id=reference_id,
        )


def equip_item(user, item, item_level=None):
    _variant(item, item_level)
    _active_item(item)
    if item.category in (Item.HISTORICAL, Item.SPECIALIZATION):
        return select_outfit(user, item)
    if not item.slot_id:
        raise ValueError("Objeto sin ranura equipable")

    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        inventory = InventoryItem.objects.get(
            ducky=ducky, item=item, item_level=item_level
        )
        if inventory.quantity < 1:
            raise ValueError("No quedan unidades disponibles")
        existing = EquippedItem.objects.select_related("inventory_item__item").filter(
            ducky=ducky, slot=item.slot
        ).first()
        if existing and existing.inventory_item_id == inventory.pk:
            return existing
        if existing:
            EquipmentHistory.objects.create(
                ducky=ducky, slot=item.slot,
                item=existing.inventory_item.item, action="UNEQUIP"
            )
            existing.delete()
        equipped = EquippedItem.objects.create(
            ducky=ducky, slot=item.slot, inventory_item=inventory
        )
        EquipmentHistory.objects.create(
            ducky=ducky, slot=item.slot, item=item, action="EQUIP"
        )
        return equipped


def consume_item(
    user, item, quantity, operation_key, *, game_reference,
    item_level=None, server_accepted=False
):
    _positive(quantity)
    _variant(item, item_level)
    if not server_accepted or not game_reference:
        raise ValueError("Solo un servidor autorizado puede confirmar consumo")
    if not item.consumable:
        raise ValueError("Objeto no consumible")
    if not operation_key:
        raise ValueError("Clave obligatoria")

    with transaction.atomic():
        ducky = Ducky.objects.select_for_update().get(user=user)
        old = ItemUsage.objects.filter(
            ducky=ducky, operation_key=operation_key
        ).first()
        if old:
            expected = (
                item.pk, item_level.pk if item_level else None,
                quantity, game_reference,
            )
            actual = (
                old.item_id, old.item_level_id, old.quantity, old.game_reference,
            )
            if actual != expected:
                raise ValueError("Conflicto de idempotencia de consumo")
            return old

        inventory = InventoryItem.objects.select_for_update().get(
            ducky=ducky, item=item, item_level=item_level
        )
        equipped = EquippedItem.objects.filter(
            ducky=ducky, inventory_item=inventory
        ).first()
        if equipped is None:
            raise ValueError("El objeto debe estar equipado antes de la partida")
        if inventory.quantity < quantity:
            raise ValueError("Inventario insuficiente")
        if inventory.quantity == quantity:
            EquipmentHistory.objects.create(
                ducky=ducky, slot=equipped.slot, item=item, action="UNEQUIP"
            )
            inventory.delete()
        else:
            inventory.quantity -= quantity
            inventory.save(update_fields=["quantity"])
        return ItemUsage.objects.create(
            ducky=ducky, item=item, item_level=item_level,
            quantity=quantity, operation_key=operation_key,
            game_reference=game_reference,
        )
