"""Coherent read plus pure A2.1 plan; never grant, freeze, authorize or activate.

The result preserves the selected technical PK, not a causal record of real use.
Preparatory and frozen catalogs are both accepted. IMMEDIATE serializes writers
only during this short observation; the returned plan is not perpetual freshness.
"""

from dataclasses import dataclass

from django.db import connections, transaction

from .target_catalog_persistence import validate_target_catalog_version
from .target_catalog_validation import InvalidTargetCatalogError
from .target_progression import InvalidTargetXPError
from .target_xp_plan import InvalidTargetXPAmountError, TargetXPPlan, plan_target_xp_grant


class TargetXPPreviewTransactionError(RuntimeError):
    """A controlled outer SQLite IMMEDIATE transaction cannot be guaranteed."""


@dataclass(frozen=True, slots=True)
class TargetXPPreview:
    catalog_version_id: int
    plan: TargetXPPlan

    def __post_init__(self):
        if type(self.catalog_version_id) is not int or not 1 <= self.catalog_version_id <= 2**63 - 1:
            raise InvalidTargetCatalogError("An exact positive version PK is required.")
        if type(self.plan) is not TargetXPPlan:
            raise TypeError("A pure TargetXPPlan is required.")


def preview_target_xp(catalog_version_id: int, *, using: str, xp_before: int, amount: int) -> TargetXPPreview:
    """Validate input, read A1.1 coherently and delegate all progression to A2.1.

    Existing atomic/manual transactions are rejected, never treated as a fresh
    BEGIN IMMEDIATE. All queries use the explicit alias. Catalog/XP/amount,
    missing-version and database errors propagate unchanged; no automatic retry.
    """
    if (type(catalog_version_id) is not int or not 1 <= catalog_version_id <= 2**63 - 1
            or type(using) is not str or not using or using not in connections):
        raise InvalidTargetCatalogError("An exact positive version PK and configured alias are required.")
    if type(xp_before) is not int or xp_before < 0:
        raise InvalidTargetXPError("Previous XP must be an exact nonnegative integer.")
    if type(amount) is not int or amount <= 0:
        raise InvalidTargetXPAmountError("XP amount must be an exact positive integer.")
    connection = connections[using]
    options = connection.settings_dict["OPTIONS"]
    if (connection.vendor != "sqlite" or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5 or options.get("autocommit", -1) != -1
            or connection.in_atomic_block):
        raise TargetXPPreviewTransactionError("A controlled outer SQLite IMMEDIATE transaction is required.")
    connection.ensure_connection()
    if (not connection.get_autocommit() or connection.connection.in_transaction
            or connection.transaction_mode != "IMMEDIATE"
            or getattr(connection.connection, "autocommit", -1) != -1):
        raise TargetXPPreviewTransactionError("An existing or incompatible transaction is not supported.")
    with transaction.atomic(using=using):
        snapshot = validate_target_catalog_version(catalog_version_id, using=using)
        plan = plan_target_xp_grant(xp_before, amount, snapshot)
        return TargetXPPreview(catalog_version_id, plan)
