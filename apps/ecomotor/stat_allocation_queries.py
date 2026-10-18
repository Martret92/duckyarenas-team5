"""S9-A: snapshots de asignaciones, sin escrituras ni reconstrucción histórica."""

from dataclasses import dataclass
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections

from apps.users.models import UserProfileEcomotor

from .models import CharacterStats, STAT_ATTRIBUTES, StatAllocationEvent
from .progress_queries import (
    InconsistentQueryStateError, InvalidHistoryParametersError,
    InvalidQueryProfileError, ProgressQueryDatabaseError,
)


@dataclass(frozen=True)
class StatAllocationHistoryEntry:
    id: int
    attribute: str
    points_spent: int
    increase_applied: int
    available_points_before: int
    available_points_after: int
    attribute_before: int
    attribute_after: int
    stage_code_at_allocation: str
    created_at: datetime

    @property
    def attribute_label(self):
        return dict(zip(STAT_ATTRIBUTES, ("ATK", "DEF", "LOG", "SPE", "VEL", "INT")))[self.attribute]


@dataclass(frozen=True)
class StatAllocationHistoryPage:
    entries: tuple[StatAllocationHistoryEntry, ...]
    has_more: bool
    next_before_id: int | None


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _numbers(instance, names, using):
    for name in names:
        value = getattr(instance, name)
        field = instance._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (not _integer(value) or (lower is not None and value < lower)
                or (upper is not None and value > upper)):
            raise ValidationError("Entero persistido inválido.")
        field.validate(value, instance)
        field.run_validators(value)


def _code(value):
    return isinstance(value, str) and 1 <= len(value) <= 32


def _read_profile(profile, using):
    current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
    if current is None:
        raise InvalidQueryProfileError("El perfil ya no existe.")
    stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
    if stats is None:
        raise InconsistentQueryStateError("Perfil sin estadísticas.")
    _numbers(current, ("id", "historical_xp_total", "current_level"), using)
    _numbers(stats, (*STAT_ATTRIBUTES, "available_points"), using)
    if not _code(current.current_stage_code) or (
        current.active_specialization_code is not None and not _code(current.active_specialization_code)
    ):
        raise ValidationError("Código persistido inválido.")
    return current


def _entry(event, profile_id, using):
    _numbers(event, ("id", "points_spent", "increase_applied", "available_points_before",
                     "available_points_after", "attribute_before", "attribute_after"), using)
    if (event._state.adding or event._state.db != using
            or not _integer(event.profile_id) or event.profile_id != profile_id or event.pk <= 0
            or not isinstance(event.attribute, str) or event.attribute not in STAT_ATTRIBUTES
            or not _code(event.stage_code_at_allocation)
            or not isinstance(event.created_at, datetime)
            or event.increase_applied != event.points_spent
            or event.available_points_before != event.available_points_after + event.points_spent
            or event.attribute_after != event.attribute_before + event.increase_applied):
        raise ValidationError("Snapshot histórico incompatible.")
    return StatAllocationHistoryEntry(**{
        name: getattr(event, name) for name in StatAllocationHistoryEntry.__dataclass_fields__
    })


def list_stat_allocation_history(profile, *, limit=50, before_id=None):
    """Página por PK descendente; no promete un snapshot conjunto entre lecturas."""
    if (not isinstance(profile, UserProfileEcomotor) or not _integer(profile.pk)
            or profile.pk <= 0 or profile._state.adding or profile._state.db not in connections):
        raise InvalidQueryProfileError("Se requiere un perfil persistido.")
    using = profile._state.db
    maximum = connections[using].ops.integer_field_range("BigAutoField")[1]
    if profile.pk > maximum:
        raise InvalidQueryProfileError("Identificador no representable.")
    if (not _integer(limit) or not 1 <= limit <= 100 or (before_id is not None and (
        not _integer(before_id) or not 1 <= before_id <= maximum
    ))):
        raise InvalidHistoryParametersError("Paginación inválida.")
    try:
        current = _read_profile(profile, using)
        query = StatAllocationEvent.objects.using(using).filter(profile_id=current.pk)
        if before_id is not None:
            query = query.filter(pk__lt=before_id)
        rows = list(query.order_by("-pk")[:limit + 1])
        # También validar la fila adicional: no esconder corrupción en el cursor.
        entries = tuple(_entry(row, current.pk, using) for row in rows)
    except ValidationError as error:
        raise InconsistentQueryStateError("Estructura de progreso o historial inválida.") from error
    except DatabaseError as error:
        raise ProgressQueryDatabaseError("Historial no disponible.") from error
    has_more = len(entries) > limit
    entries = entries[:limit]
    return StatAllocationHistoryPage(entries, has_more, entries[-1].id if has_more else None)
