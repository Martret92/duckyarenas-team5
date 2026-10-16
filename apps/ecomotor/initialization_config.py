"""Configuración interna; los fixtures nunca se convierten en valores oficiales."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InitializationConfiguration:
    atk: int
    def_stat: int
    log_stat: int
    spe: int
    vel: int
    int_stat: int
    ordered_stage_codes: tuple[str, ...]

    def __post_init__(self):
        # Copia defensiva: una lista del proveedor no queda enlazada al snapshot.
        object.__setattr__(self, "ordered_stage_codes", tuple(self.ordered_stage_codes))


# Requiere valores y correspondencia autorizados antes de habilitar altas reales.
INITIAL_CONFIGURATION: InitializationConfiguration | None = None
