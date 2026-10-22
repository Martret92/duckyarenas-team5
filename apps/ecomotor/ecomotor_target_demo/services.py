"""Local fictitious grants; not the productive A2 writer or Core authorization."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
import re
from secrets import compare_digest, token_hex

from django.core import signing
from django.db import DatabaseError, IntegrityError, OperationalError, connections, transaction

from apps.ecomotor.models import TargetCatalogVersion, TargetEpoch
from apps.ecomotor.target_progression import TargetProgressionResult, calculate_target_progression
from apps.ecomotor.target_xp_plan import plan_target_xp_grant

from .catalog import DemoCatalogError, exact_catalog
from .data import CATALOG_ID, VERSION, MAX_XP
from .isolation import demo_connection
from .models import DemoTargetProgress, DemoTargetXPEvent, DemoTargetEvolutionEvent

SALT = "ecomotor.persistent-demo.operation.v1"


class DemoInputError(ValueError): pass
class DemoAccessError(ValueError): pass
class DemoConflictError(ValueError): pass
class DemoIntegrityError(ValueError): pass
class DemoTransactionError(RuntimeError): pass
class DemoDatabaseError(RuntimeError): pass
class DemoBusyError(DemoDatabaseError): pass


@dataclass(frozen=True, slots=True)
class DemoGrantResult:
    event_id: int
    progress_id: int
    amount: int
    progression: TargetProgressionResult
    replay: bool


def _owner(secret):
    if type(secret) is not str or re.fullmatch("[0-9a-f]{64}", secret) is None:
        raise DemoAccessError("Contexto de sesión ficticia inválido.")
    return sha256(secret.encode("ascii")).hexdigest()


def _integer(value, *, positive=False):
    if type(value) is not int or not (1 if positive else 0) <= value <= MAX_XP:
        raise DemoInputError("Se requiere un entero exacto representable en SQLite.")


def _connection():
    db = demo_connection()
    if (db.in_atomic_block or not db.get_autocommit() or db.connection.in_transaction
            or db.transaction_mode != "IMMEDIATE"):
        raise DemoTransactionError("Se requiere una transacción exterior SQLite IMMEDIATE propia.")
    return db


def _progress(pk, owner, alias):
    _integer(pk, positive=True)
    try:
        progress = DemoTargetProgress.objects.using(alias).get(pk=pk)
    except DemoTargetProgress.DoesNotExist as error:
        raise DemoAccessError("Partida no disponible para esta sesión.") from error
    if not compare_digest(progress.session_owner, owner):
        raise DemoAccessError("Partida no disponible para esta sesión.")
    return progress


def create_demo_progress(*, session_token):
    owner = _owner(session_token)
    db = _connection()
    with transaction.atomic(using=db.alias):
        version = TargetCatalogVersion.objects.using(db.alias).get(catalog_id=CATALOG_ID, version=VERSION)
        _, snapshot = exact_catalog(version.pk, db.alias)
        initial = calculate_target_progression(0, 0, snapshot)
        epoch = TargetEpoch.objects.using(db.alias).get(catalog=version, code=initial.epoch_after_code)
        return DemoTargetProgress.objects.using(db.alias).create(
            session_owner=owner, catalog=version, current_epoch=epoch,
            xp_total=initial.xp_after, current_level=initial.level_after)


def issue_demo_operation(progress, *, session_token):
    owner = _owner(session_token)
    db = _connection()
    with transaction.atomic(using=db.alias):
        current = _progress(progress.pk, owner, db.alias)
        return signing.dumps({"progress": current.pk, "owner": owner, "key": token_hex(16)}, salt=SALT)


def _key(token, pk, owner):
    if type(token) is not str or len(token) > 1024:
        raise DemoInputError("Identidad de formulario inválida.")
    try:
        value = signing.loads(token, salt=SALT)
    except signing.BadSignature as error:
        raise DemoAccessError("Identidad de operación no acreditada por el servidor.") from error
    if (type(value) is not dict or set(value) != {"progress", "owner", "key"}
            or type(value["progress"]) is not int or value["progress"] != pk
            or type(value["owner"]) is not str or not compare_digest(value["owner"], owner)
            or type(value["key"]) is not str or re.fullmatch("[0-9a-f]{32}", value["key"]) is None):
        raise DemoAccessError("Operación de otra partida o sesión.")
    return value["key"]


def _historical(event, current, alias, *, replay):
    """Recover recorded facts, never recalculate thresholds from today's catalog."""
    try:
        for value in (event.amount, event.xp_before, event.xp_after): _integer(value)
    except DemoInputError as error:
        raise DemoIntegrityError("Importes históricos no representables.") from error
    before, after = event.epoch_before, event.epoch_after
    levels, codes = event.crossed_levels, event.crossed_epoch_codes
    causal = tuple(DemoTargetEvolutionEvent.objects.using(alias).filter(xp_event=event)
                   .select_related("epoch").order_by("ordinal"))
    if (event.amount <= 0 or event.xp_after != event.xp_before + event.amount
            or event.progress_id != current.pk or event.catalog_id != current.catalog_id
            or before.catalog_id != event.catalog_id or after.catalog_id != event.catalog_id
            or type(levels) is not list or type(codes) is not list
            or any(type(n) is not int for n in levels)
            or type(event.level_before) is not int or type(event.level_after) is not int
            or not 1 <= event.level_before <= event.level_after <= 2**31-1
            or len(levels) != event.level_after - event.level_before
            or any(n != event.level_before + i + 1 for i, n in enumerate(levels))
            or not 1 <= before.ordinal <= after.ordinal <= 7
            or any(type(c) is not str for c in codes) or len(set(codes)) != len(codes)
            or tuple(codes) != tuple(e.epoch.code for e in causal)
            or tuple(e.ordinal for e in causal) != tuple(range(before.ordinal + 1, after.ordinal + 1))
            or any(e.progress_id != current.pk or e.catalog_id != event.catalog_id
                   or e.epoch.catalog_id != event.catalog_id or e.ordinal != e.epoch.ordinal for e in causal)
            or current.xp_total < event.xp_after):
        raise DemoIntegrityError("Historial sintético incoherente; no se repara ni recalcula.")
    return DemoGrantResult(event.pk, current.pk, event.amount, TargetProgressionResult(
        catalog_version=event.catalog.version, xp_before=event.xp_before, xp_after=event.xp_after,
        level_before=event.level_before, level_after=event.level_after,
        epoch_before_code=before.code, epoch_after_code=after.code,
        crossed_levels=tuple(levels), crossed_epoch_codes=tuple(codes),
        choice_unlocked_before=event.level_before >= 8, choice_unlocked_after=event.level_after >= 8,
        choice_newly_unlocked=event.level_before < 8 <= event.level_after), replay)


def _history(current, alias):
    events = tuple(DemoTargetXPEvent.objects.using(alias).filter(progress=current)
                   .select_related("epoch_before", "epoch_after", "catalog").order_by("xp_before", "id"))
    evolutions = tuple(DemoTargetEvolutionEvent.objects.using(alias).filter(progress=current)
                      .select_related("epoch", "xp_event").order_by("ordinal"))
    own_ids = {event.pk for event in events}
    if any(e.xp_event_id not in own_ids for e in evolutions):
        raise DemoIntegrityError("Referencia causal ajena o ausente en la partida.")
    xp, level, epoch_id = 0, 1, None
    for event in events:
        _historical(event, current, alias, replay=True)
        if (event.xp_before != xp or event.level_before != level
                or (epoch_id is not None and event.epoch_before_id != epoch_id)
                or (epoch_id is None and event.epoch_before.ordinal != 1)):
            raise DemoIntegrityError("Cadena de snapshots ficticios incompatible.")
        xp, level, epoch_id = event.xp_after, event.level_after, event.epoch_after_id
    if (current.current_epoch.catalog_id != current.catalog_id
            or current.xp_total != xp or current.current_level != level
            or (epoch_id is not None and current.current_epoch_id != epoch_id)
            or (epoch_id is None and current.current_epoch.ordinal != 1)):
        raise DemoIntegrityError("Progreso y registro ficticio no coinciden.")
    return events, evolutions


@dataclass(frozen=True, slots=True)
class _XPTransaction:
    db: object
    connection: object
    boundary: object
    progress_id: int
    owner: str


_active_xp_transaction = ContextVar("demo_owned_xp_transaction", default=None)


def _check_xp_transaction(context):
    if type(context) is not _XPTransaction or _active_xp_transaction.get() is not context:
        raise DemoTransactionError("Núcleo XP sin contexto transaccional controlado.")
    db = context.db
    if (connections[db.alias] is not db or not db.in_atomic_block or db.get_autocommit() or db.transaction_mode != "IMMEDIATE"
            or db.connection is not context.connection or not db.connection.in_transaction
            or len(db.atomic_blocks) != 1 or db.atomic_blocks[0] is not context.boundary):
        raise DemoTransactionError("Frontera XP incompatible o finalizada.")
    return _progress(context.progress_id, context.owner, db.alias), db.alias


@contextmanager
def _xp_transaction(progress, *, session_token):
    """Private owner of one outer IMMEDIATE boundary, shared only by this demo."""
    if type(progress) is not DemoTargetProgress or progress.pk is None or progress._state.adding:
        raise DemoInputError("Se requiere una partida ficticia persistida.")
    owner = _owner(session_token)
    try:
        db = _connection()
        if progress._state.db != db.alias:
            raise DemoAccessError("La partida pertenece a otra base.")
        with transaction.atomic(using=db.alias):
            current = _progress(progress.pk, owner, db.alias)
            context = _XPTransaction(db, db.connection, db.atomic_blocks[0], current.pk, owner)
            token = _active_xp_transaction.set(context)
            try:
                yield context
            finally:
                _active_xp_transaction.reset(token)
    except IntegrityError as error:
        raise DemoIntegrityError("Restricción de integridad de la demo; operación revertida.") from error
    except OperationalError as error:
        code = getattr(error.__cause__, "sqlite_errorcode", 0) & 255
        if code in (5, 6):
            raise DemoBusyError("SQLite ocupada; sin concesión parcial. Reintenta el mismo formulario.") from error
        raise DemoDatabaseError("Fallo operativo SQLite; operación no confirmada.") from error
    except DatabaseError as error:
        raise DemoDatabaseError("Fallo de base de datos; operación no confirmada.") from error


def _grant_xp_in_transaction(context, *, amount, operation_key):
    """No begin/commit. Requires the exact live context issued by our owner above."""
    current, alias = _check_xp_transaction(context)
    _integer(amount, positive=True)
    if type(operation_key) is not str or re.fullmatch(r"(?:[0-9a-f]{32}|rx1:[0-9a-f]{28})", operation_key) is None:
        raise DemoInputError("Clave causal XP incompatible.")
    key = operation_key
    event = DemoTargetXPEvent.objects.using(alias).filter(progress=current, operation_key=key).first()
    if event is not None:
        if event.amount != amount:
            raise DemoConflictError("La identidad ya corresponde a otro importe.")
        return _historical(event, current, alias, replay=True)
    _, snapshot = exact_catalog(current.catalog_id, alias)
    _integer(current.xp_total)
    if current.xp_total > MAX_XP - amount:
        raise DemoInputError("El total excedería el entero SQLite de 64 bits.")
    actual = calculate_target_progression(current.xp_total, current.xp_total, snapshot)
    if (current.current_level != actual.level_after
            or current.current_epoch.catalog_id != current.catalog_id
            or current.current_epoch.code != actual.epoch_after_code):
        raise DemoIntegrityError("Progreso incoherente con su catálogo congelado.")
    _history(current, alias)
    plan = plan_target_xp_grant(current.xp_total, amount, snapshot)
    p = plan.progression
    epochs = {e.code: e for e in TargetEpoch.objects.using(alias).filter(catalog_id=current.catalog_id)}
    event = DemoTargetXPEvent.objects.using(alias).create(
        progress=current, operation_key=key, amount=amount, xp_before=p.xp_before, xp_after=p.xp_after,
        level_before=p.level_before, level_after=p.level_after,
        epoch_before=epochs[p.epoch_before_code], epoch_after=epochs[p.epoch_after_code],
        catalog_id=current.catalog_id, crossed_levels=list(p.crossed_levels),
        crossed_epoch_codes=list(p.crossed_epoch_codes))
    for code in p.crossed_epoch_codes:
        epoch = epochs[code]
        DemoTargetEvolutionEvent.objects.using(alias).create(
            progress=current, xp_event=event, epoch=epoch, ordinal=epoch.ordinal, catalog_id=current.catalog_id)
    current.xp_total, current.current_level, current.current_epoch = p.xp_after, p.level_after, epochs[p.epoch_after_code]
    current.save(using=alias, update_fields=["xp_total", "current_level", "current_epoch"])
    return _historical(event, current, alias, replay=False)


def grant_demo_target_xp(progress, *, amount, operation_token, session_token):
    """Unchanged public XP-token interface and historical replay semantics."""
    if type(progress) is not DemoTargetProgress or progress.pk is None or progress._state.adding:
        raise DemoInputError("Se requiere una partida ficticia persistida.")
    _integer(amount, positive=True)
    owner = _owner(session_token)
    key = _key(operation_token, progress.pk, owner)
    with _xp_transaction(progress, session_token=session_token) as context:
        return _grant_xp_in_transaction(context, amount=amount, operation_key=key)


def read_demo_progress(pk, *, session_token):
    owner = _owner(session_token)
    db = _connection()
    with transaction.atomic(using=db.alias):
        progress = _progress(pk, owner, db.alias)
        xp_events, evolutions = _history(progress, db.alias)
        # Materialize the current epoch too, before leaving the observation.
        progress.current_epoch
        return progress, xp_events, evolutions
