"""A1.1: correspondencia objetivo nivel–época, sin activar ni alterar V1.

Entradas: colecciones puras de LevelDefinition y StageDefinition, secuencia de
códigos explícitamente ordenada y versión no vacía. No se asignan nombres/códigos
oficiales ni umbrales de producción. Los puntos S1 se conservan, sin exigir cero.
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass

from .progression import LevelDefinition, StageDefinition


class InvalidTargetCatalogError(ValueError):
    """Estructura, versión o correspondencia del catálogo objetivo inválida."""


def _collection(values, *, ordered=False):
    kind = Sequence if ordered else Collection
    if not isinstance(values, kind) or isinstance(values, (str, bytes, bytearray, Mapping)):
        raise InvalidTargetCatalogError("Se requiere una colección pura explícita.")
    return tuple(values)


def _text(value):
    return type(value) is str and bool(value.strip())


def _integer(value):
    return type(value) is int and value >= 0


@dataclass(frozen=True, slots=True)
class TargetCatalogSnapshot:
    """Catálogo válido e inmutable; su construcción también valida y copia entradas.

    levels y epochs quedan ordenados por número/ordinal, con copias de sus filas.
    La versión identifica lo recibido, sin acreditar publicación o aprobación oficial.
    """

    levels: tuple[LevelDefinition, ...]
    epochs: tuple[StageDefinition, ...]
    ordered_epoch_codes: tuple[str, ...]
    catalog_version: str

    def __post_init__(self):
        if not _text(self.catalog_version):
            raise InvalidTargetCatalogError("Se requiere una versión explícita no vacía.")
        levels = _collection(self.levels)
        epochs = _collection(self.epochs)
        codes = _collection(self.ordered_epoch_codes, ordered=True)
        if len(levels) < 8:
            raise InvalidTargetCatalogError("El catálogo objetivo debe incluir al menos los niveles 1–8.")
        if len(epochs) != 7 or len(codes) != 7:
            raise InvalidTargetCatalogError("Se requieren exactamente siete épocas y códigos.")
        if any(not _text(code) for code in codes) or len(set(codes)) != 7:
            raise InvalidTargetCatalogError("Los códigos explícitos deben ser textos no vacíos y únicos.")
        for row in levels:
            if (type(row) is not LevelDefinition or not _integer(row.level) or row.level == 0
                    or not _integer(row.minimum_xp) or not _integer(row.stat_points_awarded)):
                raise InvalidTargetCatalogError("Definición de nivel inválida: enteros estrictos no negativos.")
        for row in epochs:
            if (type(row) is not StageDefinition or not _integer(row.ordinal)
                    or not 1 <= row.ordinal <= 7 or not _integer(row.minimum_xp) or not _text(row.code)):
                raise InvalidTargetCatalogError("Definición de época inválida: código, ordinal o XP.")
        levels = tuple(sorted(levels, key=lambda row: row.level))
        epochs = tuple(sorted(epochs, key=lambda row: row.ordinal))
        if tuple(row.level for row in levels) != tuple(range(1, len(levels) + 1)):
            raise InvalidTargetCatalogError("Los niveles deben ser consecutivos desde 1, sin duplicados.")
        if tuple(row.ordinal for row in epochs) != tuple(range(1, 8)):
            raise InvalidTargetCatalogError("Los ordinales deben ser consecutivos 1–7, sin duplicados.")
        if tuple(row.code for row in epochs) != codes:
            raise InvalidTargetCatalogError("Las épocas no coinciden con los códigos en el orden explícito.")
        if levels[0].minimum_xp != 0 or epochs[0].minimum_xp != 0:
            raise InvalidTargetCatalogError("El nivel y la época iniciales deben comenzar en XP cero.")
        for rows in (levels, epochs):
            if any(left.minimum_xp >= right.minimum_xp for left, right in zip(rows, rows[1:])):
                raise InvalidTargetCatalogError("Los umbrales deben crecer estrictamente.")
        if any(level.minimum_xp != epoch.minimum_xp for level, epoch in zip(levels[:7], epochs)):
            raise InvalidTargetCatalogError("Los umbrales de cada nivel y época 1–7 deben coincidir.")
        object.__setattr__(self, "levels", tuple(
            LevelDefinition(row.level, row.minimum_xp, row.stat_points_awarded) for row in levels
        ))
        object.__setattr__(self, "epochs", tuple(
            StageDefinition(row.code, row.ordinal, row.minimum_xp) for row in epochs
        ))
        object.__setattr__(self, "ordered_epoch_codes", codes)


def validate_target_level_epoch_catalog(
    levels, epochs, *, ordered_epoch_codes, catalog_version,
) -> TargetCatalogSnapshot:
    """Valida datos objetivo sin progresión, concesiones ni llamadas a validadores V1.

    Nivel 8 y posteriores tienen umbrales propios, sin requerir épocas adicionales.
    No se consumen iteradores arbitrarios ni se modifica ninguna colección recibida.
    """
    return TargetCatalogSnapshot(levels, epochs, ordered_epoch_codes, catalog_version)
