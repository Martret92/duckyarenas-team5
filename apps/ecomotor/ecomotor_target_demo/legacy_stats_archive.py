"""Pure, read-only verifier for persisted synthetic CUACK playable histories.

DIAG-ATR-OBJ-02-SNAP-01 / Phase A. Inputs are explicit JSON-shaped values,
not ORM instances. Nothing here grants gameplay permission or calls A4.
There is deliberately no CUACK/ESP alias, conversion, recovery or fallback.
This module is NOT wired into services or HTTP in Phase A.
"""

from dataclasses import dataclass
import re

from .data import CATALOG_ID, MAX_XP, OPTION_CODES, VERSION

LEGACY_DEFINITION_VERSION = "persist-stats-demo-2026-10-22-v1"
LEGACY_STAT_CODES = ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")
LEGACY_BUDGET = 45


class InvalidLegacyArchiveError(ValueError):
    """Historical synthetic evidence is incomplete, contradictory or unknown."""


def _fail(message):
    raise InvalidLegacyArchiveError(message)


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        _fail("Invalid exact historical object structure.")


def _integer(value, *, positive=False, maximum=MAX_XP):
    if type(value) is not int or value < (1 if positive else 0) or value > maximum:
        _fail("Historical numbers must be exact bounded nonnegative integers.")
    return value


def _identity(value):
    if type(value) is not str or not value.strip():
        _fail("Invalid historical identity.")
    return value


def _pairs(value):
    """Require original JSON arrays, including canonical order and no aliases."""
    if type(value) is not list or len(value) != len(LEGACY_STAT_CODES):
        _fail("Six exact historical JSON pairs are required.")
    result = []
    for index, pair in enumerate(value):
        if type(pair) is not list or len(pair) != 2 or type(pair[0]) is not str:
            _fail("Invalid historical attribute pair.")
        if pair[0] != LEGACY_STAT_CODES[index]:
            _fail("Historical attribute order, coverage or code is invalid.")
        result.append((pair[0], _integer(pair[1])))
    return tuple(result)



@dataclass(frozen=True, slots=True)
class LegacyStats:
    bases: tuple[tuple[str, int], ...]
    increments: tuple[tuple[str, int], ...]
    effective: tuple[tuple[str, int], ...]
    budget: int
    points_used: int
    points_remaining: int


@dataclass(frozen=True, slots=True)
class LegacyConfiguration:
    id: int
    revision: int
    option_code: str
    catalog_id: str
    catalog_version: str
    definition_version: str
    stats: LegacyStats


@dataclass(frozen=True, slots=True)
class LegacyPlayableSnapshot:
    progress_id: int
    catalog_pk: int
    revision: int
    active_option: str | None
    configurations: tuple[LegacyConfiguration, ...]


@dataclass(frozen=True, slots=True)
class LegacyPlayableEvent:
    event_id: int
    action: str
    option_code: str
    before: LegacyPlayableSnapshot
    after: LegacyPlayableSnapshot


@dataclass(frozen=True, slots=True)
class LegacyPlayableArchive:
    definition_version: str
    state: LegacyPlayableSnapshot
    events: tuple[LegacyPlayableEvent, ...]


def _option(code):
    if type(code) is not str or code not in OPTION_CODES:
        _fail("Unknown historical synthetic playable option.")
    return code


def _stats(bases, increments, budget):
    b = _pairs(bases)
    i = _pairs(increments)
    if any(value != 0 for _, value in b):
        _fail("Historical v1 synthetic bases must all be zero.")
    if _integer(budget) != LEGACY_BUDGET:
        _fail("Unexpected historical synthetic budget.")
    used = sum(n for _, n in i)
    if used > budget:
        _fail("Historical allocation exceeds its original budget.")
    effective = tuple((code, base + amount) for (code, base), (_, amount) in zip(b, i))
    if any(number > MAX_XP for _, number in effective):
        _fail("Historical effective value out of range.")
    return LegacyStats(b, i, effective, budget, used, budget - used)


def _configuration(raw, *, catalog_id, catalog_version):
    _keys(raw, ("id", "revision", "option_code", "catalog_id", "catalog_version",
                "definition_version", "bases", "increments", "budget"))
    cid, rev = _integer(raw["id"], positive=True), _integer(raw["revision"], positive=True)
    opt = _option(raw["option_code"])
    if (type(raw["catalog_id"]) is not str or raw["catalog_id"] != catalog_id
            or type(raw["catalog_version"]) is not str or raw["catalog_version"] != catalog_version
            or type(raw["definition_version"]) is not str
            or raw["definition_version"] != LEGACY_DEFINITION_VERSION):
        _fail("Historical definition/catalog version or identity mismatch.")
    return LegacyConfiguration(cid, rev, opt, catalog_id, catalog_version,
                               LEGACY_DEFINITION_VERSION,
                               _stats(raw["bases"], raw["increments"], raw["budget"]))


def _snapshot(raw, *, progress_id, catalog_pk, catalog_id, catalog_version):
    _keys(raw, ("progress_id", "catalog_id", "revision", "active_option", "configurations"))
    if (type(raw["progress_id"]) is not int or raw["progress_id"] != progress_id
            or type(raw["catalog_id"]) is not int or raw["catalog_id"] != catalog_pk):
        _fail("Historical progress/catalog foreign references mismatch.")
    revision = _integer(raw["revision"])
    if type(raw["configurations"]) is not list:
        _fail("Historical configurations must be an explicit JSON list.")
    configs = tuple(_configuration(c, catalog_id=catalog_id, catalog_version=catalog_version)
                    for c in raw["configurations"])
    codes = tuple(c.option_code for c in configs)
    if (codes != tuple(sorted(set(codes))) or len({c.id for c in configs}) != len(configs)
            or (not configs and (revision != 0 or raw["active_option"] is not None))
            or (configs and (revision == 0 or type(raw["active_option"]) is not str
                             or raw["active_option"] not in codes))):
        _fail("Contradictory historical active state/configuration identity.")
    return LegacyPlayableSnapshot(progress_id, catalog_pk, revision,
                                  raw["active_option"], configs)


def _request(raw):
    _keys(raw, ("action", "option_code", "increments", "expected_revision", "configuration_revision"))
    action = raw["action"]
    if type(action) is not str or action not in ("configure", "switch", "redistribute"):
        _fail("Unknown historical action.")
    code = _option(raw["option_code"])
    exp = raw["expected_revision"]
    if exp is not None:
        _integer(exp, positive=True)
    if action != "configure" and exp is None:
        _fail("Missing historical state revision.")
    confrev = raw["configuration_revision"]
    if action == "redistribute":
        _integer(confrev, positive=True)
    elif confrev is not None:
        _fail("Unexpected historical configuration revision.")
    if action == "switch":
        if raw["increments"] is not None:
            _fail("Historical switch cannot carry increments.")
        increments = None
    else:
        increments = _pairs(raw["increments"])
        if sum(number for _, number in increments) > MAX_XP:
            _fail("Historical request values exceed original numeric range.")
    return action, code, increments, exp, confrev


def _find(snapshot, code):
    return next((c for c in snapshot.configurations if c.option_code == code), None)


def _validate_event(raw, previous, *, progress_id, catalog_pk, catalog_id, catalog_version):
    _keys(raw, ("event_id", "progress_id", "operation_key", "action", "option_code",
                "original_request", "before", "after"))
    event_id = _integer(raw["event_id"], positive=True)
    if type(raw["progress_id"]) is not int or raw["progress_id"] != progress_id:
        _fail("Event belongs to a different historical progress.")
    if type(raw["operation_key"]) is not str or re.fullmatch(r"[0-9a-f]{32}", raw["operation_key"]) is None:
        _fail("Invalid historical operation identity.")
    action, code, increments, expected, config_rev = _request(raw["original_request"])
    if (type(raw["action"]) is not str or raw["action"] != action
            or type(raw["option_code"]) is not str or raw["option_code"] != code):
        _fail("Event identity contradicts original request.")
    before = _snapshot(raw["before"], progress_id=progress_id, catalog_pk=catalog_pk,
                       catalog_id=catalog_id, catalog_version=catalog_version)
    after = _snapshot(raw["after"], progress_id=progress_id, catalog_pk=catalog_pk,
                      catalog_id=catalog_id, catalog_version=catalog_version)
    required = None if previous.revision == 0 else previous.revision
    if before != previous or expected != required or after.revision != previous.revision + 1:
        _fail("Contradictory historical chain/revision.")
    old, new = _find(previous, code), _find(after, code)
    if new is None:
        _fail("Historical transition lost the chosen configuration.")
    before_others = tuple(c for c in previous.configurations if c.option_code != code)
    after_others = tuple(c for c in after.configurations if c.option_code != code)
    if before_others != after_others:
        _fail("Historical action changed another option.")
    if action == "configure":
        valid = old is None and new.revision == 1 and after.active_option == code
    elif action == "switch":
        valid = old == new and previous.active_option != code and after.active_option == code
    else:
        valid = (old is not None and old.id == new.id and new.revision == old.revision + 1
                 and old.catalog_id == new.catalog_id
                 and old.catalog_version == new.catalog_version
                 and old.definition_version == new.definition_version
                 and old.stats.bases == new.stats.bases and old.stats.budget == new.stats.budget
                 and old.stats.increments != new.stats.increments
                 and config_rev == old.revision and after.active_option == previous.active_option)
    if action != "switch" and increments != new.stats.increments:
        valid = False
    if not valid:
        _fail("Historical request/transition contradiction.")
    return LegacyPlayableEvent(event_id, action, code, before, after)


def validate_legacy_playable_archive(*, progress_id, catalog_pk, catalog_id,
                                     catalog_version, events, current_state):
    """Validate complete V1 CUACK JSON evidence without IO or A4 imports.

    ``events`` is an ordered list/tuple of dicts with exact keys event_id,
    progress_id, operation_key, action, option_code, original_request, before,
    after. ``current_state`` is the exact persisted current-state JSON shape
    produced by the existing demo reader. The public API accepts explicit
    caller data only; it neither opens a database nor authorizes gameplay.
    A nonempty chain is required to classify a history as legacy.
    """
    _integer(progress_id, positive=True)
    _integer(catalog_pk, positive=True)
    _identity(catalog_id)
    _identity(catalog_version)
    if catalog_id != CATALOG_ID or catalog_version != VERSION:
        _fail("This is not the exact original synthetic demo catalog.")
    if type(events) not in (list, tuple) or not events:
        _fail("A legacy archive requires an explicit nonempty event history.")
    previous = LegacyPlayableSnapshot(progress_id, catalog_pk, 0, None, ())
    result = []
    last_id = 0
    keys = set()
    for raw in events:
        event = _validate_event(raw, previous, progress_id=progress_id, catalog_pk=catalog_pk,
                                catalog_id=catalog_id, catalog_version=catalog_version)
        if event.event_id <= last_id or raw["operation_key"] in keys:
            _fail("Historical events must have increasing unique IDs and operation keys.")
        last_id = event.event_id
        keys.add(raw["operation_key"])
        result.append(event)
        previous = event.after
    state = _snapshot(current_state, progress_id=progress_id, catalog_pk=catalog_pk,
                      catalog_id=catalog_id, catalog_version=catalog_version)
    if previous != state:
        _fail("Current historical tables do not match reconstructed event chain.")
    # This immutable representation is separate from active A4 preparations.
    return LegacyPlayableArchive(LEGACY_DEFINITION_VERSION, state, tuple(result))
