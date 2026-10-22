"""Explicit local-only target demo; never fall back to the regular database."""

from config.settings import *  # noqa: F403

ROOT_URLCONF = "apps.ecomotor.target_demo_urls"
TARGET_DEMO_ENVIRONMENT = "A3-TARGET-DEMO-01"
TARGET_DEMO_DATABASE_ALIAS = "default"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "instance" / "target_demo.sqlite3",  # noqa: F405
        "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5},
    }
}
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
