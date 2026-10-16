"""Configuración interna; los fixtures nunca se convierten en valores oficiales."""

from dataclasses import dataclass
import json
from pathlib import Path


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


class ConfigurationFileError(ValueError):
    """No se pudo leer una fuente local, sin revelar ruta ni contenido."""


class ConfigurationFileMissingError(ConfigurationFileError):
    """La fuente explícita no existe."""


class ConfigurationSyntaxError(ValueError):
    """JSON/UTF-8 inválido."""


class ConfigurationStructureError(ValueError):
    """Estructura, tipos o rangos técnicos inválidos."""


_ATTRIBUTES = ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat")


def _validate_configuration(config, using):
    # Imports locales: conservar el módulo de datos sin consultas/activación al importar.
    from django.db import connections
    from .models import CharacterStats

    if not isinstance(config, InitializationConfiguration):
        raise ConfigurationStructureError("Se requiere InitializationConfiguration.")
    for name in _ATTRIBUTES:
        value = getattr(config, name)
        field = CharacterStats._meta.get_field(name)
        lower, upper = connections[using].ops.integer_field_range(field.get_internal_type())
        if (not isinstance(value, int) or isinstance(value, bool)
                or (lower is not None and value < lower)
                or (upper is not None and value > upper)):
            raise ConfigurationStructureError("Estadísticas fuera del contrato técnico.")
    codes = config.ordered_stage_codes
    if (not isinstance(codes, tuple) or len(codes) != 7
            or any(not isinstance(code, str) or not 1 <= len(code) <= 32 for code in codes)
            or len(set(codes)) != 7):
        raise ConfigurationStructureError("Correspondencia de etapas inválida.")


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationStructureError("Campos JSON duplicados.")
        result[key] = value
    return result


def load_initialization_configuration(path, *, using="default"):
    """Carga un candidato local; nunca instala ni modifica la referencia global."""
    try:
        source = Path(path)
        if str(source).startswith(("\\\\", "//")) or "://" in str(path):
            raise ConfigurationFileError("Solo se admiten rutas locales.")
        content = source.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ConfigurationFileMissingError("No existe la fuente local.") from error
    except UnicodeError as error:
        raise ConfigurationSyntaxError("La fuente no es JSON UTF-8 válido.") from error
    except (OSError, TypeError, ValueError) as error:
        raise ConfigurationFileError("No se pudo leer la fuente local.") from error
    try:
        data = json.loads(content, object_pairs_hook=_json_object)
    except ConfigurationStructureError:
        raise
    except (ValueError, RecursionError) as error:
        raise ConfigurationSyntaxError("Sintaxis JSON inválida.") from error
    if not isinstance(data, dict) or set(data) != {*_ATTRIBUTES, "ordered_stage_codes"}:
        raise ConfigurationStructureError("El objeto debe contener exactamente los siete parámetros.")
    if not isinstance(data["ordered_stage_codes"], list):
        raise ConfigurationStructureError("ordered_stage_codes debe ser una lista JSON.")
    config = InitializationConfiguration(**data)
    _validate_configuration(config, using)
    return config
