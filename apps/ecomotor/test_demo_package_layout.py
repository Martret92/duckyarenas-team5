"""Structural regression: nesting the lab must not install its models normally."""

from runpy import run_path
from types import SimpleNamespace
from importlib.util import find_spec
from pathlib import Path

from django.apps import apps
from django.core.management import get_commands
from django.test import SimpleTestCase, override_settings
from config import settings as normal_settings


class DemoPackageLayoutTests(SimpleTestCase):
    @override_settings(INSTALLED_APPS=normal_settings.INSTALLED_APPS)
    def test_normal_registry_and_commands_exclude_the_lab(self):
        self.assertNotIn("ecomotor_target_demo", apps.app_configs)
        self.assertFalse(any(m._meta.app_label == "ecomotor_target_demo" for m in apps.get_models()))
        self.assertEqual(apps.get_app_config("ecomotor").name, "apps.ecomotor")
        self.assertNotIn("seed_persistent_target_demo", get_commands())
        self.assertEqual(get_commands()["migrate"], "django.core")

    def test_only_the_new_physical_package_exists(self):
        self.assertIsNone(find_spec("apps.ecomotor_target_demo"))
        self.assertIsNotNone(find_spec("apps.ecomotor.ecomotor_target_demo"))
        self.assertFalse((Path(__file__).resolve().parents[2] / "apps" / "ecomotor_target_demo").exists())

    def test_opt_in_settings_use_new_routes_without_mutating_normal_settings(self):
        previous = tuple(normal_settings.INSTALLED_APPS)
        # The two-phase runner temporarily replaces connection configuration.
        # Evaluate the declared settings afresh, independently of that test harness.
        demo = SimpleNamespace(**run_path(str(Path(__file__).with_name("target_persistent_demo_settings.py"))))
        prefix = "apps.ecomotor.ecomotor_target_demo"
        self.assertEqual(demo.INSTALLED_APPS, [prefix + ".apps.EcomotorTargetDemoConfig", *previous])
        self.assertEqual(demo.ROOT_URLCONF, prefix + ".urls")
        self.assertEqual(demo.DATABASES["default"]["ENGINE"], prefix + ".db_backend")
        self.assertEqual(demo.DATABASE_ROUTERS, [prefix + ".isolation.SessionRouter"])
        self.assertEqual(demo.TEST_RUNNER, prefix + ".test_runner.DemoRunner")
        self.assertEqual(tuple(normal_settings.INSTALLED_APPS), previous)
        self.assertEqual(demo.TARGET_PERSISTENT_DEMO, "A3-TARGET-PERSIST-DEMO-01")
        self.assertEqual(demo.SESSION_COOKIE_NAME, "target_persistent_demo_session")
        self.assertEqual(demo.SESSION_COOKIE_PATH, "/demo/objetivo-persistente/")
