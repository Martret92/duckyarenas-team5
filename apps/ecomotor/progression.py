"""Cálculos S1 sobre configuración preparada, sin Django ni acceso a persistencia.

Los enteros de Python no tienen aquí un límite de juego o de almacenamiento.
La adaptación a campos persistentes y la consistencia de configuración son
responsabilidad de la futura operación S3. Ningún cálculo concede recompensas.
"""

from dataclasses import dataclass
from typing import Iterable, Sequence


class InvalidXPError(ValueError):
    """Total de XP inválido o progresión decreciente."""


class InvalidCatalogError(ValueError):
    """Configuración completa inválida o incoherente."""


@dataclass(frozen=True)
class LevelDefinition:
    level: int
    minimum_xp: int
    stat_points_awarded: int


@dataclass(frozen=True)
class StageDefinition:
    code: str
    ordinal: int
    minimum_xp: int


@dataclass(frozen=True)
class ProgressionResult:
    xp_before: int
    xp_after: int
    level_before: int
    level_after: int
    stage_before_code: str
    stage_after_code: str
    crossed_levels: tuple[LevelDefinition, ...]
    crossed_stages: tuple[StageDefinition, ...]
    total_stat_points_awarded: int


def _nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_xp(value):
    if not _nonnegative_integer(value):
        raise InvalidXPError("La XP debe ser un entero no negativo, excluyendo booleanos.")


def _snapshot(values):
    if isinstance(values, (str, bytes)):
        raise InvalidCatalogError("Se requiere una colección de definiciones o códigos.")
    try:
        return tuple(values)
    except TypeError as error:
        raise InvalidCatalogError("El catálogo debe ser una colección preparada.") from error


def _validate_levels(levels):
    definitions = _snapshot(levels)
    if not definitions:
        raise InvalidCatalogError("El catálogo de niveles está vacío.")
    for item in definitions:
        if not isinstance(item, LevelDefinition):
            raise InvalidCatalogError("Se requieren objetos LevelDefinition.")
        if not _nonnegative_integer(item.level) or item.level == 0:
            raise InvalidCatalogError("Los niveles deben ser enteros positivos.")
        if not _nonnegative_integer(item.minimum_xp):
            raise InvalidCatalogError("Los umbrales deben ser enteros no negativos.")
        if not _nonnegative_integer(item.stat_points_awarded):
            raise InvalidCatalogError("Los puntos deben ser enteros no negativos.")
    ordered = tuple(sorted(definitions, key=lambda item: item.level))
    if tuple(item.level for item in ordered) != tuple(range(1, len(ordered) + 1)):
        raise InvalidCatalogError("Los niveles deben ser consecutivos desde 1, sin duplicados.")
    if ordered[0].minimum_xp != 0:
        raise InvalidCatalogError("El nivel 1 debe comenzar en 0 XP.")
    if any(left.minimum_xp >= right.minimum_xp for left, right in zip(ordered, ordered[1:])):
        raise InvalidCatalogError("Los umbrales de nivel deben crecer estrictamente.")
    return ordered


def _valid_code(code):
    # Mismo requisito de cadena no vacía y longitud del CharField existente.
    return isinstance(code, str) and 1 <= len(code) <= 32


def _validate_stages(stages, ordered_stage_codes):
    definitions = _snapshot(stages)
    codes = _snapshot(ordered_stage_codes)
    if len(codes) != 7 or any(not _valid_code(code) for code in codes):
        raise InvalidCatalogError("Se requieren siete códigos no vacíos de hasta 32 caracteres.")
    if len(set(codes)) != 7:
        raise InvalidCatalogError("Los códigos configurados deben ser únicos.")
    if len(definitions) != 7:
        raise InvalidCatalogError("El catálogo debe contener exactamente siete etapas.")
    for item in definitions:
        if not isinstance(item, StageDefinition):
            raise InvalidCatalogError("Se requieren objetos StageDefinition.")
        if not _nonnegative_integer(item.ordinal) or not 1 <= item.ordinal <= 7:
            raise InvalidCatalogError("Los ordinales deben ser enteros del 1 al 7.")
        if not _valid_code(item.code) or not _nonnegative_integer(item.minimum_xp):
            raise InvalidCatalogError("Código o umbral de etapa inválido.")
    ordered = tuple(sorted(definitions, key=lambda item: item.ordinal))
    if tuple(item.ordinal for item in ordered) != tuple(range(1, 8)):
        raise InvalidCatalogError("Los ordinales deben ser consecutivos, sin duplicados.")
    if tuple(item.code for item in ordered) != codes:
        raise InvalidCatalogError("Las etapas no siguen la correspondencia funcional configurada.")
    if ordered[0].minimum_xp != 0:
        raise InvalidCatalogError("La primera etapa debe comenzar en 0 XP.")
    if any(left.minimum_xp >= right.minimum_xp for left, right in zip(ordered, ordered[1:])):
        raise InvalidCatalogError("Los umbrales de etapa deben crecer estrictamente.")
    return ordered


def _resolve(xp_total, definitions):
    return next(item for item in reversed(definitions) if item.minimum_xp <= xp_total)


def resolve_level(xp_total: int, levels: Iterable[LevelDefinition]) -> int:
    """Resuelve el mayor nivel alcanzado, incluyendo la igualdad con su umbral."""
    _validate_xp(xp_total)
    return _resolve(xp_total, _validate_levels(levels)).level


def resolve_stage(
    xp_total: int, stages: Iterable[StageDefinition], *, ordered_stage_codes: Sequence[str]
) -> str:
    """Resuelve la etapa; los códigos se reciben en el orden funcional documentado."""
    _validate_xp(xp_total)
    return _resolve(xp_total, _validate_stages(stages, ordered_stage_codes)).code


def calculate_progression(
    xp_before: int,
    xp_after: int,
    levels: Iterable[LevelDefinition],
    stages: Iterable[StageDefinition],
    *,
    ordered_stage_codes: Sequence[str],
) -> ProgressionResult:
    """Calcula todas las transiciones entre totales; excluye puntos del nivel inicial."""
    _validate_xp(xp_before)
    _validate_xp(xp_after)
    if xp_after < xp_before:
        raise InvalidXPError("La XP histórica no puede disminuir.")
    ordered_levels = _validate_levels(levels)
    ordered_stages = _validate_stages(stages, ordered_stage_codes)
    crossed_levels = tuple(
        item for item in ordered_levels if xp_before < item.minimum_xp <= xp_after
    )
    crossed_stages = tuple(
        item for item in ordered_stages if xp_before < item.minimum_xp <= xp_after
    )
    return ProgressionResult(
        xp_before=xp_before,
        xp_after=xp_after,
        level_before=_resolve(xp_before, ordered_levels).level,
        level_after=_resolve(xp_after, ordered_levels).level,
        stage_before_code=_resolve(xp_before, ordered_stages).code,
        stage_after_code=_resolve(xp_after, ordered_stages).code,
        crossed_levels=crossed_levels,
        crossed_stages=crossed_stages,
        total_stat_points_awarded=sum(item.stat_points_awarded for item in crossed_levels),
    )
