"""S2-A: pareja local perfil/stats, sin provisionamiento global ni recompensas."""

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections, transaction

from apps.users.models import UserProfileEcomotor

from . import initialization_config
from .catalog_validation import validate_evolution_stage_catalog, validate_level_catalog
from .models import CharacterStats, EvolutionStage, LevelThreshold


class InvalidUserError(ValueError):
    """User incorrecto, no persistido o inexistente."""


class InvalidInitializationConfigError(ValueError):
    """Configuración inicial o catálogos ausentes/inválidos."""


class InconsistentInitializationStateError(ValueError):
    """Estado parcial o estructura legacy/inválida; nunca se repara aquí."""


class InitializationDatabaseError(RuntimeError):
    """Fallo de BD con rollback; el llamador decide un retry en nueva transacción."""


@dataclass(frozen=True)
class InitializationResult:
    profile_id: int
    character_stats_id: int
    created: bool


_ATTRIBUTES = ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat")


def _configuration(using):
    config = initialization_config.INITIAL_CONFIGURATION
    if not isinstance(config, initialization_config.InitializationConfiguration):
        raise InvalidInitializationConfigError("Falta configuración inicial autorizada.")
    for name in _ATTRIBUTES:
        value = getattr(config, name)
        field = CharacterStats._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (
            not isinstance(value, int) or isinstance(value, bool)
            or (lower is not None and value < lower)
            or (upper is not None and value > upper)
        ):
            raise InvalidInitializationConfigError("Atributos iniciales inválidos: " + name)
    codes = config.ordered_stage_codes
    if (
        not isinstance(codes, tuple) or len(codes) != 7
        or any(not isinstance(code, str) or not 1 <= len(code) <= 32 for code in codes)
        or len(set(codes)) != 7
    ):
        raise InvalidInitializationConfigError("Correspondencia funcional de etapas inválida.")
    return config


def _existing_result(profile, using):
    stats = CharacterStats.objects.using(using).filter(profile_id=profile.pk).first()
    if stats is None:
        raise InconsistentInitializationStateError("Perfil existente sin CharacterStats.")
    try:
        # Estructura de campos; no reinterpreta catálogos ni progresión histórica.
        profile.full_clean(validate_unique=False, validate_constraints=False)
        stats.full_clean(validate_unique=False, validate_constraints=False)
    except ValidationError as error:
        raise InconsistentInitializationStateError("Estructura de progreso inválida.") from error
    return InitializationResult(profile.pk, stats.pk, False)


def ensure_ecomotor_initialized(user):
    """Inicializa una vez en la BD del User existente; devuelve IDs sin reset."""
    user_model = get_user_model()
    if (
        not isinstance(user, user_model) or user.pk is None or user._state.adding
        or user._state.db not in connections
    ):
        raise InvalidUserError("Se requiere un User persistido.")
    using = user._state.db
    try:
        user_model._meta.pk.clean(user.pk, user)
    except (ValidationError, TypeError, ValueError) as error:
        raise InvalidUserError("Identificador de User inválido.") from error
    try:
        # D-19: BEGIN IMMEDIATE antes de cualquier lectura mutable en SQLite.
        with transaction.atomic(using=using):
            if not user_model.objects.using(using).filter(pk=user.pk).exists():
                raise InvalidUserError("El User ya no existe.")
            profile = UserProfileEcomotor.objects.using(using).filter(user_id=user.pk).first()
            if profile is not None:
                return _existing_result(profile, using)
            config = _configuration(using)
            levels = list(LevelThreshold.objects.using(using).all())
            stages = list(EvolutionStage.objects.using(using).all())
            try:
                validate_level_catalog(levels)
                validate_evolution_stage_catalog(
                    stages, ordered_stage_codes=config.ordered_stage_codes,
                )
            except ValidationError as error:
                raise InvalidInitializationConfigError("Catálogos iniciales inválidos.") from error
            first_level = next(level for level in levels if level.level == 1)
            first_stage = next(stage for stage in stages if stage.ordinal == 1)
            profile = UserProfileEcomotor.objects.using(using).create(
                user_id=user.pk, historical_xp_total=0, current_level=first_level.level,
                current_stage_code=first_stage.code, active_specialization_code=None,
            )
            stats = CharacterStats.objects.using(using).create(
                profile_id=profile.pk, available_points=first_level.stat_points_awarded,
                **{name: getattr(config, name) for name in _ATTRIBUTES},
            )
            return InitializationResult(profile.pk, stats.pk, True)
    except DatabaseError as error:
        # Fuera de atomic(): rollback ya efectuado, también si falla COMMIT/lock.
        raise InitializationDatabaseError("Inicialización abortada por error de BD.") from error
