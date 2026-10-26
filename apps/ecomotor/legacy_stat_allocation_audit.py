"""INT-A2-T04: internal, read-only diagnosis of observed V1 S7 allocations.

The trusted caller authorizes the profile and selects the configured SQLite
alias. The observed rows are read in one controlled IMMEDIATE transaction.
Passing this diagnosis never proves complete historical point grants/spends,
authorizes migration, or reconstructs chronology from primary keys.
"""

from dataclasses import dataclass
from enum import Enum

from django.db import DatabaseError, connections, transaction

from apps.users.models import UserProfileEcomotor

from .legacy_inventory_reader import LegacyInventoryTransactionError, _check_transaction_boundary
from .models import StatAllocationEvent
from .stat_allocation import InconsistentAllocationStateError, _validate_event


class InvalidStatAllocationAuditProfileIdError(ValueError):
    """The profile ID must be an exact, positive, representable integer."""


class InvalidStatAllocationAuditAliasError(ValueError):
    """An explicit, configured database alias is required."""


class StatAllocationAuditTransactionError(RuntimeError):
    """The requested connection cannot provide a controlled snapshot."""


class StatAllocationAuditProfileNotFoundError(ValueError):
    """The profile does not exist in the selected database."""


class StatAllocationAuditReadError(RuntimeError):
    """A database failure prevented a complete observation."""


class StatAllocationAuditStatus(str, Enum):
    OBSERVED_CONSISTENT = "OBSERVED_CONSISTENT"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True, slots=True)
class StatAllocationAuditIssue:
    code: str
    event_id: int | None


@dataclass(frozen=True, slots=True)
class LegacyStatAllocationAuditResult:
    profile_id: int
    status: StatAllocationAuditStatus
    observed_event_count: int
    s7_valid_event_ids: tuple[int, ...]
    issues: tuple[StatAllocationAuditIssue, ...]
    evidence_limits: tuple[str, ...]


_EVIDENCE_LIMITS = (
    "FULL_POINTS_HISTORY_NOT_PROVEN",
    "POINT_GRANTS_AND_UNRECORDED_SPENDS_NOT_AUDITED",
    "EVENT_IDS_ARE_NOT_FUNCTIONAL_CHRONOLOGY",
)


def _load_events(profile_id, using):
    # Full materialization before leaving atomic; never return model instances.
    return list(StatAllocationEvent.objects.using(using).filter(
        profile_id=profile_id,
    ).order_by("pk"))


def _diagnose(profile, events, using):
    issues = set()
    valid_ids = []
    by_id = {}
    by_key = {}

    for event in events:
        event_id = event.pk if type(event.pk) is int and event.pk > 0 else None
        if event_id is not None:
            by_id.setdefault(event_id, []).append(event)
        if type(event.operation_key) is str:
            # Compare exact keys: do not trim, normalize, log, or expose them.
            by_key.setdefault(event.operation_key, []).append(event)
        try:
            # The S7 writer/replay validator is the sole source of truth for
            # stored identity, ownership, ranges, attributes and equations.
            _validate_event(event, profile, event.operation_key, using)
        except InconsistentAllocationStateError:
            issues.add(StatAllocationAuditIssue("INVALID_S7_EVENT", event_id))
        else:
            valid_ids.append(event.pk)

    for groups, code in ((by_id, "DUPLICATE_EVENT_ID"),
                         (by_key, "DUPLICATE_OPERATION_KEY")):
        for group in groups.values():
            if len(group) > 1:
                for event in group:
                    event_id = event.pk if type(event.pk) is int and event.pk > 0 else None
                    issues.add(StatAllocationAuditIssue(code, event_id))

    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.event_id or 0)))
    return LegacyStatAllocationAuditResult(
        profile_id=profile.pk,
        status=(StatAllocationAuditStatus.INCONSISTENT if ordered
                else StatAllocationAuditStatus.OBSERVED_CONSISTENT),
        observed_event_count=len(events),
        s7_valid_event_ids=tuple(valid_ids),
        issues=ordered,
        evidence_limits=_EVIDENCE_LIMITS,
    )


def audit_legacy_stat_allocations(profile_id: int, *, using: str) -> LegacyStatAllocationAuditResult:
    """Diagnose every observed S7 event; never write, repair or infer history.

    S7 event consistency is independent of current stats, stage and catalogs.
    The result is a point-in-time observation, not a durable completeness proof.
    """
    if type(profile_id) is not int or not 1 <= profile_id <= 2**63 - 1:
        raise InvalidStatAllocationAuditProfileIdError("A positive local profile ID is required.")
    if type(using) is not str or not using or using not in connections:
        raise InvalidStatAllocationAuditAliasError("A configured database alias is required.")
    try:
        _check_transaction_boundary(connections[using])
        with transaction.atomic(using=using):
            profile = UserProfileEcomotor.objects.using(using).filter(pk=profile_id).first()
            if profile is None:
                raise StatAllocationAuditProfileNotFoundError("Profile not found in the selected database.")
            result = _diagnose(profile, _load_events(profile_id, using), using)
        return result
    except LegacyInventoryTransactionError:
        raise StatAllocationAuditTransactionError("A controlled SQLite transaction is required.") from None
    except DatabaseError:
        # Do not leak SQL, operation keys or sensitive IDs via exception chains.
        raise StatAllocationAuditReadError("Stat allocation audit could not be read.") from None
