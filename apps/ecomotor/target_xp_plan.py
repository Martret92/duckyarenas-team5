"""A2.1: propuesta pura de progresión, nunca concesión ni autorización de escritor.

No consulta estado persistido o configuración. El futuro servicio debe verificar
de nuevo autorización, catálogo confiable y estado persistido; construir un plan
directamente tampoco otorga permiso para persistirlo. A3/Core siguen pendientes.
"""

from dataclasses import dataclass

from . import target_progression
from .target_catalog_validation import InvalidTargetCatalogError, TargetCatalogSnapshot
from .target_progression import InvalidTargetXPError, TargetProgressionResult


class InvalidTargetXPAmountError(ValueError):
    """El importe debe ser un entero exacto estrictamente positivo, sin bool."""


def _validate_amount(amount):
    if type(amount) is not int or amount <= 0:
        raise InvalidTargetXPAmountError("Se requiere un importe XP entero estrictamente positivo.")


@dataclass(frozen=True, slots=True)
class TargetXPPlan:
    amount: int
    progression: TargetProgressionResult

    def __post_init__(self):
        _validate_amount(self.amount)
        if type(self.progression) is not TargetProgressionResult:
            raise TypeError("Se requiere un resultado inmutable de A1.2.")


def plan_target_xp_grant(
    xp_before: int, amount: int, catalog: TargetCatalogSnapshot,
) -> TargetXPPlan:
    """Suma el importe positivo y delega íntegramente el cálculo a A1.2.

    No revalida el snapshot A1.1 ni impone límites de campos persistentes. La versión
    del catálogo se conserva como dato, sin activar un escritor o confirmar efectos.
    """
    if type(xp_before) is not int or xp_before < 0:
        raise InvalidTargetXPError("Se requiere XP anterior entera no negativa.")
    _validate_amount(amount)
    if type(catalog) is not TargetCatalogSnapshot:
        raise InvalidTargetCatalogError("Se requiere un snapshot objetivo validado por A1.1.")
    xp_after = xp_before + amount
    progression = target_progression.calculate_target_progression(xp_before, xp_after, catalog)
    return TargetXPPlan(amount, progression)
