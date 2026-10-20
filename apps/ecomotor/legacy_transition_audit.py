"""A3.1: audit supplied V1 evidence; never extract, repair or authorize migration.

COMPATIBLE covers only observable profile/stats/XP and evolution references.
It does not verify historical stage attributes (not persisted in EvolutionEvent),
level derivation, points history, specialization/domain/ranks, Duckies equipment,
EvolutionItem, classification or target migration. Coverage is a caller assertion,
not proof of trusted extraction. No chronology is inferred from primary keys.

Malformed representation raises InvalidLegacySnapshotError. Representable but
invalid persisted values produce issues. Integer ranges below describe the
current SQLite V1 backend (including its signed IntegerField range), not gameplay
limits or a backend inspection. No claim is made about other physical backends.
"""

from dataclasses import dataclass, fields
from enum import Enum


class InvalidLegacySnapshotError(ValueError):
    """Evidence is not composed of the explicit, strictly typed snapshots."""


class LegacyAuditStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    REQUIRES_DECISION = "REQUIRES_DECISION"
    INCONSISTENT = "INCONSISTENT"


_BIG_MAX = 2**63 - 1


class _Record:
    __slots__ = ()

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            expected = field.type
            if expected is int:
                valid = type(value) is int
            elif expected is str:
                valid = type(value) is str
            else:  # Only the optional active specialization code uses a union.
                valid = value is None or type(value) is str
            if not valid:
                raise InvalidLegacySnapshotError("Invalid snapshot field type: " + field.name)
            if field.name == "id" or field.name.endswith("_id"):
                if not 1 <= value <= _BIG_MAX:
                    raise InvalidLegacySnapshotError("Invalid record identity: " + field.name)


@dataclass(frozen=True, slots=True)
class LegacyProfileSnapshot(_Record):
    profile_id: int
    historical_xp_total: int
    current_level: int
    current_stage_code: str
    active_specialization_code: str | None = None


@dataclass(frozen=True, slots=True)
class LegacyCharacterStatsSnapshot(_Record):
    profile_id: int
    atk: int
    def_stat: int
    log_stat: int
    spe: int
    vel: int
    int_stat: int
    available_points: int


@dataclass(frozen=True, slots=True)
class LegacyXPEventSnapshot(_Record):
    id: int
    profile_id: int
    operation_key: str
    amount: int
    xp_before: int
    xp_after: int


@dataclass(frozen=True, slots=True)
class LegacyEvolutionEventSnapshot(_Record):
    id: int
    profile_id: int
    xp_event_id: int
    stage_id: int


@dataclass(frozen=True, slots=True)
class LegacyStageSnapshot(_Record):
    id: int
    code: str
    ordinal: int
    minimum_xp: int


@dataclass(frozen=True, slots=True)
class LegacyAuditCoverage:
    xp_events_complete: bool
    evolution_events_complete: bool
    stages_complete: bool
    character_stats_observed: bool

    def __post_init__(self):
        if any(type(getattr(self, field.name)) is not bool for field in fields(self)):
            raise InvalidLegacySnapshotError("Coverage flags must be exact booleans.")


def _collection(value, item_type):
    if type(value) not in (tuple, list) or any(type(item) is not item_type for item in value):
        raise InvalidLegacySnapshotError("An explicit list/tuple of typed snapshots is required.")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class LegacyAuditSnapshot:
    profile: LegacyProfileSnapshot
    character_stats: LegacyCharacterStatsSnapshot | None
    xp_events: tuple[LegacyXPEventSnapshot, ...]
    evolution_events: tuple[LegacyEvolutionEventSnapshot, ...]
    stages: tuple[LegacyStageSnapshot, ...]
    coverage: LegacyAuditCoverage

    def __post_init__(self):
        if type(self.profile) is not LegacyProfileSnapshot or type(self.coverage) is not LegacyAuditCoverage:
            raise InvalidLegacySnapshotError("Typed profile and coverage required.")
        if self.character_stats is not None and type(self.character_stats) is not LegacyCharacterStatsSnapshot:
            raise InvalidLegacySnapshotError("Invalid statistics snapshot.")
        for name, item_type in (("xp_events", LegacyXPEventSnapshot),
                                ("evolution_events", LegacyEvolutionEventSnapshot),
                                ("stages", LegacyStageSnapshot)):
            object.__setattr__(self, name, _collection(getattr(self, name), item_type))


@dataclass(frozen=True, slots=True)
class LegacyAuditIssue:
    """Stable code and local record reference; never includes operation keys."""
    code: str
    severity: LegacyAuditStatus
    record_type: str
    record_id: int | None = None

    def __post_init__(self):
        if (type(self.code) is not str or not self.code
                or type(self.record_type) is not str or not self.record_type
                or type(self.severity) is not LegacyAuditStatus
                or self.severity is LegacyAuditStatus.COMPATIBLE
                or (self.record_id is not None and
                    (type(self.record_id) is not int or not 1 <= self.record_id <= _BIG_MAX))):
            raise InvalidLegacySnapshotError("Invalid diagnostic.")


@dataclass(frozen=True, slots=True)
class LegacyAuditResult:
    """Only structural compatibility in the V1 subset stated in this module.

    Never migration approval, classification, XP eligibility or a Duckies audit.
    """
    profile_id: int
    status: LegacyAuditStatus
    issues: tuple[LegacyAuditIssue, ...]

    def __post_init__(self):
        if (type(self.profile_id) is not int or not 1 <= self.profile_id <= _BIG_MAX
                or type(self.status) is not LegacyAuditStatus):
            raise InvalidLegacySnapshotError("Invalid audit result.")
        object.__setattr__(self, "issues", _collection(self.issues, LegacyAuditIssue))


def _code_valid(value, maximum=32):
    # No trimming/normalization; S3 also treats opaque nonempty strings literally.
    return 1 <= len(value) <= maximum


def audit_legacy_transition(snapshot: LegacyAuditSnapshot) -> LegacyAuditResult:
    """Audit observations without assuming completeness or historical catalogs.

    Missing references are inconsistent only with complete reference inventories.
    Available stage attributes are checked structurally, never used to reconstruct
    evolutions or calculate historical levels. Duplicated causes remain ambiguous;
    all matching observed owners are checked rather than choosing an input row.
    """
    if type(snapshot) is not LegacyAuditSnapshot:
        raise InvalidLegacySnapshotError("A LegacyAuditSnapshot is required.")
    profile = snapshot.profile
    coverage = snapshot.coverage
    issues = set()
    inconsistent = LegacyAuditStatus.INCONSISTENT
    review = LegacyAuditStatus.REQUIRES_DECISION

    def issue(code, severity, kind, record_id=None):
        issues.add(LegacyAuditIssue(code, severity, kind, record_id))

    def duplicate(rows, key, code, kind):
        groups = {}
        for row in rows:
            groups.setdefault(key(row), []).append(row)
        for group in groups.values():
            if len(group) > 1:
                for row in group:
                    issue(code, inconsistent, kind, row.id)
        return groups

    for complete, kind in ((coverage.xp_events_complete, "xp_events"),
                           (coverage.evolution_events_complete, "evolution_events"),
                           (coverage.stages_complete, "stages"),
                           (coverage.character_stats_observed, "character_stats")):
        if not complete:
            issue("EVIDENCE_INCOMPLETE", review, kind)

    if (not 0 <= profile.historical_xp_total <= _BIG_MAX
            or not 1 <= profile.current_level <= _BIG_MAX
            or not _code_valid(profile.current_stage_code)
            or (profile.active_specialization_code is not None
                and not _code_valid(profile.active_specialization_code))):
        issue("INVALID_PROFILE_VALUES", inconsistent, "profile", profile.profile_id)

    stats = snapshot.character_stats
    if stats is None:
        if coverage.character_stats_observed:
            issue("CHARACTER_STATS_MISSING", inconsistent, "profile", profile.profile_id)
    else:
        if stats.profile_id != profile.profile_id:
            issue("STATS_PROFILE_MISMATCH", inconsistent, "character_stats", stats.profile_id)
        if (any(not -2**63 <= getattr(stats, name) <= _BIG_MAX for name in
                ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat"))
                or not 0 <= stats.available_points <= _BIG_MAX):
            issue("INVALID_STATS_VALUES", inconsistent, "character_stats", stats.profile_id)

    xp_by_id = duplicate(snapshot.xp_events, lambda row: row.id, "DUPLICATE_XP_ID", "xp_event")
    duplicate(snapshot.xp_events, lambda row: (row.profile_id, row.operation_key),
              "DUPLICATE_OPERATION_KEY", "xp_event")
    for event in snapshot.xp_events:
        if event.profile_id != profile.profile_id:
            issue("XP_PROFILE_MISMATCH", inconsistent, "xp_event", event.id)
        if (not 1 <= event.amount <= _BIG_MAX or not 0 <= event.xp_before <= _BIG_MAX
                or not 0 <= event.xp_after <= _BIG_MAX
                or event.xp_after != event.xp_before + event.amount
                or not _code_valid(event.operation_key, 255)):
            issue("INVALID_XP_SNAPSHOT", inconsistent, "xp_event", event.id)
        if event.profile_id == profile.profile_id and event.xp_after > profile.historical_xp_total:
            issue("XP_EXCEEDS_PROFILE_TOTAL", inconsistent, "xp_event", event.id)
    # Only an observed upper endpoint, never a sum, inferred chronology or a
    # requirement that history starts at zero/reconstructs all accumulated XP.
    observed_after = max((event.xp_after for event in snapshot.xp_events
                          if event.profile_id == profile.profile_id), default=0)
    if profile.historical_xp_total > observed_after:
        issue("ACCUMULATED_XP_WITHOUT_SUFFICIENT_HISTORY", review, "profile", profile.profile_id)

    stages_by_id = duplicate(snapshot.stages, lambda row: row.id, "DUPLICATE_STAGE_ID", "stage")
    duplicate(snapshot.stages, lambda row: row.code, "DUPLICATE_STAGE_CODE", "stage")
    duplicate(snapshot.stages, lambda row: row.ordinal, "DUPLICATE_STAGE_ORDINAL", "stage")
    for stage in snapshot.stages:
        if (not _code_valid(stage.code) or not 1 <= stage.ordinal <= 7
                or not 0 <= stage.minimum_xp <= _BIG_MAX):
            issue("INVALID_STAGE_VALUES", inconsistent, "stage", stage.id)
    if not any(stage.code == profile.current_stage_code for stage in snapshot.stages):
        issue("CURRENT_STAGE_NOT_FOUND", inconsistent if coverage.stages_complete else review,
              "profile", profile.profile_id)

    duplicate(snapshot.evolution_events, lambda row: row.id, "DUPLICATE_EVOLUTION_ID", "evolution_event")
    duplicate(snapshot.evolution_events, lambda row: (row.profile_id, row.stage_id),
              "DUPLICATE_PROFILE_EVOLUTION", "evolution_event")
    for event in snapshot.evolution_events:
        if event.profile_id != profile.profile_id:
            issue("EVOLUTION_PROFILE_MISMATCH", inconsistent, "evolution_event", event.id)
        causes = xp_by_id.get(event.xp_event_id, ())
        if not causes:
            issue("XP_CAUSE_NOT_FOUND", inconsistent if coverage.xp_events_complete else review,
                  "evolution_event", event.id)
        elif any(cause.profile_id != event.profile_id for cause in causes):
            issue("EVOLUTION_CAUSE_PROFILE_MISMATCH", inconsistent, "evolution_event", event.id)
        if event.stage_id not in stages_by_id:
            issue("STAGE_REFERENCE_NOT_FOUND", inconsistent if coverage.stages_complete else review,
                  "evolution_event", event.id)

    ordered = tuple(sorted(issues, key=lambda item: (
        item.code, item.record_type, item.record_id or 0, item.severity.value,
    )))
    status = (inconsistent if any(item.severity is inconsistent for item in ordered)
              else review if ordered else LegacyAuditStatus.COMPATIBLE)
    return LegacyAuditResult(profile.profile_id, status, ordered)
