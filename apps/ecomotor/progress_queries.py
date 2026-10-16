"""S4-A: lecturas locales, sin escrituras ni snapshot transaccional conjunto."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections

from apps.users.models import UserProfileEcomotor

from . import initialization_config, progression
from .catalog_validation import validate_evolution_stage_catalog, validate_level_catalog
from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent


class InvalidQueryProfileError(ValueError):
    """Perfil incorrecto, no persistido o inexistente."""


class InconsistentQueryStateError(ValueError):
    """Estructura parcial/inválida o historial causalmente incompatible."""


class InvalidHistoryParametersError(ValueError):
    """Parámetros fuera de los límites técnicos de paginación V1."""


class ProgressQueryDatabaseError(RuntimeError):
    """Fallo real de BD, con causa preservada; nunca se oculta como UNAVAILABLE."""


class GoalState(str, Enum):
    CALCULABLE = "CALCULABLE"
    COMPLETED = "COMPLETED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GoalProjection:
    state: GoalState
    level: int | None = None
    stage_code: str | None = None
    minimum_xp: int | None = None
    remaining_xp: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ProgressOverview:
    profile_id: int
    historical_xp_total: int
    current_level: int
    current_stage_code: str
    atk: int
    def_stat: int
    log_stat: int
    spe: int
    vel: int
    int_stat: int
    available_points: int
    next_level: GoalProjection
    next_stage: GoalProjection


@dataclass(frozen=True)
class EvolutionHistoryEntry:
    id: int
    xp_event_id: int
    stage_id: int
    created_at: datetime


@dataclass(frozen=True)
class XPHistoryEntry:
    id: int
    profile_id: int
    operation_key: str
    amount: int
    xp_before: int
    xp_after: int
    created_at: datetime
    evolutions: tuple[EvolutionHistoryEntry, ...]


@dataclass(frozen=True)
class ProgressHistoryPage:
    entries: tuple[XPHistoryEntry, ...]
    has_more: bool
    next_before_id: int | None


_STATS = ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points")


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_numbers(instance, names, using):
    for name in names:
        value = getattr(instance, name)
        if not _integer(value):
            raise ValidationError("Campo persistido no entero: " + name)
        field = instance._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (lower is not None and value < lower) or (upper is not None and value > upper):
            raise ValidationError("Campo persistido fuera de rango: " + name)
        # Sin clean()/to_python(): no convertir valores legacy silenciosamente.
        field.validate(value, instance)
        field.run_validators(value)


def _read_profile(profile):
    if (
        not isinstance(profile, UserProfileEcomotor) or profile.pk is None
        or profile._state.adding or profile._state.db not in connections
    ):
        raise InvalidQueryProfileError("Se requiere un perfil persistido.")
    try:
        UserProfileEcomotor._meta.pk.clean(profile.pk, profile)
    except (ValidationError, TypeError, ValueError) as error:
        raise InvalidQueryProfileError("Identificador de perfil inválido.") from error
    using = profile._state.db
    current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
    if current is None:
        raise InvalidQueryProfileError("El perfil ya no existe.")
    stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
    if stats is None:
        raise InconsistentQueryStateError("Perfil sin CharacterStats.")
    try:
        _validate_numbers(current, ("historical_xp_total", "current_level"), using)
        _validate_numbers(stats, _STATS, using)
        for name in ("current_stage_code", "active_specialization_code"):
            value = getattr(current, name)
            if value is not None and not isinstance(value, str):
                raise ValidationError("Código persistido inválido.")
            field = current._meta.get_field(name)
            field.validate(value, current)
            field.run_validators(value)
    except ValidationError as error:
        raise InconsistentQueryStateError("Estructura de progreso inválida.") from error
    return current, stats, using


def _unavailable(reason):
    return GoalProjection(GoalState.UNAVAILABLE, reason=reason)


def _next_level(profile, using):
    try:
        levels = list(LevelThreshold.objects.using(using).order_by("level"))
        for row in levels:
            _validate_numbers(row, ("level", "minimum_xp", "stat_points_awarded"), using)
        validate_level_catalog(levels)
        resolved = progression.resolve_level(profile.historical_xp_total, [
            progression.LevelDefinition(row.level, row.minimum_xp, row.stat_points_awarded)
            for row in levels
        ])
    except (ValidationError, progression.InvalidCatalogError, progression.InvalidXPError):
        return _unavailable("INVALID_LEVEL_CATALOG")
    if resolved != profile.current_level:
        return _unavailable("LEVEL_STATE_MISMATCH")
    following = next((row for row in levels if row.level > resolved), None)
    if following is None:
        return GoalProjection(GoalState.COMPLETED)
    return GoalProjection(
        GoalState.CALCULABLE, level=following.level, minimum_xp=following.minimum_xp,
        remaining_xp=following.minimum_xp - profile.historical_xp_total,
    )


def _next_stage(profile, using):
    config = initialization_config.INITIAL_CONFIGURATION
    if config is None:
        return _unavailable("STAGE_CONFIGURATION_UNAVAILABLE")
    if not isinstance(config, initialization_config.InitializationConfiguration):
        return _unavailable("INVALID_STAGE_CONFIGURATION")
    codes = config.ordered_stage_codes
    if (
        not isinstance(codes, tuple) or len(codes) != 7
        or any(not isinstance(code, str) or not 1 <= len(code) <= 32 for code in codes)
        or len(set(codes)) != 7
    ):
        return _unavailable("INVALID_STAGE_CONFIGURATION")
    try:
        stages = list(EvolutionStage.objects.using(using).order_by("ordinal"))
        for row in stages:
            _validate_numbers(row, ("ordinal", "minimum_xp"), using)
        validate_evolution_stage_catalog(stages, ordered_stage_codes=codes)
        resolved = progression.resolve_stage(profile.historical_xp_total, [
            progression.StageDefinition(row.code, row.ordinal, row.minimum_xp) for row in stages
        ], ordered_stage_codes=codes)
    except (ValidationError, progression.InvalidCatalogError, progression.InvalidXPError):
        return _unavailable("INVALID_STAGE_CATALOG")
    if resolved != profile.current_stage_code:
        return _unavailable("STAGE_STATE_MISMATCH")
    ordinal = next(row.ordinal for row in stages if row.code == resolved)
    following = next((row for row in stages if row.ordinal > ordinal), None)
    if following is None:
        return GoalProjection(GoalState.COMPLETED)
    return GoalProjection(
        GoalState.CALCULABLE, stage_code=following.code, minimum_xp=following.minimum_xp,
        remaining_xp=following.minimum_xp - profile.historical_xp_total,
    )


def get_progress_overview(profile):
    """Estado actual y objetivos independientes; sin snapshot conjunto garantizado."""
    try:
        current, stats, using = _read_profile(profile)
        return ProgressOverview(
            profile_id=current.pk, historical_xp_total=current.historical_xp_total,
            current_level=current.current_level, current_stage_code=current.current_stage_code,
            **{name: getattr(stats, name) for name in _STATS},
            next_level=_next_level(current, using), next_stage=_next_stage(current, using),
        )
    except DatabaseError as error:
        raise ProgressQueryDatabaseError("Consulta de progreso fallida.") from error


def _history_entry(event, evolutions, using):
    try:
        _validate_numbers(event, ("amount", "xp_before", "xp_after"), using)
    except ValidationError as error:
        raise InconsistentQueryStateError("Snapshots históricos inválidos.") from error
    if (
        event.xp_after != event.xp_before + event.amount
        or not isinstance(event.operation_key, str) or not 1 <= len(event.operation_key) <= 255
        or not isinstance(event.created_at, datetime)
    ):
        raise InconsistentQueryStateError("XPEvent histórico inválido.")
    return XPHistoryEntry(
        event.pk, event.profile_id, event.operation_key, event.amount,
        event.xp_before, event.xp_after, event.created_at, tuple(evolutions),
    )


def list_progress_history(profile, *, limit=50, before_id=None):
    """Página por PK descendente; solo snapshots e IDs persistidos de su propietario."""
    if not _integer(limit) or not 1 <= limit <= 100:
        raise InvalidHistoryParametersError("limit debe ser entero entre 1 y 100, sin bool.")
    if before_id is not None and (not _integer(before_id) or before_id <= 0):
        raise InvalidHistoryParametersError("before_id debe ser entero positivo, sin bool.")
    try:
        current, _, using = _read_profile(profile)
        if EvolutionEvent.objects.using(using).filter(profile_id=current.pk).exclude(
            xp_event__profile_id=current.pk,
        ).exists():
            raise InconsistentQueryStateError("Evolución del perfil con causa ajena.")
        events = XPEvent.objects.using(using).filter(profile_id=current.pk)
        if before_id is not None:
            events = events.filter(pk__lt=before_id)
        selected = list(events.order_by("-pk")[:limit + 1])
        has_more = len(selected) > limit
        selected = selected[:limit]
        groups = {event.pk: [] for event in selected}
        if groups:
            evolutions = EvolutionEvent.objects.using(using).filter(
                xp_event_id__in=groups,
            ).order_by("pk")
            for row in evolutions:
                if row.profile_id != current.pk or not isinstance(row.created_at, datetime):
                    raise InconsistentQueryStateError("Evolución con perfil/estructura incompatible.")
                groups[row.xp_event_id].append(EvolutionHistoryEntry(
                    row.pk, row.xp_event_id, row.stage_id, row.created_at,
                ))
        return ProgressHistoryPage(
            tuple(_history_entry(event, groups[event.pk], using) for event in selected),
            has_more, selected[-1].pk if has_more else None,
        )
    except DatabaseError as error:
        raise ProgressQueryDatabaseError("Consulta de historial fallida.") from error
