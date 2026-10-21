"""Point-in-time technical observation, never authorization or an XP credential.

Only reads under one outer SQLite IMMEDIATE transaction. The migration's SQL is
imported before auditing; no DML probes, installation, repair or external I/O.
Comparison intentionally rejects even internal formatting differences. This is
not a formal equivalence proof or protection against schema administrators.
"""

from dataclasses import dataclass
from enum import Enum
from importlib import import_module
import re

from django.db import connections, transaction
from django.utils.dateparse import parse_datetime

from .models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from .target_catalog_persistence import validate_target_catalog_version
from .target_catalog_validation import InvalidTargetCatalogError


# Authoritative rules, not copied/reinterpreted here. Immutable local reference.
_REFERENCE = tuple(import_module("apps.ecomotor.migrations.0007_target_catalog_freeze").TRIGGERS)
_MIGRATION = "0007_target_catalog_freeze"


class InvalidTargetCatalogAuditInputError(ValueError):
    """An exact positive technical PK and explicit configured alias are required."""


class TargetCatalogAuditTransactionError(RuntimeError):
    """A controlled outer SQLite IMMEDIATE observation cannot be established."""


class CatalogAuditState(Enum):
    UNOBSERVED = "UNOBSERVED"
    PREPARATORY = "PREPARATORY"
    FROZEN = "FROZEN"


@dataclass(frozen=True, slots=True)
class CatalogAuditCheck:
    name: str
    subject: str
    issue_code: str | None = None

    def __post_init__(self):
        if (type(self.name) is not str or not self.name
                or type(self.subject) is not str or not self.subject
                or self.issue_code is not None and (type(self.issue_code) is not str or not self.issue_code)):
            raise ValueError("Invalid technical check structure.")

    @property
    def passed(self):
        return self.issue_code is None


@dataclass(frozen=True, slots=True)
class TargetCatalogAuditResult:
    using: str
    catalog_version_id: int
    catalog_id: str | None
    version: str | None
    frozen_at: str | None  # Observed SQLite text, not a certificate of server origin.
    state: CatalogAuditState
    checks: tuple[CatalogAuditCheck, ...]

    def __post_init__(self):
        if (type(self.using) is not str or not self.using
                or type(self.catalog_version_id) is not int or not 1 <= self.catalog_version_id <= 2**63 - 1
                or type(self.state) is not CatalogAuditState
                or any(value is not None and type(value) is not str
                       for value in (self.catalog_id, self.version, self.frozen_at))
                or type(self.checks) not in (list, tuple)
                or any(type(check) is not CatalogAuditCheck for check in self.checks)):
            raise ValueError("Invalid technical audit result structure.")
        object.__setattr__(self, "checks", tuple(self.checks))

    @property
    def issues(self):
        return tuple(check for check in self.checks if not check.passed)

    @property
    def technically_conformant(self):
        return bool(self.checks) and not self.issues and self.state is not CatalogAuditState.UNOBSERVED


def _sql_text(sql):
    # SQLite may omit a final statement delimiter. Preserve every internal byte:
    # literals, comments, whitespace, quotes, operators, OLD/NEW and RAISE bodies.
    return sql.strip().removesuffix(";").rstrip() if type(sql) is str else None


def _schema_check(connection, cursor, model):
    table = model._meta.db_table
    cursor.execute("PRAGMA table_info(" + connection.ops.quote_name(table) + ")")
    columns = {row[1]: row for row in cursor.fetchall()}
    problems = []
    if sum(bool(row[5]) for row in columns.values()) != 1:
        problems.append("incompatible:primary_key")
    for field in model._meta.local_fields:
        column = columns.get(field.column)
        if column is None:
            problems.append("missing:" + field.column)
        elif (column[2].strip().upper() != field.db_type(connection).strip().upper()
              or bool(column[5]) != field.primary_key
              or not field.primary_key and bool(column[3]) != (not field.null)):
            problems.append("incompatible:" + field.column)
    if model is not TargetCatalogVersion:
        cursor.execute("PRAGMA foreign_key_list(" + connection.ops.quote_name(table) + ")")
        if not any(row[2] == TargetCatalogVersion._meta.db_table and row[3] == "catalog_id" and row[4] == "id"
                   for row in cursor.fetchall()):
            problems.append("missing:catalog_fk")
    return CatalogAuditCheck("SCHEMA", table + (" " + ",".join(problems) if problems else ""),
                             "SCHEMA_INCOMPLETE" if problems else None)


def _observe(connection, catalog_version_id, using):
    checks = []
    catalog_id = version = frozen_at = None
    state = CatalogAuditState.UNOBSERVED
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        if "django_migrations" not in tables:
            checks.append(CatalogAuditCheck("SCHEMA", "django_migrations missing", "SCHEMA_INCOMPLETE"))
            applied = False
        else:
            cursor.execute('PRAGMA table_info("django_migrations")')
            columns = {row[1] for row in cursor.fetchall()}
            if not {"app", "name"} <= columns:
                checks.append(CatalogAuditCheck("SCHEMA", "django_migrations missing app/name", "SCHEMA_INCOMPLETE"))
                applied = False
            else:
                cursor.execute("SELECT 1 FROM django_migrations WHERE app=%s AND name=%s LIMIT 1", ["ecomotor", _MIGRATION])
                applied = cursor.fetchone() is not None
        checks.append(CatalogAuditCheck("MIGRATION_0007", "ecomotor." + _MIGRATION,
                                       None if applied else "MIGRATION_0007_MISSING"))
        schema_ready = True
        for model in (TargetCatalogVersion, TargetLevelThreshold, TargetEpoch):
            if model._meta.db_table not in tables:
                check = CatalogAuditCheck("SCHEMA", model._meta.db_table + " missing", "SCHEMA_INCOMPLETE")
            else:
                check = _schema_check(connection, cursor, model)
            checks.append(check)
            schema_ready = schema_ready and check.passed
        cursor.execute("SELECT name,tbl_name,sql FROM sqlite_master WHERE type='trigger'")
        observed = {row[0]: row[1:] for row in cursor.fetchall()}
        for reference in _REFERENCE:
            match = re.match(r"CREATE TRIGGER (\w+)\s+BEFORE (?:INSERT|UPDATE|DELETE) ON (\w+)", reference)
            if match is None:
                raise RuntimeError("Unsupported migration trigger reference.")
            name, table = match.groups()
            row = observed.get(name)
            issue = ("TRIGGER_MISSING" if row is None else
                     "TRIGGER_SQL_MISMATCH" if row[0] != table or _sql_text(row[1]) != _sql_text(reference) else None)
            checks.append(CatalogAuditCheck("TRIGGER", name, issue))
        expected_names = {check.subject for check in checks if check.name == "TRIGGER"}
        protected_tables = {model._meta.db_table for model in (TargetCatalogVersion, TargetLevelThreshold, TargetEpoch)}
        for name in sorted(observed.keys() - expected_names):
            if observed[name][0] in protected_tables:
                checks.append(CatalogAuditCheck("TRIGGER", name + " unexpected", "TRIGGER_SQL_MISMATCH"))
        if schema_ready:
            cursor.execute("SELECT catalog_id,version,CAST(frozen_at AS TEXT) FROM ecomotor_targetcatalogversion WHERE id=%s", [catalog_version_id])
            row = cursor.fetchone()
            if row is None:
                checks.append(CatalogAuditCheck("CATALOG", str(catalog_version_id), "CATALOG_NOT_FOUND"))
            else:
                catalog_id, version, frozen_at = row
                state = CatalogAuditState.PREPARATORY if frozen_at is None else CatalogAuditState.FROZEN
                representable = type(catalog_id) is str and type(version) is str
                if frozen_at is not None:
                    try:
                        representable = representable and parse_datetime(frozen_at) is not None
                    except ValueError:  # Invalid observed date, not a database/reader failure.
                        representable = False
                if not representable:
                    catalog_id = catalog_id if type(catalog_id) is str else None
                    version = version if type(version) is str else None
                    checks.append(CatalogAuditCheck("CATALOG", "identity/frozen_at", "CATALOG_INVALID"))
                else:
                    try:
                        validate_target_catalog_version(catalog_version_id, using=using)
                    except InvalidTargetCatalogError:
                        checks.append(CatalogAuditCheck("CATALOG_A1_1", str(catalog_version_id), "CATALOG_INVALID"))
                    else:
                        checks.append(CatalogAuditCheck("CATALOG_A1_1", str(catalog_version_id)))
    return TargetCatalogAuditResult(using, catalog_version_id, catalog_id, version, frozen_at, state, tuple(checks))


def audit_target_catalog(catalog_version_id: int, *, using: str) -> TargetCatalogAuditResult:
    """Complete a coherent technical observation or propagate operational failure.

    Missing migration/schema/trigger/catalog and A1.1 violations are diagnostics.
    Connection, lock, timeout and unexpected SQL errors remain real failures.
    No migration executor/recorder that could create django_migrations is used.
    """
    if (type(catalog_version_id) is not int or not 1 <= catalog_version_id <= 2**63 - 1
            or type(using) is not str or not using or using not in connections):
        raise InvalidTargetCatalogAuditInputError("An exact positive PK and configured explicit alias are required.")
    connection = connections[using]
    options = connection.settings_dict["OPTIONS"]
    if (connection.vendor != "sqlite" or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5 or options.get("autocommit", -1) != -1
            or connection.in_atomic_block):
        raise TargetCatalogAuditTransactionError("A controlled outer SQLite IMMEDIATE transaction is required.")
    connection.ensure_connection()
    if (not connection.get_autocommit() or connection.connection.in_transaction
            or connection.transaction_mode != "IMMEDIATE"
            or getattr(connection.connection, "autocommit", -1) != -1):
        raise TargetCatalogAuditTransactionError("An existing or incompatible transaction is not supported.")
    with transaction.atomic(using=using):
        return _observe(connection, catalog_version_id, using)
