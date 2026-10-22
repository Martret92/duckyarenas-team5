"""SQLite 5.2 lifecycle with guarded, noncreating ordinary opens."""

from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteWrapper
from django.core.exceptions import ImproperlyConfigured

from ..isolation import MIGRATING, checked_path


class DatabaseWrapper(SQLiteWrapper):
    def get_connection_params(self):
        path = checked_path(self, creating=MIGRATING.get())
        params = super().get_connection_params()
        params["database"] = path.as_uri() + ("?mode=rwc" if MIGRATING.get() else "?mode=rw")
        return params

    def get_new_connection(self, params):
        path = checked_path(self, creating=MIGRATING.get())
        before = path.stat() if path.exists() else None
        connection = super().get_new_connection(params)
        try:
            checked_path(self)
            observed = path.stat()
            identity = (observed.st_dev, observed.st_ino)
            if before is not None and identity != (before.st_dev, before.st_ino):
                raise ImproperlyConfigured("La SQLite fue sustituida durante su apertura.")
            self._demo_file_identity = identity
        except BaseException:
            connection.close()
            raise
        return connection

    def ensure_connection(self):
        expected = checked_path(self, creating=MIGRATING.get())
        if self.connection is not None:
            observed = expected.stat()
            if (observed.st_dev, observed.st_ino) != getattr(self, "_demo_file_identity", None):
                raise ImproperlyConfigured("El archivo SQLite ha cambiado desde su apertura.")
        super().ensure_connection()
        # Native query avoids recursive cursor()/ensure_connection(). No DML.
        rows = self.connection.execute("PRAGMA database_list").fetchall()
        actual = next(row[2] for row in rows if row[1] == "main")
        checked_path(self)
        try:
            if not actual or not expected.samefile(actual):
                raise ImproperlyConfigured("La conexión efectiva no es la SQLite aislada esperada.")
        except OSError as error:
            raise ImproperlyConfigured("La SQLite abierta ha desaparecido o fue sustituida.") from error
