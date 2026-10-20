"""A3.3 pure rules: candidates and supplied history, never persisted policy.

Only the trusted caller can establish real existence, authorization, sufficiently
current evidence and a transactional lookup. TARGET_CONFIRMED does not activate
A2; S3 V1 remains the writer. No ORM, operator, timestamps, catalog or I/O.

ConfirmedClassificationEvent wraps the original request and before/after
PolicySnapshots, retaining profile, origin, state and revision on both sides.
ClassificationRuleResult exposes the corresponding before/after snapshots:
historical replay values describe that operation, NOT the current profile.
No collections or mutable nested data are accepted. Text is opaque and exact;
there are no speculative physical length or revision limits.
"""

from dataclasses import dataclass
from enum import Enum


class ProfileOrigin(str, Enum):
    LEGACY_V1 = "LEGACY_V1"
    NATIVE_V1 = "NATIVE_V1"
    NATIVE_TARGET = "NATIVE_TARGET"


class TransitionState(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    V1_VERIFIED = "V1_VERIFIED"
    TARGET_PREPARED = "TARGET_PREPARED"
    TARGET_CONFIRMED = "TARGET_CONFIRMED"
    BLOCKED = "BLOCKED"


class ClassificationAction(str, Enum):
    INITIAL = "INITIAL"
    TRANSITION = "TRANSITION"
    BLOCK = "BLOCK"
    RECOVER = "RECOVER"


class ClassificationResultKind(str, Enum):
    NEW_CANDIDATE = "NEW_CANDIDATE"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"


class InvalidClassificationInputError(ValueError):
    """Wrong representation, identity scope or required request content."""


class ForbiddenClassificationTransitionError(ValueError):
    """The proposed initial state or action/state relationship is forbidden."""


class ClassificationOriginConflictError(ValueError):
    """A new operation attempts to change the confirmed origin."""


class StaleClassificationRevisionError(ValueError):
    """Expected revision differs from the required current revision/absence."""


class ClassificationContentConflictError(ValueError):
    """The same conceptual identity contains a different original request."""


class InconsistentClassificationHistoryError(ValueError):
    """Supplied history is insufficient, foreign or internally contradictory."""


def _positive_integer(value):
    return type(value) is int and value > 0


def _text(value):
    return type(value) is str and len(value) > 0


@dataclass(frozen=True, slots=True)
class ClassificationRequest:
    profile_id: int
    operation_key: str
    action: ClassificationAction
    origin: ProfileOrigin
    target_state: TransitionState
    expected_revision: int | None
    incident_reference: str | None = None
    blocking_operation_key: str | None = None

    def __post_init__(self):
        if (not _positive_integer(self.profile_id) or not _text(self.operation_key)
                or type(self.action) is not ClassificationAction
                or type(self.origin) is not ProfileOrigin
                or type(self.target_state) is not TransitionState
                or (self.expected_revision is not None and not _positive_integer(self.expected_revision))
                or any(value is not None and type(value) is not str for value in
                       (self.incident_reference, self.blocking_operation_key))):
            raise InvalidClassificationInputError("Invalid classification request structure.")


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    profile_id: int
    origin: ProfileOrigin
    transition_state: TransitionState
    revision: int

    def __post_init__(self):
        if (not _positive_integer(self.profile_id) or not _positive_integer(self.revision)
                or type(self.origin) is not ProfileOrigin
                or type(self.transition_state) is not TransitionState):
            raise InvalidClassificationInputError("Invalid policy snapshot structure.")


@dataclass(frozen=True, slots=True)
class ConfirmedClassificationEvent:
    """Caller-supplied historical evidence, not proof of database confirmation."""
    request: ClassificationRequest
    before: PolicySnapshot | None
    after: PolicySnapshot

    def __post_init__(self):
        if (type(self.request) is not ClassificationRequest
                or (self.before is not None and type(self.before) is not PolicySnapshot)
                or type(self.after) is not PolicySnapshot):
            raise InconsistentClassificationHistoryError("Invalid historical event structure.")


@dataclass(frozen=True, slots=True)
class ClassificationRuleResult:
    """Calculated candidate or supplied historical states; no applied/XP flags."""
    kind: ClassificationResultKind
    before: PolicySnapshot | None
    after: PolicySnapshot

    def __post_init__(self):
        if (type(self.kind) is not ClassificationResultKind
                or (self.before is not None and type(self.before) is not PolicySnapshot)
                or type(self.after) is not PolicySnapshot):
            raise InvalidClassificationInputError("Invalid classification result structure.")


def _initial_state(origin):
    if origin is ProfileOrigin.LEGACY_V1:
        return TransitionState.PENDING_REVIEW
    if origin is ProfileOrigin.NATIVE_V1:
        return TransitionState.V1_VERIFIED
    return TransitionState.TARGET_CONFIRMED


def _forward_pair(before, after):
    return (before, after) in (
        (TransitionState.PENDING_REVIEW, TransitionState.V1_VERIFIED),
        (TransitionState.V1_VERIFIED, TransitionState.TARGET_PREPARED),
        (TransitionState.TARGET_PREPARED, TransitionState.TARGET_CONFIRMED),
    )


def _recovery_destination(request, blocked_before, blocking_event, *, historical=False):
    if type(blocking_event) is not ConfirmedClassificationEvent:
        raise InconsistentClassificationHistoryError("Original blocking evidence is required.")
    if blocking_event.request.action is not ClassificationAction.BLOCK:
        raise InconsistentClassificationHistoryError("The linked event is not a block.")
    _validate_history(blocking_event, None)
    if (not _text(request.blocking_operation_key)
            or request.blocking_operation_key != blocking_event.request.operation_key
            or blocking_event.after != blocked_before
            or request.profile_id != blocking_event.request.profile_id
            or request.origin is not blocking_event.request.origin):
        raise InconsistentClassificationHistoryError("Blocking evidence does not match the recovery.")
    if request.operation_key == blocking_event.request.operation_key:
        error = InconsistentClassificationHistoryError if historical else ClassificationContentConflictError
        raise error("Recovery and block must have distinct operation identities.")
    return blocking_event.before.transition_state


def _validate_history(event, blocking_event):
    """Check original evidence, not current-policy eligibility or revision.

    Historical action relationships are invariants of the supplied operation.
    Never call the new-candidate path or synthesize missing evidence from current.
    """
    request, before, after = event.request, event.before, event.after
    if (after.profile_id != request.profile_id or after.origin is not request.origin
            or after.transition_state is not request.target_state):
        raise InconsistentClassificationHistoryError("Historical identity or destination is inconsistent.")
    if request.action is ClassificationAction.INITIAL:
        if (before is not None or request.expected_revision is not None or after.revision != 1
                or after.transition_state is not _initial_state(request.origin)):
            raise InconsistentClassificationHistoryError("Invalid historical first classification.")
        return
    if (before is None or before.profile_id != request.profile_id or before.origin is not request.origin
            or request.expected_revision != before.revision or after.revision != before.revision + 1):
        raise InconsistentClassificationHistoryError("Historical origin or revision is inconsistent.")
    if request.action is ClassificationAction.TRANSITION:
        valid = _forward_pair(before.transition_state, after.transition_state)
    elif request.action is ClassificationAction.BLOCK:
        valid = (before.transition_state is not TransitionState.BLOCKED
                 and after.transition_state is TransitionState.BLOCKED and _text(request.incident_reference))
    else:  # RECOVER, with the original block even if current is no longer blocked.
        if before.transition_state is not TransitionState.BLOCKED:
            raise InconsistentClassificationHistoryError("Historical recovery did not start blocked.")
        valid = after.transition_state is _recovery_destination(request, before, blocking_event, historical=True)
    if not valid:
        raise InconsistentClassificationHistoryError("Historical action and states are inconsistent.")


def _new_candidate(request, current, blocking_event):
    if current is None:
        if request.action is not ClassificationAction.INITIAL:
            raise ForbiddenClassificationTransitionError("First classification requires INITIAL.")
        if request.expected_revision is not None:
            raise StaleClassificationRevisionError("First classification requires absence of revision.")
        if request.target_state is not _initial_state(request.origin):
            raise ForbiddenClassificationTransitionError("Initial state does not match origin.")
        revision = 1
    else:
        if request.action is ClassificationAction.INITIAL:
            raise ForbiddenClassificationTransitionError("The profile already has a policy.")
        if request.origin is not current.origin:
            raise ClassificationOriginConflictError("Confirmed origin cannot be changed.")
        if request.expected_revision != current.revision:
            raise StaleClassificationRevisionError("Expected revision does not match current policy.")
        if request.action is ClassificationAction.TRANSITION:
            valid = _forward_pair(current.transition_state, request.target_state)
        elif request.action is ClassificationAction.BLOCK:
            if not _text(request.incident_reference):
                raise InvalidClassificationInputError("A nonempty incident reference is required.")
            valid = (current.transition_state is not TransitionState.BLOCKED
                     and request.target_state is TransitionState.BLOCKED)
        else:
            if current.transition_state is not TransitionState.BLOCKED:
                raise ForbiddenClassificationTransitionError("Recovery requires a blocked policy.")
            valid = request.target_state is _recovery_destination(request, current, blocking_event)
        if not valid:
            raise ForbiddenClassificationTransitionError("Action/state transition is forbidden.")
        revision = current.revision + 1
    after = PolicySnapshot(request.profile_id, request.origin, request.target_state, revision)
    return ClassificationRuleResult(ClassificationResultKind.NEW_CANDIDATE, current, after)


def evaluate_classification_rules(
    request: ClassificationRequest, *, current: PolicySnapshot | None,
    recorded_event: ConfirmedClassificationEvent | None = None,
    blocking_event: ConfirmedClassificationEvent | None = None,
) -> ClassificationRuleResult:
    """Evaluate supplied data; do not look up, authorize or confirm anything.

    Validate typed representations first, then historical identity/integrity and
    exact original content. Only without recorded_event evaluate current revision
    and new eligibility. Current revision/state never rewrite historical results.
    """
    if (type(request) is not ClassificationRequest
            or (current is not None and type(current) is not PolicySnapshot)):
        raise InvalidClassificationInputError("Typed request and optional policy are required.")
    if current is not None and current.profile_id != request.profile_id:
        raise InvalidClassificationInputError("Current policy belongs to a different profile.")
    for event in (recorded_event, blocking_event):
        if event is not None and type(event) is not ConfirmedClassificationEvent:
            raise InconsistentClassificationHistoryError("Typed historical evidence is required.")
    if recorded_event is not None:
        original = recorded_event.request
        if (original.profile_id != request.profile_id or original.operation_key != request.operation_key):
            raise InconsistentClassificationHistoryError("Recorded event identity does not match request.")
        _validate_history(recorded_event, blocking_event)
        if original != request:
            raise ClassificationContentConflictError("Original classification content differs.")
        return ClassificationRuleResult(
            ClassificationResultKind.HISTORICAL_REPLAY, recorded_event.before, recorded_event.after,
        )
    return _new_candidate(request, current, blocking_event)
