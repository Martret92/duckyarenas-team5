"""S11-A: primera selección local, atómica e idempotente por estado."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections, transaction

from apps.users.models import UserProfileEcomotor

from . import initialization_config, progression
from .catalog_validation import validate_evolution_stage_catalog
from .models import (
    CharacterStats, EvolutionStage, Specialization, STAT_ATTRIBUTES, UserSpecializationProgress,
)


class InvalidSpecializationProfileError(ValueError):
    """Perfil incorrecto, no persistido o inexistente."""


class InvalidSpecializationCodeError(ValueError):
    """Código de entrada inválido o especialización solicitada inexistente."""


class InvalidSpecializationConfigurationError(ValueError):
    """Configuración o catálogo de etapas ausente/inválido para una operación nueva."""


class IneligibleSpecializationStageError(ValueError):
    """Operación nueva solicitada antes de Actual."""


class SpecializationConflictError(ValueError):
    """Ya existe una selección coherente de otro código."""


class InconsistentSpecializationStateError(ValueError):
    """Estado parcial/incompatible: no se repara ni reinicia."""


class SpecializationDatabaseError(RuntimeError):
    """Fallo real de BD con causa preservada y rollback completo."""


@dataclass(frozen=True)
class SpecializationSelectionResult:
    profile_id: int
    specialization_id: int
    specialization_code: str
    progress_id: int
    created: bool


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _code(value):
    return isinstance(value, str) and 1 <= len(value) <= 32


def _numbers(instance, names, using):
    for name in names:
        value = getattr(instance, name)
        field = instance._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (not _integer(value) or (lower is not None and value < lower)
                or (upper is not None and value > upper)):
            raise ValidationError("Entero persistido no representable.")
        field.validate(value, instance)
        field.run_validators(value)


def _identity(instance, using):
    _numbers(instance, ("id",), using)
    if instance.pk <= 0 or instance._state.adding or instance._state.db != using:
        raise ValidationError("Identidad local persistida inválida.")


def _structure(profile, stats, using):
    if stats is None:
        raise ValidationError("Perfil sin CharacterStats.")
    _identity(profile, using)
    _identity(stats, using)
    _numbers(profile, ("historical_xp_total", "current_level"), using)
    _numbers(stats, (*STAT_ATTRIBUTES, "available_points"), using)
    if (stats.profile_id != profile.pk or not _code(profile.current_stage_code)
            or (profile.active_specialization_code is not None and not _code(profile.active_specialization_code))):
        raise ValidationError("Estructura de perfil/estadísticas incompatible.")
    # La identidad de User es opaca: no se valida ni consulta su representación.


def _specialization(row, using):
    _identity(row, using)
    for name in ("code", "name"):
        value = getattr(row, name)
        if not isinstance(value, str):
            raise ValidationError("Campo de especialización no textual.")
        field = row._meta.get_field(name)
        field.validate(value, row)
        field.run_validators(value)


def _existing_selection(profile, rows, using):
    if profile.active_specialization_code is None:
        if rows:
            raise ValidationError("Progreso sin selección activa.")
        return None
    selected = None
    identities, specializations, codes = set(), set(), set()
    for progress in rows:
        _identity(progress, using)
        _numbers(progress, ("domain_xp_total",), using)
        for name in ("profile", "specialization"):
            field = progress._meta.get_field(name)
            value = getattr(progress, field.attname)
            lower, upper = connections[using].ops.integer_field_range(field.target_field.get_internal_type())
            if (not _integer(value) or value <= 0 or (lower is not None and value < lower)
                    or (upper is not None and value > upper)):
                raise ValidationError("Referencia de progreso no representable.")
        if (progress.profile_id != profile.pk or progress.specialization_id <= 0
                or progress.pk in identities or progress.specialization_id in specializations):
            raise ValidationError("Propietario o referencia de progreso inválidos/duplicados.")
        specialization = Specialization.objects.using(using).filter(pk=progress.specialization_id).first()
        if specialization is None:
            raise ValidationError("Especialización referenciada inexistente.")
        _specialization(specialization, using)
        if specialization.code in codes:
            raise ValidationError("Códigos de especialización duplicados.")
        identities.add(progress.pk)
        specializations.add(progress.specialization_id)
        codes.add(specialization.code)
        if specialization.code == profile.active_specialization_code:
            selected = specialization, progress
    if selected is None:
        raise ValidationError("Selección sin progreso activo compatible.")
    return selected


def _eligible(profile, using):
    config = initialization_config.INITIAL_CONFIGURATION
    if not isinstance(config, initialization_config.InitializationConfiguration):
        raise InvalidSpecializationConfigurationError("Falta configuración de etapas.")
    codes = config.ordered_stage_codes
    if (not isinstance(codes, tuple) or len(codes) != 7
            or any(not _code(code) for code in codes) or len(set(codes)) != 7):
        raise InvalidSpecializationConfigurationError("Correspondencia de etapas inválida.")
    stages = list(EvolutionStage.objects.using(using).order_by("ordinal"))
    try:
        for row in stages:
            _numbers(row, ("ordinal", "minimum_xp"), using)
            if not isinstance(row.code, str) or not isinstance(row.name, str):
                raise ValidationError("Campos de etapa no textuales.")
        validate_evolution_stage_catalog(stages, ordered_stage_codes=codes)
        resolved = progression.resolve_stage(profile.historical_xp_total, [
            progression.StageDefinition(row.code, row.ordinal, row.minimum_xp) for row in stages
        ], ordered_stage_codes=codes)
    except (ValidationError, progression.InvalidCatalogError, progression.InvalidXPError) as error:
        raise InvalidSpecializationConfigurationError("Catálogo de etapas inválido.") from error
    if resolved != profile.current_stage_code:
        raise InconsistentSpecializationStateError("Etapa incompatible con XP persistida.")
    if resolved != codes[6]:
        raise IneligibleSpecializationStageError("La operación requiere Actual.")


def _result(profile, specialization, progress, created):
    return SpecializationSelectionResult(profile.pk, specialization.pk, specialization.code, progress.pk, created)


def _profile_alias(profile):
    if (not isinstance(profile, UserProfileEcomotor) or not _integer(profile.pk)
            or profile.pk <= 0 or profile._state.adding or profile._state.db not in connections):
        raise InvalidSpecializationProfileError("Se requiere un perfil persistido.")
    using = profile._state.db
    maximum = connections[using].ops.integer_field_range(UserProfileEcomotor._meta.pk.get_internal_type())[1]
    if profile.pk > maximum:
        raise InvalidSpecializationProfileError("Identificador local no representable.")
    return using


def select_initial_specialization(profile, specialization_code):
    """Selecciona una vez o recupera estado coherente; no concede XP de dominio."""
    using = _profile_alias(profile)
    if not _code(specialization_code):
        raise InvalidSpecializationCodeError("Código inválido.")
    try:
        with transaction.atomic(using=using):
            # D-19: BEGIN IMMEDIATE antes de leer cualquier estado mutable.
            current = UserProfileEcomotor.objects.using(using).filter(pk=profile.pk).first()
            if current is None:
                raise InvalidSpecializationProfileError("El perfil ya no existe.")
            stats = CharacterStats.objects.using(using).filter(profile_id=current.pk).first()
            try:
                _structure(current, stats, using)
                rows = list(UserSpecializationProgress.objects.using(using).filter(profile_id=current.pk))
                existing = _existing_selection(current, rows, using)
            except ValidationError as error:
                raise InconsistentSpecializationStateError("Selección/estado persistido incompatible.") from error
            if existing is not None:
                specialization, progress = existing
                if specialization.code != specialization_code:
                    raise SpecializationConflictError("La especialización activa no puede cambiarse.")
                return _result(current, specialization, progress, False)
            _eligible(current, using)
            specialization = Specialization.objects.using(using).filter(code=specialization_code).first()
            if specialization is None:
                raise InvalidSpecializationCodeError("Especialización solicitada inexistente.")
            try:
                _specialization(specialization, using)
            except ValidationError as error:
                raise InconsistentSpecializationStateError("Especialización persistida inválida.") from error
            current.active_specialization_code = specialization.code
            current.save(using=using, update_fields=["active_specialization_code"])
            progress = UserSpecializationProgress.objects.using(using).create(
                profile_id=current.pk, specialization_id=specialization.pk, domain_xp_total=0,
            )
            return _result(current, specialization, progress, True)
    except DatabaseError as error:
        raise SpecializationDatabaseError("Selección abortada por fallo de BD.") from error
