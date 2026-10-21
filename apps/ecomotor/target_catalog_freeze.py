"""Freeze a structurally valid catalog, without publication or functional authority.

Only a controlled outer SQLite IMMEDIATE transaction is accepted. An existing
atomic/manual transaction is rejected: a savepoint cannot establish a new BEGIN
IMMEDIATE. Physical DML protection is installed by migration 0007, not this service.
Schema administrators can remove it; a direct NULL->date update can bypass A1.1.
"""

from dataclasses import dataclass
from datetime import datetime

from django.db import connections, transaction
from django.utils import timezone

from .models import TargetCatalogVersion
from .target_catalog_persistence import validate_target_catalog_version
from .target_catalog_validation import InvalidTargetCatalogError


class TargetCatalogFreezeTransactionError(RuntimeError):
    """Connection cannot provide the controlled IMMEDIATE transaction boundary."""


@dataclass(frozen=True, slots=True)
class TargetCatalogFreezeResult:
    catalog_version_id: int
    frozen_at: datetime


def freeze_target_catalog_version(catalog_version_id: int, *, using: str) -> TargetCatalogFreezeResult:
    """Validate and mark, or revalidate/recover the unchanged existing date.

    InvalidTargetCatalogError, DoesNotExist and DatabaseError remain distinct.
    A returned date is neither publication nor permission to use the catalog.
    No retries or manual BEGIN; failures propagate and atomic rolls back.
    """
    if (type(catalog_version_id) is not int or not 1 <= catalog_version_id <= 2**63 - 1
            or type(using) is not str or not using or using not in connections):
        raise InvalidTargetCatalogError("An exact positive version PK and configured alias are required.")
    connection = connections[using]
    options = connection.settings_dict["OPTIONS"]
    if (connection.vendor != "sqlite" or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5 or options.get("autocommit", -1) != -1
            or connection.in_atomic_block):
        raise TargetCatalogFreezeTransactionError("A controlled outer SQLite IMMEDIATE transaction is required.")
    connection.ensure_connection()
    if (not connection.get_autocommit() or connection.connection.in_transaction
            or connection.transaction_mode != "IMMEDIATE"
            or getattr(connection.connection, "autocommit", -1) != -1):
        raise TargetCatalogFreezeTransactionError("An existing or incompatible transaction is not supported.")
    with transaction.atomic(using=using):
        version = TargetCatalogVersion.objects.using(using).get(pk=catalog_version_id)
        validate_target_catalog_version(catalog_version_id, using=using)
        if version.frozen_at is None:
            version.frozen_at = timezone.now()
            version.save(using=using, update_fields=["frozen_at"])
        return TargetCatalogFreezeResult(version.pk, version.frozen_at)
