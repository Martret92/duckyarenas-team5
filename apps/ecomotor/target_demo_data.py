"""Local synthetic fixtures and environment boundary; no official configuration."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

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
    expected = (Path(settings.BASE_DIR) / "instance" / "target_demo.sqlite3").resolve()
    config = db.settings_dict
    options = config.get("OPTIONS", {})
    if (db.vendor != "sqlite" or str(config["NAME"]).startswith("file:")
            or Path(config["NAME"]).resolve() != expected
            or "database" in options or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5):
        raise ImproperlyConfigured("La demo solo permite su SQLite aislada en instance/target_demo.sqlite3.")
    if not expected.is_file():
        raise ImproperlyConfigured("Primero crea instance/ y ejecuta migrate con target_demo_settings.")
    return alias
