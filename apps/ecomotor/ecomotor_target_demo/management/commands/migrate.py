"""The only local command permitted to create the persistent demo SQLite."""

from django.core.management.commands.migrate import Command as DjangoMigrate
from django.core.management.base import CommandError
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

from ...isolation import MIGRATING, checked_path, selected_alias


class Command(DjangoMigrate):
    def execute(self, *args, **options):
        # The isolated Django test runner uses standard SQLite in-memory for the
        # existing regression suite. This exception cannot select a disk file.
        from ...test_runner import running
        db = connections[options["database"]]
        if running and db.settings_dict["ENGINE"] == "django.db.backends.sqlite3" and (
                db.settings_dict["NAME"] == ":memory:"
                or str(db.settings_dict["NAME"]).startswith("file:memorydb_")):
            return super().execute(*args, **options)
        try:
            if options["database"] != selected_alias():
                raise ImproperlyConfigured("Alias de migración incompatible.")
            checked_path(db, creating=True)
        except ImproperlyConfigured as error:
            raise CommandError(str(error)) from error
        token = MIGRATING.set(True)
        try:
            # Include Django's pre-migration JSON/database checks in this
            # explicit creation scope: they may connect before handle().
            return super().execute(*args, **options)
        finally:
            MIGRATING.reset(token)
