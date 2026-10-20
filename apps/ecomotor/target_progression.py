"""A1.2: cálculo objetivo sobre snapshot A1.1, sin activación o efectos V1.

La versión y los datos ya validados se reciben explícitamente. Nivel 8 permite
elegir, pero no selecciona una opción ni añade una época. No se leen ni suman los
puntos de las definiciones heredadas; no hay persistencia ni configuración global.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from .target_catalog_validation import InvalidTargetCatalogError, TargetCatalogSnapshot


class InvalidTargetXPError(ValueError):
    """XP no entera/no negativa o intervalo decreciente."""


@dataclass(frozen=True, slots=True)
class TargetProgressionResult:
    catalog_version: str
    xp_before: int
    xp_after: int
    level_before: int
    level_after: int
    epoch_before_code: str
    epoch_after_code: str
    crossed_levels: tuple[int, ...]
    crossed_epoch_codes: tuple[str, ...]
    choice_unlocked_before: bool
    choice_unlocked_after: bool
    choice_newly_unlocked: bool

    def __post_init__(self):
        # También protege la construcción directa frente a listas mutables/anidadas.
        for name in ("crossed_levels", "crossed_epoch_codes"):
            values = getattr(self, name)
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
                raise ValueError(f"{name}: se requiere una secuencia explícita.")
            values = tuple(values)
            if name == "crossed_levels":
                valid = all(type(value) is int and value > 0 for value in values)
            else:
                valid = all(type(value) is str and bool(value.strip()) for value in values)
            if not valid:
                raise ValueError(f"{name}: transición estructuralmente inválida.")
            object.__setattr__(self, name, values)


def _resolve(xp, rows):
    return next(row for row in reversed(rows) if row.minimum_xp <= xp)


def calculate_target_progression(
    xp_before: int, xp_after: int, catalog: TargetCatalogSnapshot,
) -> TargetProgressionResult:
    """Resuelve estados y todos los cruces xp_before < umbral <= xp_after.

    Solo acepta TargetCatalogSnapshot construido/validado por A1.1. No repite
    esa validación ni utiliza las reglas independientes o el cálculo de puntos V1.
    Los indicadores de elección son cálculos, no autorización ni selección persistida.
    """
    if (type(xp_before) is not int or type(xp_after) is not int
            or xp_before < 0 or xp_after < xp_before):
        raise InvalidTargetXPError("Se requieren totales XP enteros no negativos y no decrecientes.")
    if type(catalog) is not TargetCatalogSnapshot:
        raise InvalidTargetCatalogError("Se requiere un snapshot objetivo validado por A1.1.")
    level_before = _resolve(xp_before, catalog.levels).level
    level_after = _resolve(xp_after, catalog.levels).level
    unlocked_before = level_before >= 8
    unlocked_after = level_after >= 8
    return TargetProgressionResult(
        catalog_version=catalog.catalog_version,
        xp_before=xp_before, xp_after=xp_after,
        level_before=level_before, level_after=level_after,
        epoch_before_code=_resolve(xp_before, catalog.epochs).code,
        epoch_after_code=_resolve(xp_after, catalog.epochs).code,
        crossed_levels=tuple(row.level for row in catalog.levels if xp_before < row.minimum_xp <= xp_after),
        crossed_epoch_codes=tuple(row.code for row in catalog.epochs if xp_before < row.minimum_xp <= xp_after),
        choice_unlocked_before=unlocked_before,
        choice_unlocked_after=unlocked_after,
        choice_newly_unlocked=not unlocked_before and unlocked_after,
    )
