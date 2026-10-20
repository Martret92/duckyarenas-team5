"""A3.2: materialize one profile's V1 evidence, never audit or migrate it.

The trusted caller owns inspection authorization and alias selection. All reads
use one SQLite IMMEDIATE transaction (timeout 5), which can temporarily block
writers. An existing transaction, including manual autocommit-off, is rejected.
No snapshot remains current indefinitely; full coverage is not coherence,
migration permission or an integral Duckies/specialization/points-history audit.

Operation keys are copied exactly, without logging or exporting evidence. A3.1
dataclasses can include keys in repr: callers must not log arbitrary snapshots.
Public translated errors suppress sensitive internal exception chains. This is
not protection against arbitrary consumer logging or debugger inspection.
"""

from django.db import DatabaseError, connections, transaction

from apps.users.models import UserProfileEcomotor

from .legacy_transition_audit import (
    InvalidLegacySnapshotError, LegacyAuditCoverage, LegacyAuditSnapshot,
    LegacyCharacterStatsSnapshot, LegacyEvolutionEventSnapshot,
    LegacyProfileSnapshot, LegacyStageSnapshot, LegacyXPEventSnapshot,
)
from .models import CharacterStats, EvolutionEvent, EvolutionStage, XPEvent


class InvalidLegacyProfileIdError(ValueError):
    """Profile ID is not an exact positive, representable local integer PK."""


class InvalidLegacyDatabaseAliasError(ValueError):
    """An explicit configured Django alias is required, not authorization."""


class LegacyProfileNotFoundError(ValueError):
    """The profile was not observed in the selected database."""


class LegacyInventoryTransactionError(RuntimeError):
    """The connection cannot provide the controlled SQLite snapshot boundary."""


class LegacyForeignCausalityError(RuntimeError):
    """Cross-profile causality was observed; foreign evidence is not returned."""


class LegacyInventoryReadError(RuntimeError):
    """Database access failed; no partial snapshot is returned."""


class LegacyInventoryEvidenceError(RuntimeError):
    """Observed evidence cannot be represented by the strict A3.1 snapshots."""


def _check_transaction_boundary(connection):
    options = connection.settings_dict["OPTIONS"]
    if (connection.vendor != "sqlite" or options.get("transaction_mode") != "IMMEDIATE"
            or options.get("timeout") != 5 or options.get("autocommit", -1) != -1):
        raise LegacyInventoryTransactionError("Unsupported inventory connection configuration.")
    if connection.in_atomic_block:
        raise LegacyInventoryTransactionError("An outer transaction is not supported.")
    connection.ensure_connection()
    if (not connection.get_autocommit() or connection.connection.in_transaction
            or connection.transaction_mode != "IMMEDIATE"
            # Python 3.12 sqlite autocommit=True makes native commit() a no-op.
            # -1 is LEGACY_TRANSACTION_CONTROL; older Python has no such flag.
            or getattr(connection.connection, "autocommit", -1) != -1):
        raise LegacyInventoryTransactionError("A controlled IMMEDIATE transaction is required.")


def _rows(query, snapshot_type, names):
    # No model instances, deferred fields, slicing or iterator escaping atomic().
    return tuple(snapshot_type(**row) for row in query.order_by("pk").values(*names))


def _extract(profile_id, using):
    own_xp = XPEvent.objects.using(using).filter(profile_id=profile_id)
    own_evolutions = EvolutionEvent.objects.using(using).filter(profile_id=profile_id)
    row = UserProfileEcomotor.objects.using(using).filter(pk=profile_id).values(
        "id", "historical_xp_total", "current_level", "current_stage_code",
        "active_specialization_code",
    ).first()
    if row is None:
        raise LegacyProfileNotFoundError("Profile not found in the selected database.")
    profile = LegacyProfileSnapshot(profile_id=row.pop("id"), **row)
    row = CharacterStats.objects.using(using).filter(profile_id=profile_id).values(
        "profile_id", "atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points",
    ).first()
    stats = None if row is None else LegacyCharacterStatsSnapshot(**row)
    xp_events = _rows(own_xp, LegacyXPEventSnapshot, (
        "id", "profile_id", "operation_key", "amount", "xp_before", "xp_after",
    ))
    # Do not join causes or stages here: orphan references must survive extraction.
    evolutions = _rows(own_evolutions, LegacyEvolutionEventSnapshot, (
        "id", "profile_id", "xp_event_id", "stage_id",
    ))
    stages = _rows(EvolutionStage.objects.using(using).all(), LegacyStageSnapshot, (
        "id", "code", "ordinal", "minimum_xp",
    ))

    # Existence-only checks: no foreign keys/payloads are copied into the result
    # or errors. Subqueries avoid an unbounded IN list of all observed event IDs.
    foreign_cause = XPEvent.objects.using(using).filter(
        pk__in=own_evolutions.values("xp_event_id"),
    ).exclude(profile_id=profile_id).exists()
    foreign_evolution = EvolutionEvent.objects.using(using).filter(
        xp_event_id__in=own_xp.values("pk"),
    ).exclude(profile_id=profile_id).exists()
    if foreign_cause or foreign_evolution:
        raise LegacyForeignCausalityError("Cross-profile evolution causality detected.")

    return LegacyAuditSnapshot(
        profile=profile, character_stats=stats, xp_events=xp_events,
        evolution_events=evolutions, stages=stages,
        coverage=LegacyAuditCoverage(True, True, True, True),
    )


def extract_legacy_audit_snapshot(profile_id: int, *, using: str) -> LegacyAuditSnapshot:
    """Extract complete evidence or fail; no auditing, writes or normalization.

    Missing CharacterStats is observed as None. A genuinely missing XP cause is
    preserved for an independent A3.1 audit. No historical stage attributes are
    reconstructed. PK ordering is reproducibility, not functional chronology.
    """
    if type(profile_id) is not int or not 1 <= profile_id <= 2**63 - 1:
        raise InvalidLegacyProfileIdError("A positive local profile ID is required.")
    if type(using) is not str or not using or using not in connections:
        raise InvalidLegacyDatabaseAliasError("An explicit configured database alias is required.")
    connection = connections[using]
    try:
        _check_transaction_boundary(connection)
        with transaction.atomic(using=using):
            snapshot = _extract(profile_id, using)
        return snapshot
    except DatabaseError:
        # Do not preserve a visible chain containing SQL, keys or foreign IDs.
        raise LegacyInventoryReadError("Legacy inventory could not be read.") from None
    except InvalidLegacySnapshotError:
        raise LegacyInventoryEvidenceError("Legacy evidence is not representable.") from None
