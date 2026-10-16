"""S7-A: gasto local 1:1, evento persistente y replay sin reinterpretación."""

from dataclasses import dataclass, fields
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections, transaction

from apps.users.models import UserProfileEcomotor

from . import initialization_config, progression
from .catalog_validation import validate_evolution_stage_catalog
from .models import CharacterStats, EvolutionStage, STAT_ATTRIBUTES, StatAllocationEvent


class InvalidAllocationProfileError(ValueError):
    """Perfil no persistido o inexistente."""


class InvalidAttributeError(ValueError):
    """Nombre persistido no permitido."""


class InvalidPointsError(ValueError):
    """Cantidad de entrada no válida/representable."""


class InvalidAllocationKeyError(ValueError):
    """Clave no válida, sin normalización."""


class InvalidAllocationConfigurationError(ValueError):
    """Correspondencia o catálogo de etapas ausente/inválido."""


class IneligibleStageError(ValueError):
    """Perfil coherente en etapa anterior a Actual."""


class InsufficientPointsError(ValueError):
    """Saldo insuficiente al adquirir la transacción."""


class AllocationConflictError(ValueError):
    """Clave ya utilizada para otros parámetros."""


class InconsistentAllocationStateError(ValueError):
    """Estado persistido/histórico incoherente, sin reparación."""


class AllocationOverflowError(OverflowError):
    """Resultado o snapshot no representable técnicamente."""


class AllocationDatabaseError(RuntimeError):
    """Fallo real de BD, causa preservada y rollback completo."""


@dataclass(frozen=True)
class StatAllocationResult:
    replayed: bool
    profile_id: int
    allocation_event_id: int
    operation_key: str
    attribute: str
    points_spent: int
    increase_applied: int
    available_points_before: int
    available_points_after: int
    attribute_before: int
    attribute_after: int
    stage_code_at_allocation: str


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _fits(value, model, name, using):
    field = model._meta.get_field(name)
    lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
    if (lower is not None and value < lower) or (upper is not None and value > upper):
        raise AllocationOverflowError("Valor fuera del rango técnico persistible.")


def _numbers(instance, names, using):
    for name in names:
        value = getattr(instance, name)
        if not _integer(value):
            raise InconsistentAllocationStateError("Campos persistidos no enteros.")
        try:
            _fits(value, type(instance), name, using)
            field = instance._meta.get_field(name)
            field.validate(value, instance)
            field.run_validators(value)
        except (ValidationError, AllocationOverflowError) as error:
            raise InconsistentAllocationStateError("Campos persistidos inválidos.") from error


def _code(value):
    return isinstance(value, str) and 1 <= len(value) <= 32


def _structure(profile, stats, using):
    if stats is None:
        raise InconsistentAllocationStateError("Perfil sin CharacterStats.")
    _numbers(profile, ("historical_xp_total", "current_level"), using)
    _numbers(stats, (*STAT_ATTRIBUTES, "available_points"), using)
    if not _code(profile.current_stage_code) or (
        profile.active_specialization_code is not None and not _code(profile.active_specialization_code)
    ):
        raise InconsistentAllocationStateError("Códigos persistidos inválidos.")


def _eligible(profile, using):
    config = initialization_config.INITIAL_CONFIGURATION
    if not isinstance(config, initialization_config.InitializationConfiguration):
        raise InvalidAllocationConfigurationError("Falta correspondencia confiable de etapas.")
    codes = config.ordered_stage_codes
    if (not isinstance(codes, tuple) or len(codes) != 7
            or any(not _code(code) for code in codes) or len(set(codes)) != 7):
        raise InvalidAllocationConfigurationError("Correspondencia de etapas inválida.")
    stages = list(EvolutionStage.objects.using(using).order_by("ordinal"))
    try:
        for row in stages:
            _numbers(row, ("ordinal", "minimum_xp"), using)
        validate_evolution_stage_catalog(stages, ordered_stage_codes=codes)
        resolved = progression.resolve_stage(profile.historical_xp_total, [
            progression.StageDefinition(row.code, row.ordinal, row.minimum_xp) for row in stages
        ], ordered_stage_codes=codes)
    except (ValidationError, InconsistentAllocationStateError,
            progression.InvalidCatalogError, progression.InvalidXPError) as error:
        raise InvalidAllocationConfigurationError("Catálogo de etapas inválido.") from error
    if resolved != profile.current_stage_code:
        raise InconsistentAllocationStateError("Etapa persistida incompatible con XP/catálogo.")
    if resolved != codes[6]:
        raise IneligibleStageError("La asignación requiere la etapa Actual.")


def _validate_event(event, profile, key, using):
    if (not _integer(event.pk) or event.pk <= 0 or event._state.adding
            or event._state.db != using or event.profile_id != profile.pk
            or not isinstance(event.operation_key, str) or event.operation_key != key
            or not 1 <= len(event.operation_key) <= 255
            or event.attribute not in STAT_ATTRIBUTES
            or not isinstance(event.attribute, str)
            or not _code(event.stage_code_at_allocation)
            or not isinstance(event.created_at, datetime)):
        raise InconsistentAllocationStateError("Identidad/estructura histórica incompatible.")
    _numbers(event, ("points_spent", "increase_applied", "available_points_before",
                     "available_points_after", "attribute_before", "attribute_after"), using)
    if (event.increase_applied != event.points_spent
            or event.available_points_before != event.available_points_after + event.points_spent
            or event.attribute_after != event.attribute_before + event.increase_applied):
        raise InconsistentAllocationStateError("Snapshots históricos incompatibles.")


def _result(event, replayed):
    return StatAllocationResult(replayed=replayed, allocation_event_id=event.pk, **{
        field.name: getattr(event, field.name) for field in fields(StatAllocationResult)
        if field.name not in ("replayed", "allocation_event_id")
    })


def allocate_stat_points(profile, attribute, points, operation_key):
    """Gasta una vez o recupera snapshots originales, nunca inicializa ni repara."""
    if (not isinstance(profile, UserProfileEcomotor) or not _integer(profile.pk)
            or profile.pk <= 0 or profile._state.adding or profile._state.db not in connections):
        raise InvalidAllocationProfileError("Se requiere perfil persistido.")
    if not isinstance(attribute, str) or attribute not in STAT_ATTRIBUTES:
        raise InvalidAttributeError("Atributo no permitido.")
    if not _integer(points) or points <= 0:
        raise InvalidPointsError("points debe ser entero positivo sin bool.")
    if not isinstance(operation_key, str) or not 1 <= len(operation_key) <= 255:
        raise InvalidAllocationKeyError("Clave inválida.")
    using = profile._state.db
    try:
        _fits(points, StatAllocationEvent, "points_spent", using)
    except AllocationOverflowError as error:
        raise InvalidPointsError("Cantidad no representable.") from error
    try:
        with transaction.atomic(using=using):
            # D-19: BEGIN IMMEDIATE antes de leer perfil, stats, clave o saldo.
            current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
            if current is None:
                raise InvalidAllocationProfileError("El perfil ya no existe.")
            stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
            _structure(current, stats, using)
            event = StatAllocationEvent.objects.using(using).filter(
                profile_id=current.pk, operation_key=operation_key,
            ).first()
            if event is not None:
                _validate_event(event, current, operation_key, using)
                if event.attribute != attribute or event.points_spent != points:
                    raise AllocationConflictError("Clave utilizada para otra asignación.")
                return _result(event, True)
            _eligible(current, using)
            if points > stats.available_points:
                raise InsufficientPointsError("Saldo insuficiente.")
            before = getattr(stats, attribute)
            after = before + points
            balance_after = stats.available_points - points
            _fits(after, CharacterStats, attribute, using)
            values = dict(
                profile_id=current.pk, operation_key=operation_key, attribute=attribute,
                points_spent=points, increase_applied=points,
                available_points_before=stats.available_points, available_points_after=balance_after,
                attribute_before=before, attribute_after=after,
                stage_code_at_allocation=current.current_stage_code,
            )
            for name in ("points_spent", "increase_applied", "available_points_before",
                         "available_points_after", "attribute_before", "attribute_after"):
                _fits(values[name], StatAllocationEvent, name, using)
            event = StatAllocationEvent.objects.using(using).create(**values)
            setattr(stats, attribute, after)
            stats.available_points = balance_after
            stats.save(using=using, update_fields=[attribute, "available_points"])
            return _result(event, False)
    except DatabaseError as error:
        raise AllocationDatabaseError("Asignación abortada por fallo de BD.") from error
