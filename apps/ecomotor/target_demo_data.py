"""Local synthetic fixtures and environment boundary; no official configuration."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

from config import settings as normal_settings

from .target_catalog_audit import _ensure_noncreating_connection

CATALOG_ID = "synthetic-target-web-demo"
CATALOG_VERSION = "demo-2026-10-22-v1"
DEMO_BUDGET = 45
EPOCH_NAMES = ("Prehistórico", "Griego", "Romano", "Medieval", "Renacentista",
               "Revolución Industrial", "Siglo XX")
EPOCH_CODES = tuple(f"demo-epoch-{n}" for n in range(1, 8))
THRESHOLDS = (0, 100, 200, 300, 400, 500, 600, 700, 900)
HISTORICAL_OPTIONS = tuple(zip(EPOCH_CODES, EPOCH_NAMES))
TECH_OPTIONS = (("demo-developer", "Developer"), ("demo-ciber", "Ciber"),
                ("demo-sistemas", "Sistemas"), ("demo-data-ia", "Data IA"), ("demo-gamer", "Gamer"))
OPTIONS = HISTORICAL_OPTIONS + TECH_OPTIONS
STAT_LABELS = ("Ataque", "Defensa", "Velocidad", "Inteligencia", "Lógica", "Cuak")


def _isolated_file(path, expected):
    # Inspect lexical components BEFORE resolve: resolving the expected path too
    # would hide a symlink/junction at the file or any containing directory.
    if path != expected or any(
            part.is_symlink() or getattr(part, "is_junction", lambda: False)()
            for part in (path, *path.parents)):
        raise ImproperlyConfigured("La SQLite de demo no admite enlaces simbólicos o junctions.")
    if not path.is_file():
        raise ImproperlyConfigured("Primero crea instance/ y ejecuta migrate con target_demo_settings.")
    # samefile uses physical file identity, including hard links on Windows and
    # POSIX; no assumption about inode numbers or special Windows permissions.
    habitual = (Path(settings.BASE_DIR) / "db.sqlite3",
                Path(normal_settings.DATABASES["default"]["NAME"]))
    for other in habitual:
        if other.exists() and path.samefile(other):
            raise ImproperlyConfigured("La demo no puede compartir el archivo físico de la base habitual.")


def demo_database():
    """Require explicit opt-in and the exact isolated file, including live wrapper.

    A trusted test harness may configure an isolated alias and BASE_DIR. There is
    no HTTP/CLI alias override. Memory/URI and OPTIONS database overrides are not
    accepted here: this demo always uses its dedicated, reproducible disk file.
    """
    if getattr(settings, "TARGET_DEMO_ENVIRONMENT", None) != "A3-TARGET-DEMO-01":
        raise ImproperlyConfigured("La demo requiere sus settings exclusivos.")
    alias = getattr(settings, "TARGET_DEMO_DATABASE_ALIAS", "default")
    if type(alias) is not str or alias not in connections:
        raise ImproperlyConfigured("Alias de demo incompatible.")
    db = connections[alias]
    expected = Path(settings.BASE_DIR).absolute() / "instance" / "target_demo.sqlite3"
    config = db.settings_dict
    options = config.get("OPTIONS", {})
    if (db.vendor != "sqlite" or str(config["NAME"]).startswith("file:")
            or Path(config["NAME"]).absolute() != expected
            or "database" in options or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5):
        raise ImproperlyConfigured("La demo solo permite su SQLite aislada en instance/target_demo.sqlite3.")
    try:
        _isolated_file(Path(config["NAME"]).absolute(), expected)
        # Reuse AUDIT-01's connection-opening utility, not its audit service.
        # Native mode=rw prevents creation even if the checked file disappears.
        # Django's lifecycle and the original NAME/OPTIONS remain unchanged.
        _ensure_noncreating_connection(db)
        with db.cursor() as cursor:
            cursor.execute("PRAGMA database_list")
            actual = next(row[2] for row in cursor.fetchall() if row[1] == "main")
        _isolated_file(expected, expected)
        if not actual or not Path(actual).samefile(expected):
            raise ImproperlyConfigured("La conexión abierta no corresponde al archivo aislado de demo.")
    except OSError as error:
        raise ImproperlyConfigured("No se pudo verificar la separación física de la SQLite de demo.") from error
    return alias
