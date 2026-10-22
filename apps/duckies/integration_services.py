
"""Coordinación Ecomotor -> Duckies sin modificar Ecomotor.

Puntos de entrada para alta, XP histórica y especialización. Todos los
servicios deben usar la misma BD. No gestiona Wallet, Shop ni Rewards.
"""

from django.db import transaction

from apps.ecomotor.initialization import ensure_ecomotor_initialized
from apps.ecomotor.specialization_service import select_initial_specialization
from apps.ecomotor.specialization_switch_service import (
    SpecializationSwitchKind,
    switch_active_specialization,
)
from apps.ecomotor.xp_service import grant_historical_xp
from apps.users.models import UserProfileEcomotor

from .services import (
    initialize_ducky,
    sync_historical_outfit,
    sync_specialization_outfit,
    validate_selected_outfit,
)


def _database_alias(user):
    """Duckies services use the default DB; reject cross-database operations."""
    if user.pk is None or user._state.adding:
        raise ValueError("Se requiere un usuario guardado")
    alias = user._state.db or "default"
    if alias != "default":
        raise ValueError("Duckies requiere la base de datos 'default'")
    return alias


def initialize_player_ducky(user, sex):
    """Inicializa Ecomotor y Duckies; Wallet se aprovisiona en Bank."""
    alias = _database_alias(user)
    with transaction.atomic(using=alias):
        ensure_ecomotor_initialized(user)
        ducky = initialize_ducky(user, sex)
        validate_selected_outfit(user)
        return ducky


def grant_xp_and_sync_outfit(user, amount, operation_key):
    """Concede XP y sincroniza apariencia según etapa persistida actual."""
    alias = _database_alias(user)
    with transaction.atomic(using=alias):
        profile = UserProfileEcomotor.objects.using(alias).get(user=user)
        result = grant_historical_xp(profile, amount, operation_key)
        sync_historical_outfit(user)
        validate_selected_outfit(user)
        return result


def select_initial_specialization_and_outfit(user, specialization_code):
    """Primera selección: solo sincroniza como alta cuando Ecomotor la crea."""
    alias = _database_alias(user)
    with transaction.atomic(using=alias):
        profile = UserProfileEcomotor.objects.using(alias).get(user=user)
        result = select_initial_specialization(profile, specialization_code)
        if result.created:
            sync_specialization_outfit(
                user,
                previous_specialization_code=None,
                new_specialization_code=result.specialization_code,
                first_selection=True,
            )
        validate_selected_outfit(user)
        return result


def switch_specialization_and_outfit(user, target_code, expected_active_code):
    """Cambia la rama en Ecomotor y adapta la vestimenta en Duckies."""
    alias = _database_alias(user)
    with transaction.atomic(using=alias):
        profile = UserProfileEcomotor.objects.using(alias).get(user=user)
        result = switch_active_specialization(
            profile,
            target_code=target_code,
            expected_active_code=expected_active_code,
        )
        if result.kind == SpecializationSwitchKind.FIRST_ACTIVATION:
            # Puede ser la primera activación absoluta o la primera de otra rama.
            # La existencia de una especialización anterior decide la apariencia.
            sync_specialization_outfit(
                user,
                previous_specialization_code=expected_active_code,
                new_specialization_code=result.specialization_code,
                first_selection=not bool(expected_active_code),
            )
        elif result.kind == SpecializationSwitchKind.REACTIVATION:
            sync_specialization_outfit(
                user,
                previous_specialization_code=expected_active_code,
                new_specialization_code=result.specialization_code,
                first_selection=False,
            )
        elif result.kind != SpecializationSwitchKind.UNCHANGED:
            raise ValueError("Resultado de cambio de especialización desconocido")
        validate_selected_outfit(user)
        return result
