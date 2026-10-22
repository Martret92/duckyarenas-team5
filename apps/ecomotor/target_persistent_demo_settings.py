"""Opt-in local synthetic persistent demo. Bind runserver to 127.0.0.1."""

from config.settings import *  # noqa: F403

INSTALLED_APPS = ["apps.ecomotor_target_demo.apps.EcomotorTargetDemoConfig", *INSTALLED_APPS]  # noqa: F405
ROOT_URLCONF = "apps.ecomotor_target_demo.urls"
TARGET_PERSISTENT_DEMO = "A3-TARGET-PERSIST-DEMO-01"
TARGET_PERSISTENT_DEMO_ALIAS = "default"
DATABASES = {"default": {
    "ENGINE": "apps.ecomotor_target_demo.db_backend",
    "NAME": BASE_DIR / "instance" / "target_persistent_demo.sqlite3",  # noqa: F405
    "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 5},
}}
DATABASE_ROUTERS = ["apps.ecomotor_target_demo.isolation.SessionRouter"]
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "target_persistent_demo_session"
CSRF_COOKIE_NAME = "target_persistent_demo_csrf"
SESSION_COOKIE_PATH = "/demo/objetivo-persistente/"
CSRF_COOKIE_PATH = "/demo/objetivo-persistente/"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
TEST_RUNNER = "apps.ecomotor_target_demo.test_runner.DemoRunner"
