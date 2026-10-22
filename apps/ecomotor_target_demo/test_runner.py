"""Test harness only: existing regressions retain isolated standard SQLite.

New demo tests explicitly instantiate the guarded backend against disposable
files. No production flag, settings option or HTTP argument bypasses it.
"""

from django.db import connections
from django.test.runner import DiscoverRunner
from django.test import override_settings
from config import settings as normal_settings

running = False


class DemoRunner(DiscoverRunner):
    def run_tests(self, test_labels, **kwargs):
        global running
        original = connections.databases["default"]
        connections["default"].close()
        del connections["default"]
        connections.databases["default"] = {
            **original, "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",
            "TEST": {**original.get("TEST", {}), "NAME": None},
        }
        running = True
        try:
            # Historical migration fixtures deliberately stop at 0005/0007.
            # With the new app in their registry, Django's PROTECT collector
            # would query demo tables those historical fixtures never create.
            # Run unmodified legacy tests with their normal app registry, then
            # the explicit new suite with the actual persistent app installed.
            labels = list(test_labels or ["apps.ecomotor", "apps.users", "apps.duckies",
                                          "apps.ecomotor_target_demo.demo_tests"])
            new = [label for label in labels if label.startswith("apps.ecomotor_target_demo.demo_tests")]
            legacy = [label for label in labels if label not in new]
            failures = 0
            if legacy:
                with override_settings(INSTALLED_APPS=normal_settings.INSTALLED_APPS,
                        SESSION_COOKIE_NAME="sessionid", CSRF_COOKIE_NAME="csrftoken",
                        SESSION_COOKIE_PATH="/", CSRF_COOKIE_PATH="/", ROOT_URLCONF="config.urls"):
                    failures += super().run_tests(legacy, **kwargs)
            if new:
                failures += super().run_tests(new, **kwargs)
            return failures
        finally:
            connections["default"].close()
            del connections["default"]
            connections.databases["default"] = original
            running = False
