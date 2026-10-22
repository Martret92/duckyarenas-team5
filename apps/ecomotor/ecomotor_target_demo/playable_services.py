"""Session-owned synthetic selections. No XP writes or production authorization.

The outer transaction and ownership/history readers are shared with Step 2;
none of its public functions that open transactions are called inside atomic.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import json
import re
from secrets import token_hex

from django.core import signing
from django.db import DatabaseError, IntegrityError, OperationalError, transaction

from apps.ecomotor.target_progression import calculate_target_progression
from apps.ecomotor.target_stats_config_validation import (TargetStatsCatalogContext,
    validate_target_stats_definition, InvalidTargetStatsDefinitionError)
from apps.ecomotor.target_stats_preparation import prepare_target_stats_configuration, PreparedTargetStatsConfiguration
from apps.ecomotor.target_stats_validation import validate_target_stats, InvalidTargetStatsError

from . import services as xp
from .catalog import exact_catalog
from .data import MAX_XP, OPTION_CODES
from .models import (DemoTargetProgress, DemoTargetOptionConfiguration as Configuration,
    DemoTargetPlayableState as State, DemoTargetPlayableEvent as Event)
from .stats_definitions import synthetic_definition, ZERO_BASES, DEMO_BUDGET

SALT = "ecomotor.persistent-demo.playable.v1"
ACTIONS = ("configure", "switch", "redistribute")


class DemoRevisionError(xp.DemoConflictError):
    """Expected state/configuration revision is stale or incompatible."""


@dataclass(frozen=True, slots=True)
class ConfigurationSnapshot:
    id: int
    revision: int
    prepared: PreparedTargetStatsConfiguration


@dataclass(frozen=True, slots=True)
class PlayableSnapshot:
    progress_id: int
    catalog_id: int
    revision: int
    active_option: str | None
    configurations: tuple[ConfigurationSnapshot, ...]


@dataclass(frozen=True, slots=True)
class PlayableResult:
    event_id: int | None
    action: str
    option_code: str
    before: PlayableSnapshot
    after: PlayableSnapshot
    replay: bool = False
    changed: bool = True


def _revision(value, *, absent=False):
    if absent and value is None:
        return
    if type(value) is not int or not 1 <= value <= MAX_XP:
        raise xp.DemoInputError("Revisión exacta positiva requerida.")


def _option(code):
    if type(code) is not str or code not in OPTION_CODES:
        raise xp.DemoInputError("Opción sintética no válida.")


def _request(action, option, increments, expected_revision, configuration_revision):
    _option(option)
    if type(action) is not str or action not in ACTIONS:
        raise xp.DemoInputError("Operación jugable no válida.")
    _revision(expected_revision, absent=action == "configure")
    if action == "redistribute":
        _revision(configuration_revision)
    elif configuration_revision is not None:
        raise xp.DemoInputError("Revisión de configuración inesperada.")
    if action == "switch":
        if increments is not None:
            raise xp.DemoInputError("Un cambio no recibe incrementos.")
        pairs = None
    else:
        # Canonicalize the original request without losing duplicates. The
        # actual allocation/budget is checked through A4.3 below.
        pairs = validate_target_stats(ZERO_BASES, increments, budget=MAX_XP).increments
    return {"action": action, "option_code": option,
        "increments": None if pairs is None else [list(pair) for pair in pairs],
        "expected_revision": expected_revision, "configuration_revision": configuration_revision}


def _canonical(value):
    # JSON comparison deliberately distinguishes true from 1.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _encode(snapshot):
    return {"progress_id": snapshot.progress_id, "catalog_id": snapshot.catalog_id,
        "revision": snapshot.revision, "active_option": snapshot.active_option,
        "configurations": [{"id": config.id, "revision": config.revision,
            "option_code": config.prepared.definition.option_code,
            "catalog_id": config.prepared.definition.catalog_id,
            "catalog_version": config.prepared.definition.catalog_version,
            "definition_version": config.prepared.definition.definition_version,
            "bases": [list(p) for p in config.prepared.definition.bases],
            "increments": [list(p) for p in config.prepared.calculation.increments],
            "budget": config.prepared.calculation.budget} for config in snapshot.configurations]}


def _decode(value, progress):
    """Validate complete historical snapshots using their persisted definitions."""
    try:
        if type(value) is not dict or set(value) != {"progress_id", "catalog_id", "revision", "active_option", "configurations"}:
            raise xp.DemoIntegrityError("Estructura de snapshot incoherente.")
        for key, expected in (("progress_id", progress.pk), ("catalog_id", progress.catalog_id)):
            if type(value[key]) is not int or value[key] != expected:
                raise xp.DemoIntegrityError("Referencias históricas incoherentes.")
        revision = value["revision"]
        if type(revision) is not int or not 0 <= revision <= MAX_XP or type(value["configurations"]) is not list:
            raise xp.DemoIntegrityError("Revisión histórica incoherente.")
        context = TargetStatsCatalogContext(progress.catalog.catalog_id, progress.catalog.version)
        configs = []
        for row in value["configurations"]:
            if type(row) is not dict or set(row) != {"id", "revision", "option_code", "catalog_id", "catalog_version", "definition_version", "bases", "increments", "budget"}:
                raise xp.DemoIntegrityError("Configuración histórica incompleta.")
            _revision(row["id"])
            _revision(row["revision"])
            _option(row["option_code"])
            xp._integer(row["budget"])
            definition = validate_target_stats_definition(option_code=row["option_code"],
                catalog_id=row["catalog_id"], catalog_version=row["catalog_version"],
                definition_version=row["definition_version"], bases=row["bases"], expected_catalog=context)
            prepared = prepare_target_stats_configuration(definition=definition, increments=row["increments"],
                budget=row["budget"], expected_catalog=context)
            for _, number in prepared.calculation.effective:
                xp._integer(number)
            configs.append(ConfigurationSnapshot(row["id"], row["revision"], prepared))
        codes = tuple(c.prepared.definition.option_code for c in configs)
        if (codes != tuple(sorted(set(codes))) or len({c.id for c in configs}) != len(configs)
                or (not configs and (revision != 0 or value["active_option"] is not None))
                or (configs and (revision == 0 or type(value["active_option"]) is not str or value["active_option"] not in codes))):
            raise xp.DemoIntegrityError("Estado activo o configuraciones contradictorias.")
        result = PlayableSnapshot(progress.pk, progress.catalog_id, revision, value["active_option"], tuple(configs))
        if _canonical(_encode(result)) != _canonical(value):
            raise xp.DemoIntegrityError("Snapshot no canónico.")
        return result
    except (xp.DemoInputError, InvalidTargetStatsError, InvalidTargetStatsDefinitionError) as error:
        raise xp.DemoIntegrityError("Datos históricos no representables.") from error


def _empty(progress):
    return PlayableSnapshot(progress.pk, progress.catalog_id, 0, None, ())


def _find(snapshot, code):
    return next((c for c in snapshot.configurations if c.prepared.definition.option_code == code), None)


def _validate_event(event, before, progress):
    try:
        raw = event.original_request
        if type(raw) is not dict or set(raw) != {"action", "option_code", "increments", "expected_revision", "configuration_revision"}:
            raise xp.DemoIntegrityError("Solicitud histórica incompleta.")
        request = _request(raw["action"], raw["option_code"], raw["increments"], raw["expected_revision"], raw["configuration_revision"])
        if (_canonical(raw) != _canonical(request) or event.action != request["action"]
                or event.option_code != request["option_code"] or type(event.operation_key) is not str
                or re.fullmatch("[0-9a-f]{32}", event.operation_key) is None):
            raise xp.DemoIntegrityError("Identidad o solicitud histórica contradictoria.")
        observed_before = _decode(event.before, progress)
        after = _decode(event.after, progress)
        code, action = request["option_code"], request["action"]
        old, new = _find(before, code), _find(after, code)
        expected = None if before.revision == 0 else before.revision
        if (observed_before != before or after.revision != before.revision + 1
                or request["expected_revision"] != expected or new is None):
            raise xp.DemoIntegrityError("Cadena o revisiones históricas incoherentes.")
        old_others = tuple(c for c in before.configurations if c.prepared.definition.option_code != code)
        new_others = tuple(c for c in after.configurations if c.prepared.definition.option_code != code)
        if old_others != new_others:
            raise xp.DemoIntegrityError("Una operación alteró otra configuración.")
        if action == "configure":
            valid = old is None and new.revision == 1 and after.active_option == code
        elif action == "switch":
            valid = old == new and before.active_option != code and after.active_option == code
        else:
            valid = (old is not None and old.id == new.id and new.revision == old.revision + 1
                and old.prepared.definition == new.prepared.definition
                and old.prepared.calculation.budget == new.prepared.calculation.budget
                and old.prepared.calculation.increments != new.prepared.calculation.increments
                and request["configuration_revision"] == old.revision and after.active_option == before.active_option)
        if action != "switch" and tuple(map(tuple, request["increments"])) != new.prepared.calculation.increments:
            valid = False
        if not valid:
            raise xp.DemoIntegrityError("Efecto histórico incompatible con la solicitud.")
        return PlayableResult(event.pk, action, code, before, after)
    except (xp.DemoInputError, InvalidTargetStatsError) as error:
        raise xp.DemoIntegrityError("Solicitud histórica inválida.") from error


def _read(progress, alias):
    previous = _empty(progress)
    history = []
    for event in Event.objects.using(alias).filter(progress=progress).order_by("pk"):
        result = _validate_event(event, previous, progress)
        history.append(result)
        previous = result.after
    configs = tuple(Configuration.objects.using(alias).filter(progress=progress).order_by("option_code"))
    states = tuple(State.objects.using(alias).filter(progress=progress).select_related("active_configuration"))
    if configs and (len(states) != 1 or states[0].active_configuration.progress_id != progress.pk):
        raise xp.DemoIntegrityError("Estado activo ajeno o ausente.")
    state = states[0] if states else None
    raw = {"progress_id": progress.pk, "catalog_id": progress.catalog_id,
        "revision": state.revision if state else 0,
        "active_option": state.active_configuration.option_code if state else None,
        "configurations": []}
    for config in configs:
        if config.catalog_id != progress.catalog_id:
            raise xp.DemoIntegrityError("Catálogo ajeno en configuración.")
        raw["configurations"].append({"id": config.pk, "revision": config.revision,
            "option_code": config.option_code, "catalog_id": progress.catalog.catalog_id,
            "catalog_version": progress.catalog.version, "definition_version": config.definition_version,
            "bases": config.bases, "increments": config.increments, "budget": config.budget})
    current = _decode(raw, progress)
    if current != previous:
        raise xp.DemoIntegrityError("El estado guardado no corresponde al historial jugable.")
    return current, tuple(history)


@contextmanager
def _scope(progress, secret):
    if type(progress) is not DemoTargetProgress or progress.pk is None:
        raise xp.DemoInputError("Se requiere una partida persistida.")
    owner = xp._owner(secret)
    db = xp._connection()  # Before atomic; same guarded SQLite/IMMEDIATE boundary.
    if progress._state.db != db.alias:
        raise xp.DemoAccessError("Partida de otra conexión.")
    try:
        with transaction.atomic(using=db.alias):
            current = xp._progress(progress.pk, owner, db.alias)
            xp._history(current, db.alias)
            current.catalog  # Materialize while the transaction is open.
            yield current, db.alias, owner
    except IntegrityError as error:
        raise xp.DemoIntegrityError("Integridad jugable rechazada; operación revertida.") from error
    except OperationalError as error:
        base = getattr(error.__cause__, "sqlite_errorcode", 0) & 255
        cls = xp.DemoBusyError if base in (5, 6) else xp.DemoDatabaseError
        raise cls("Operación jugable no confirmada por la base de datos.") from error
    except DatabaseError as error:
        raise xp.DemoDatabaseError("Operación jugable no confirmada.") from error


def issue_playable_operation(progress, *, action, session_token):
    if type(action) is not str or action not in ACTIONS:
        raise xp.DemoInputError("Propósito jugable inválido.")
    with _scope(progress, session_token) as (current, alias, owner):
        return signing.dumps({"progress": current.pk, "owner": owner, "purpose": action, "key": token_hex(16)}, salt=SALT)


def _key(token, progress, owner, action):
    try:
        if type(token) is not str or len(token) > 1024:
            raise signing.BadSignature("Invalid token")
        value = signing.loads(token, salt=SALT)
        if (type(value) is not dict or set(value) != {"progress", "owner", "purpose", "key"}
                or type(value["progress"]) is not int or value["progress"] != progress.pk
                or value["owner"] != owner or value["purpose"] != action
                or type(value["key"]) is not str or re.fullmatch("[0-9a-f]{32}", value["key"]) is None):
            raise signing.BadSignature("Invalid context")
        return value["key"]
    except signing.BadSignature:
        raise xp.DemoAccessError("Operación jugable no disponible para esta sesión y propósito.") from None


def _operate(progress, *, action, option_code, operation_token, session_token,
             expected_revision, increments=None, configuration_revision=None):
    request = _request(action, option_code, increments, expected_revision, configuration_revision)
    with _scope(progress, session_token) as (current, alias, owner):
        key = _key(operation_token, current, owner, action)
        before, history = _read(current, alias)
        # Switch is deliberately revision-first, even for a destination already
        # active or an operation key found in history.
        if action == "switch" and expected_revision != before.revision:
            raise DemoRevisionError("El estado cambió; recarga antes de cambiar de opción.")
        recorded = Event.objects.using(alias).filter(progress=current, operation_key=key).first()
        if recorded:
            if _canonical(recorded.original_request) != _canonical(request):
                raise xp.DemoConflictError("Identidad jugable reutilizada con otro contenido.")
            result = next(r for r in history if r.event_id == recorded.pk)
            return PlayableResult(result.event_id, result.action, result.option_code,
                result.before, result.after, replay=True, changed=False)
        expected = None if before.revision == 0 else before.revision
        if expected_revision != expected:
            raise DemoRevisionError("Revisión del estado obsoleta.")
        _, catalog = exact_catalog(current.catalog_id, alias)
        calculated = calculate_target_progression(current.xp_total, current.xp_total, catalog)
        if (calculated.level_after != current.current_level or calculated.epoch_after_code != current.current_epoch.code
                or current.current_epoch.catalog_id != current.catalog_id):
            raise xp.DemoIntegrityError("Progreso no coherente con su catálogo.")
        if current.current_level < 8:
            raise xp.DemoInputError("Las doce opciones se desbloquean desde nivel 8.")
        old = _find(before, option_code)
        context = TargetStatsCatalogContext(current.catalog.catalog_id, current.catalog.version)
        if action == "configure":
            if old is not None:
                raise xp.DemoConflictError("Esta opción ya tiene configuración; utiliza cambio o redistribución.")
            prepared = prepare_target_stats_configuration(definition=synthetic_definition(option_code, context),
                increments=increments, budget=DEMO_BUDGET, expected_catalog=context)
        elif old is None:
            raise xp.DemoInputError("Configura primero esta opción.")
        elif action == "redistribute":
            if configuration_revision != old.revision:
                raise DemoRevisionError("Revisión de configuración obsoleta.")
            prepared = prepare_target_stats_configuration(definition=old.prepared.definition, increments=increments,
                budget=old.prepared.calculation.budget, expected_catalog=context)
            if prepared.calculation.increments == old.prepared.calculation.increments:
                return PlayableResult(None, action, option_code, before, before, changed=False)
        elif before.active_option == option_code:
            return PlayableResult(None, action, option_code, before, before, changed=False)
        if before.revision == MAX_XP or (old and action == "redistribute" and old.revision == MAX_XP):
            raise xp.DemoInputError("Revisión fuera del rango SQLite.")
        if action == "configure":
            config = Configuration.objects.using(alias).create(progress=current, option_code=option_code,
                catalog_id=current.catalog_id, definition_version=prepared.definition.definition_version,
                bases=[list(p) for p in prepared.definition.bases], increments=[list(p) for p in prepared.calculation.increments],
                budget=prepared.calculation.budget, revision=1)
            if before.revision == 0:
                State.objects.using(alias).create(progress=current, active_configuration=config, revision=1)
            else:
                State.objects.using(alias).filter(progress=current).update(active_configuration=config, revision=before.revision + 1)
        elif action == "switch":
            State.objects.using(alias).filter(progress=current).update(active_configuration_id=old.id, revision=before.revision + 1)
        else:
            config = Configuration.objects.using(alias).get(pk=old.id)
            config.increments = [list(p) for p in prepared.calculation.increments]
            config.revision += 1
            config.save(using=alias, update_fields=("increments", "revision", "updated_at"))
            State.objects.using(alias).filter(progress=current).update(revision=before.revision + 1)
        # Validate the candidate with the historical transition validator,
        # then read back all tables before committing the transaction.
        configs = list(before.configurations)
        if action == "configure":
            configs.append(ConfigurationSnapshot(config.pk, 1, prepared))
        elif action == "redistribute":
            configs = [ConfigurationSnapshot(c.id, c.revision + 1, prepared) if c.id == old.id else c for c in configs]
        after = PlayableSnapshot(current.pk, current.catalog_id, before.revision + 1,
            before.active_option if action == "redistribute" else option_code,
            tuple(sorted(configs, key=lambda c: c.prepared.definition.option_code)))
        event = Event(progress=current, operation_key=key, action=action, option_code=option_code,
            original_request=request, before=_encode(before), after=_encode(after))
        _validate_event(event, before, current)
        event.save(using=alias, force_insert=True)
        observed, _ = _read(current, alias)
        if observed != after:
            raise xp.DemoIntegrityError("Confirmación jugable contradictoria.")
        return PlayableResult(event.pk, action, option_code, before, after)


def configure_demo_option(progress, *, option_code, increments, operation_token, session_token, expected_revision=None):
    return _operate(progress, action="configure", option_code=option_code, increments=increments,
        operation_token=operation_token, session_token=session_token, expected_revision=expected_revision)


def switch_demo_option(progress, *, option_code, expected_revision, operation_token, session_token):
    return _operate(progress, action="switch", option_code=option_code, expected_revision=expected_revision,
        operation_token=operation_token, session_token=session_token)


def redistribute_demo_option(progress, *, option_code, increments, expected_revision, configuration_revision,
                             operation_token, session_token):
    return _operate(progress, action="redistribute", option_code=option_code, increments=increments,
        expected_revision=expected_revision, configuration_revision=configuration_revision,
        operation_token=operation_token, session_token=session_token)


def read_demo_playable(progress, *, session_token):
    with _scope(progress, session_token) as (current, alias, owner):
        return _read(current, alias)
