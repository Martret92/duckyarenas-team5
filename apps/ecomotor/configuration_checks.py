"""Diagnóstico técnico SELECT; no aprueba parámetros ni activa configuración."""

from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ValidationError
from django.db import DatabaseError, connections
from django.utils.connection import ConnectionDoesNotExist

from . import initialization_config
from .catalog_validation import validate_evolution_stage_catalog, validate_level_catalog
from .models import EvolutionStage, LevelThreshold


class ReadinessStatus(str, Enum):
    CONFIGURATION_MISSING = "CONFIGURATION_MISSING"
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    CATALOG_INCOMPLETE = "CATALOG_INCOMPLETE"
    INVALID_CATALOG = "INVALID_CATALOG"
    TECHNICALLY_READY = "TECHNICALLY_READY"


class ReadinessDatabaseError(RuntimeError):
    """Error operativo real con causa preservada."""


@dataclass(frozen=True)
class ReadinessIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ReadinessResult:
    status: ReadinessStatus
    issues: tuple[ReadinessIssue, ...]
    technically_consistent: bool


_CURRENT = object()


def _row_valid(row, names, using):
    for name in names:
        value = getattr(row, name)
        field = row._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (not isinstance(value, int) or isinstance(value, bool)
                or (lower is not None and value < lower)
                or (upper is not None and value > upper)):
            raise ValidationError("Tipo/rango persistido inválido.")
    # Sobre una copia recién leída; las funciones existentes no escriben.
    row.full_clean(validate_unique=False, validate_constraints=False)


def check_ecomotor_readiness(*, configuration=_CURRENT, using="default"):
    """Estado técnico, sin snapshot conjunto ni instalación del candidato."""
    if configuration is _CURRENT:
        configuration = initialization_config.INITIAL_CONFIGURATION
    try:
        connections[using]  # Alias inválido es fallo operativo incluso sin configuración.
        if configuration is None:
            return ReadinessResult(ReadinessStatus.CONFIGURATION_MISSING, (
                ReadinessIssue("CONFIGURATION_MISSING", "No hay configuración disponible."),), False)
        try:
            initialization_config._validate_configuration(configuration, using)
        except initialization_config.ConfigurationStructureError:
            return ReadinessResult(ReadinessStatus.INVALID_CONFIGURATION, (
                ReadinessIssue("INVALID_CONFIGURATION", "Parámetros técnicos inválidos."),), False)
        levels = list(LevelThreshold.objects.using(using).order_by("level"))
        stages = list(EvolutionStage.objects.using(using).order_by("ordinal"))
        issues = []
        invalid = False
        incomplete = False
        if not levels:
            incomplete = True
            issues.append(ReadinessIssue("LEVELS_MISSING", "El catálogo de niveles está vacío."))
        else:
            try:
                for row in levels:
                    _row_valid(row, ("level", "minimum_xp", "stat_points_awarded"), using)
                validate_level_catalog(levels)
            except ValidationError:
                invalid = True
                issues.append(ReadinessIssue("INVALID_LEVELS", "Niveles con filas o invariantes inválidas."))
        try:
            for row in stages:
                _row_valid(row, ("ordinal", "minimum_xp"), using)
                if row.code != configuration.ordered_stage_codes[row.ordinal - 1]:
                    raise ValidationError("Correspondencia incompatible.")
                if row.ordinal == 1 and row.minimum_xp != 0:
                    raise ValidationError("XP inicial incompatible.")
            if any(a.minimum_xp >= b.minimum_xp for a, b in zip(stages, stages[1:])):
                raise ValidationError("Umbrales incompatibles.")
            if len(stages) < 7:
                incomplete = True
                issues.append(ReadinessIssue("STAGES_MISSING", "El catálogo de etapas está incompleto."))
            else:
                validate_evolution_stage_catalog(stages, ordered_stage_codes=configuration.ordered_stage_codes)
        except ValidationError:
            invalid = True
            issues.append(ReadinessIssue("INVALID_STAGES", "Etapas con filas o correspondencia inválidas."))
        status = (ReadinessStatus.INVALID_CATALOG if invalid else
                  ReadinessStatus.CATALOG_INCOMPLETE if incomplete else ReadinessStatus.TECHNICALLY_READY)
        return ReadinessResult(status, tuple(issues), status == ReadinessStatus.TECHNICALLY_READY)
    except (DatabaseError, ConnectionDoesNotExist) as error:
        raise ReadinessDatabaseError("No se pudo consultar la base de datos seleccionada.") from error
