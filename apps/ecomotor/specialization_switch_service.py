"""S14-A: cambio local por estado esperado, sin historial de solicitudes ni premios."""

from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction

from apps.users.models import UserProfileEcomotor

from . import specialization_service as selection
from .models import CharacterStats, Specialization, UserSpecializationProgress
from .specialization_service import (
    InconsistentSpecializationStateError, IneligibleSpecializationStageError,
    InvalidSpecializationCodeError, InvalidSpecializationConfigurationError,
    InvalidSpecializationProfileError, SpecializationDatabaseError,
)


class StaleSpecializationStateError(ValueError):
    """El código activo persistido ya no coincide con la precondición recibida."""


class SpecializationSwitchKind(str, Enum):
    FIRST_ACTIVATION = "FIRST_ACTIVATION"
    REACTIVATION = "REACTIVATION"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class SpecializationSwitchResult:
    profile_id: int
    specialization_id: int
    specialization_code: str
    progress_id: int
    kind: SpecializationSwitchKind


def switch_active_specialization(profile, target_code, expected_active_code):
    """Activa una rama o recupera la activa solo si coincide el estado esperado.

    Una secuencia A → B → A no puede distinguir todas las solicitudes antiguas.
    El resultado es estado confirmado por esta transacción, no replay histórico.
    """
    using = selection._profile_alias(profile)
    if not selection._code(target_code) or not selection._code(expected_active_code):
        raise InvalidSpecializationCodeError("Código objetivo o esperado inválido.")
    try:
        with transaction.atomic(using=using):
            current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
            if current is None:
                raise InvalidSpecializationProfileError("El perfil ya no existe.")
            stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
            rows = list(UserSpecializationProgress.objects.using(using).filter(profile_id=current.pk))
            try:
                selection._structure(current, stats, using)
                existing = selection._existing_selection(current, rows, using)
                if existing is None:
                    raise ValidationError("El cambio requiere una selección previa.")
            except ValidationError as error:
                raise InconsistentSpecializationStateError("Estado de especialización incompatible.") from error

            if current.active_specialization_code != expected_active_code:
                raise StaleSpecializationStateError("La solicitud tiene un estado esperado obsoleto.")
            if current.active_specialization_code == target_code:
                target, progress = existing
                kind = SpecializationSwitchKind.UNCHANGED
            else:
                selection._eligible(current, using)
                target = Specialization.objects.using(using).filter(code=target_code).first()
                if target is None:
                    raise InvalidSpecializationCodeError("Especialización solicitada inexistente.")
                try:
                    selection._specialization(target, using)
                except ValidationError as error:
                    raise InconsistentSpecializationStateError("Especialización persistida inválida.") from error
                progress = next((row for row in rows if row.specialization_id == target.pk), None)
                if progress is None:
                    progress = UserSpecializationProgress.objects.using(using).create(
                        profile_id=current.pk, specialization_id=target.pk, domain_xp_total=0,
                    )
                    kind = SpecializationSwitchKind.FIRST_ACTIVATION
                else:
                    kind = SpecializationSwitchKind.REACTIVATION
                current.active_specialization_code = target.code
                current.save(using=using, update_fields=["active_specialization_code"])
            return SpecializationSwitchResult(current.pk, target.pk, target.code, progress.pk, kind)
    except DatabaseError as error:
        raise SpecializationDatabaseError("Cambio abortado por fallo de BD.") from error
