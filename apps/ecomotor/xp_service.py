"""S3 V1: XP histórica local, con replay persistente y cálculo exclusivo S1."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections, transaction
from django.db.models import F, Q

from apps.users.models import UserProfileEcomotor

from . import initialization_config, progression
from .catalog_validation import validate_evolution_stage_catalog, validate_level_catalog
from .models import CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, XPEvent


class InvalidProfileError(ValueError):
    """Perfil incorrecto, no persistido o inexistente."""


class InvalidXPAmountError(ValueError):
    """Importe distinto de un entero positivo, excluyendo bool."""


class InvalidOperationKeyError(ValueError):
    """Clave inválida; no se normaliza ni trunca."""


class IdempotencyConflictError(ValueError):
    """La clave persistida corresponde a otra cantidad."""


class InvalidXPConfigurationError(ValueError):
    """Catálogos o correspondencia funcional inválidos/ausentes."""


class InconsistentProgressError(ValueError):
    """Progreso parcial/incoherente; requiere revisión, no reparación automática."""


class XPOverflowError(OverflowError):
    """Valor no representable en el campo persistente del backend."""


class XPDatabaseError(RuntimeError):
    """Fallo real de BD con rollback y causa preservada."""


@dataclass(frozen=True)
class XPGrantResult:
    replayed: bool
    profile_id: int
    xp_event_id: int
    amount: int
    operation_key: str
    xp_before: int
    xp_after: int
    evolution_event_ids: tuple[int, ...]
    evolved_stage_ids: tuple[int, ...]
    level_before: int | None
    level_after: int | None
    stage_before_code: str | None
    stage_after_code: str | None
    crossed_levels: tuple[int, ...] | None
    crossed_stage_codes: tuple[str, ...] | None
    stat_points_awarded: int | None
    available_points_after: int | None


def _fits(value, model, field_name, using):
    field = model._meta.get_field(field_name)
    lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
    if (lower is not None and value < lower) or (upper is not None and value > upper):
        raise XPOverflowError("Fuera del rango técnico de " + model.__name__ + "." + field_name)


def _structure(profile, stats):
    if stats is None:
        raise InconsistentProgressError("El perfil no tiene CharacterStats; S3 no inicializa.")
    numeric = [profile.historical_xp_total, profile.current_level] + [
        getattr(stats, name) for name in
        ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points")
    ]
    # full_clean puede convertir floats a int: no normalizar datos legacy al leer.
    if any(not isinstance(value, int) or isinstance(value, bool) for value in numeric):
        raise InconsistentProgressError("Campos persistidos no enteros.")
    try:
        profile.full_clean(validate_unique=False, validate_constraints=False)
        stats.full_clean(validate_unique=False, validate_constraints=False)
    except ValidationError as error:
        raise InconsistentProgressError("Estructura de progreso inválida.") from error


def _causal_integrity(profile, using):
    # Incluye causas del perfil enlazadas indebidamente desde otro perfil.
    incompatible = EvolutionEvent.objects.using(using).filter(
        Q(profile_id=profile.pk) | Q(xp_event__profile_id=profile.pk),
    ).exclude(profile_id=F("xp_event__profile_id"))
    if incompatible.exists():
        raise InconsistentProgressError("Perfil de evolución distinto de su causa XP.")


def _catalogs(using):
    config = initialization_config.INITIAL_CONFIGURATION
    if not isinstance(config, initialization_config.InitializationConfiguration):
        raise InvalidXPConfigurationError("Falta correspondencia autorizada de etapas.")
    # Solo códigos: no valida ni utiliza los seis atributos iniciales de S2-A.
    codes = config.ordered_stage_codes
    if (
        not isinstance(codes, tuple) or len(codes) != 7
        or any(not isinstance(code, str) or not 1 <= len(code) <= 32 for code in codes)
        or len(set(codes)) != 7
    ):
        raise InvalidXPConfigurationError("Correspondencia funcional inválida.")
    levels = list(LevelThreshold.objects.using(using).all())
    stages = list(EvolutionStage.objects.using(using).all())
    try:
        validate_level_catalog(levels)
        validate_evolution_stage_catalog(stages, ordered_stage_codes=codes)
    except ValidationError as error:
        raise InvalidXPConfigurationError("Catálogos de progresión inválidos.") from error
    return levels, stages, codes


def _replay(profile, event, using):
    if any(not isinstance(value, int) or isinstance(value, bool) for value in
           (event.amount, event.xp_before, event.xp_after)):
        raise InconsistentProgressError("Snapshots históricos no enteros.")
    try:
        event.full_clean(validate_unique=False, validate_constraints=False)
    except ValidationError as error:
        raise InconsistentProgressError("XPEvent histórico inválido.") from error
    if (
        event.amount <= 0 or event.xp_after != event.xp_before + event.amount
        or event.xp_after > profile.historical_xp_total
    ):
        raise InconsistentProgressError("Snapshots históricos incompatibles.")
    # No join al catálogo: IDs persistidos en orden de inserción, no códigos actuales.
    evolutions = list(EvolutionEvent.objects.using(using).filter(
        xp_event_id=event.pk,
    ).order_by("pk").values_list("pk", "stage_id"))
    return XPGrantResult(
        replayed=True, profile_id=profile.pk, xp_event_id=event.pk,
        amount=event.amount, operation_key=event.operation_key,
        xp_before=event.xp_before, xp_after=event.xp_after,
        evolution_event_ids=tuple(row[0] for row in evolutions),
        evolved_stage_ids=tuple(row[1] for row in evolutions),
        level_before=None, level_after=None, stage_before_code=None, stage_after_code=None,
        crossed_levels=None, crossed_stage_codes=None, stat_points_awarded=None,
        available_points_after=None,
    )


def grant_historical_xp(profile, amount, operation_key):
    """Concede una vez o devuelve historia; nunca inicializa ni reinterpreta replay."""
    if (
        not isinstance(profile, UserProfileEcomotor) or profile.pk is None
        or profile._state.adding or profile._state.db not in connections
    ):
        raise InvalidProfileError("Se requiere un perfil persistido.")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise InvalidXPAmountError("amount debe ser entero positivo, sin bool.")
    if not isinstance(operation_key, str) or not 1 <= len(operation_key) <= 255:
        raise InvalidOperationKeyError("operation_key debe tener entre 1 y 255 caracteres.")
    try:
        UserProfileEcomotor._meta.pk.clean(profile.pk, profile)
    except (ValidationError, TypeError, ValueError) as error:
        raise InvalidProfileError("Identificador de perfil inválido.") from error
    using = profile._state.db
    try:
        with transaction.atomic(using=using):
            # BEGIN IMMEDIATE precede a la lectura; no se depende de bloqueo por fila.
            current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
            if current is None:
                raise InvalidProfileError("El perfil ya no existe.")
            stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
            _structure(current, stats)
            event = XPEvent.objects.using(using).filter(
                profile_id=current.pk, operation_key=operation_key,
            ).first()
            if event is not None and event.amount != amount:
                raise IdempotencyConflictError("La clave ya tiene otra cantidad.")
            _causal_integrity(current, using)
            if event is not None:
                return _replay(current, event, using)
            levels, stages, codes = _catalogs(using)
            xp_after = current.historical_xp_total + amount
            _fits(amount, XPEvent, "amount", using)
            _fits(xp_after, UserProfileEcomotor, "historical_xp_total", using)
            _fits(xp_after, XPEvent, "xp_after", using)
            try:
                change = progression.calculate_progression(
                    current.historical_xp_total, xp_after,
                    [progression.LevelDefinition(row.level, row.minimum_xp, row.stat_points_awarded)
                     for row in levels],
                    [progression.StageDefinition(row.code, row.ordinal, row.minimum_xp)
                     for row in stages], ordered_stage_codes=codes,
                )
            except (progression.InvalidCatalogError, progression.InvalidXPError) as error:
                raise InvalidXPConfigurationError("Configuración incompatible con S1.") from error
            if (current.current_level != change.level_before
                    or current.current_stage_code != change.stage_before_code):
                raise InconsistentProgressError("Progreso actual incompatible con XP/catálogos.")
            points_after = stats.available_points + change.total_stat_points_awarded
            _fits(change.level_after, UserProfileEcomotor, "current_level", using)
            _fits(points_after, CharacterStats, "available_points", using)
            stage_by_code = {stage.code: stage for stage in stages}
            crossed_ids = tuple(stage_by_code[row.code].pk for row in change.crossed_stages)
            if EvolutionEvent.objects.using(using).filter(
                profile_id=current.pk, stage_id__in=crossed_ids,
            ).exists():
                raise InconsistentProgressError("Una etapa cruzada ya consta en el historial.")
            event = XPEvent.objects.using(using).create(
                profile_id=current.pk, amount=amount, xp_before=change.xp_before,
                xp_after=change.xp_after, operation_key=operation_key,
            )
            evolution_ids = tuple(
                EvolutionEvent.objects.using(using).create(
                    profile_id=current.pk, stage_id=stage_id, xp_event_id=event.pk,
                ).pk for stage_id in crossed_ids
            )
            current.historical_xp_total = change.xp_after
            current.current_level = change.level_after
            current.current_stage_code = change.stage_after_code
            current.save(using=using, update_fields=[
                "historical_xp_total", "current_level", "current_stage_code",
            ])
            stats.available_points = points_after
            stats.save(using=using, update_fields=["available_points"])
            return XPGrantResult(
                replayed=False, profile_id=current.pk, xp_event_id=event.pk,
                amount=amount, operation_key=operation_key,
                xp_before=change.xp_before, xp_after=change.xp_after,
                evolution_event_ids=evolution_ids, evolved_stage_ids=crossed_ids,
                level_before=change.level_before, level_after=change.level_after,
                stage_before_code=change.stage_before_code, stage_after_code=change.stage_after_code,
                crossed_levels=tuple(row.level for row in change.crossed_levels),
                crossed_stage_codes=tuple(row.code for row in change.crossed_stages),
                stat_points_awarded=change.total_stat_points_awarded,
                available_points_after=points_after,
            )
    except DatabaseError as error:
        # atomic ya revirtió; jamás convertir una colisión/fallo en replay supuesto.
        raise XPDatabaseError("Concesión abortada por error de BD.") from error
