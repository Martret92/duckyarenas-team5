"""Filesystem/connection boundary, including explicit initial migration creation.

Not a defence against administrators replacing files/triggers during execution.
No symlink, junction or multiply linked database is an accepted demo destination.
"""

from contextvars import ContextVar
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

from config import settings as normal_settings

MIGRATING = ContextVar("persistent_demo_migrating", default=False)


def selected_alias():
    if getattr(settings, "TARGET_PERSISTENT_DEMO", None) != "A3-TARGET-PERSIST-DEMO-01":
        raise ImproperlyConfigured("Se requieren los settings exclusivos de la demo persistente.")
    alias = getattr(settings, "TARGET_PERSISTENT_DEMO_ALIAS", "default")
    if type(alias) is not str or alias not in connections:
        raise ImproperlyConfigured("Alias de demo inválido.")
    return alias


def checked_path(connection, *, creating=False):
    alias = selected_alias()
    config = connection.settings_dict
    options = config.get("OPTIONS", {})
    expected = Path(settings.BASE_DIR).absolute() / "instance" / "target_persistent_demo.sqlite3"
    if (connection.alias != alias or not config["ENGINE"].endswith("ecomotor_target_demo.db_backend")
            or str(config["NAME"]).startswith("file:") or Path(config["NAME"]).absolute() != expected
            or set(options) != {"transaction_mode", "timeout"}
            or options["transaction_mode"] != "IMMEDIATE" or options["timeout"] != 5):
        raise ImproperlyConfigured("La conexión no es la SQLite persistente de demo aislada.")
    try:
        if any(p.is_symlink() or getattr(p, "is_junction", lambda: False)()
               for p in (expected, *expected.parents)):
            raise ImproperlyConfigured("No se permiten symlinks ni junctions en la ruta de demo.")
        if not expected.parent.is_dir():
            raise ImproperlyConfigured("Crea explícitamente instance/ antes de migrate.")
        if expected.exists():
            if not expected.is_file() or expected.stat().st_nlink != 1:
                raise ImproperlyConfigured("La SQLite de demo no admite enlaces duros ni rutas incompatibles.")
            for other in (Path(normal_settings.DATABASES["default"]["NAME"]),
                          Path(settings.BASE_DIR) / "db.sqlite3",
                          Path(settings.BASE_DIR) / "instance" / "target_demo.sqlite3"):
                if other.exists() and expected.samefile(other):
                    raise ImproperlyConfigured("La demo no puede compartir otra base física.")
        elif not creating:
            raise ImproperlyConfigured("La SQLite de demo no existe; ejecuta migrate explícitamente.")
    except OSError as error:
        raise ImproperlyConfigured("No se pudo verificar el aislamiento físico de la demo.") from error
    return expected


def demo_connection():
    db = connections[selected_alias()]
    checked_path(db)
    db.ensure_connection()  # Custom backend checks both opening and live connection.
    return db


class SessionRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == "sessions":
            return selected_alias()

    db_for_write = db_for_read
