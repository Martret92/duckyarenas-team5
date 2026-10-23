"""Synthetic Rewards coordinator; one owned IMMEDIATE transaction, no F2-A API."""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from secrets import compare_digest, token_hex

from django.core import signing
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from apps.bank import services as bank_service
from apps.bank.models import Wallet, Transaction

from apps.ecomotor.reward_identity import semantic_fingerprint
from apps.ecomotor.reward_rules import evaluate_reward
from apps.ecomotor.reward_types import RewardIdentity, RewardDecision, ProposedEffect, InvalidRewardRuleSetError
from apps.ecomotor.target_progression import TargetProgressionResult, calculate_target_progression

from . import services as xp, reward_demo_rules as rules
from .catalog import exact_catalog
from .models import DemoTargetRewardEvent as Reward, DemoTargetXPEvent as XPEvent, DemoTargetEvolutionEvent as Evolution

SALT = "ecomotor.persistent-demo.reward-fact.v1"
V1_SNAPSHOT_VERSION = "demo-reward-result-v1"
SNAPSHOT_VERSION = "demo-reward-result-v2"


class DemoRewardConfigurationError(ValueError):
    """Rule/effect outside this pilot; never NO_REWARD."""


@dataclass(frozen=True, slots=True)
class DemoBankSnapshot:
    user_id: int
    wallet_id: int
    transaction_id: int
    operation_key: str
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    source_platform: str
    issuing_entity: str
    reference_type: str
    reference_id: str
    request_fingerprint: str
    created_at: str


@dataclass(frozen=True, slots=True)
class DemoRewardResult:
    event_id: int
    identity: RewardIdentity
    activity_type: str
    occurred_at: datetime
    status: str
    fingerprint_version: str
    fingerprint: str
    decision: RewardDecision
    xp_amount: int
    xp_event_id: int | None
    evolution_ids: tuple[int, ...]
    progression: TargetProgressionResult
    replay: bool = False
    coin_amount: int = 0
    bank: DemoBankSnapshot | None = None


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _instant(value):
    if type(value) is not str or len(value) > 32:
        raise xp.DemoInputError("Instante original del hecho inválido.")
    try:
        result = datetime.fromisoformat(value)
        if result.utcoffset() is None or result.isoformat(timespec="microseconds") != value:
            raise ValueError
        if result.utcoffset().total_seconds() != 0:
            raise ValueError
        return result
    except (ValueError, OverflowError):
        raise xp.DemoInputError("Instante original del hecho inválido.") from None


def _activity(value):
    if type(value) is not str or value not in rules.INTERNAL_ACTIVITIES:
        raise xp.DemoInputError("Actividad ficticia inválida.")


def issue_reward_fact(progress, *, activity, session_token):
    _activity(activity)
    with xp._xp_transaction(progress, session_token=session_token) as context:
        return signing.dumps({"progress": context.progress_id, "owner": context.owner,
            "activity": activity, "fact_id": token_hex(16), "fact_version": rules.fact_version(activity),
            "occurred_at": now().astimezone(timezone.utc).isoformat(timespec="microseconds")}, salt=SALT)


def _fact(token, progress, owner, activity):
    _activity(activity)
    try:
        if type(token) is not str or len(token) > 1536:
            raise signing.BadSignature
        value = signing.loads(token, salt=SALT)
        if (type(value) is not dict or set(value) != {"progress", "owner", "activity", "fact_id", "fact_version", "occurred_at"}
                or type(value["progress"]) is not int or value["progress"] != progress.pk
                or type(value["owner"]) is not str or not compare_digest(value["owner"], owner)
                or value["activity"] != activity or value["fact_version"] != rules.fact_version(activity)
                or type(value["fact_id"]) is not str or re.fullmatch("[0-9a-f]{32}", value["fact_id"]) is None):
            raise signing.BadSignature
        instant = _instant(value["occurred_at"])
        return rules.synthetic_fact(progress.pk, value["fact_id"], instant, activity)
    except signing.BadSignature:
        raise xp.DemoAccessError("Hecho no disponible para esta sesión, partida y actividad.") from None


def _xp_key(identity):
    # Versioned, unambiguous logical identity, NEVER the semantic fingerprint.
    encoded = _json(["demo-reward-xp-key-v1", identity.origin_code, identity.fact_id, identity.recipient_id])
    return "rx1:" + sha256(encoded.encode("utf-8")).hexdigest()[:28]


def _bank_key(identity):
    encoded = _json(["demo-reward-bank-key-v1", identity.origin_code, identity.fact_id, identity.recipient_id])
    return "rb1:" + sha256(encoded.encode("utf-8")).hexdigest()


def _bank_default(alias):
    if alias != "default":
        raise xp.DemoTransactionError("El piloto monetario requiere el default protegido de la demo.")


def _wallet(current, alias, *, provision=False):
    _bank_default(alias)
    User = get_user_model()
    if current.synthetic_user_id is None:
        if not provision:
            raise xp.DemoIntegrityError("Causa monetaria sin usuario sintético.")
        user = User(username="rew-demo-" + token_hex(16), is_active=False,
                    is_staff=False, is_superuser=False, email="", first_name="", last_name="")
        user.set_unusable_password()
        user.save(using=alias)
        wallet = Wallet.objects.using(alias).create(user=user, available_balance=0)
        current.synthetic_user = user
        current.save(using=alias, update_fields=["synthetic_user"])
        return user, wallet
    try:
        user = User.objects.using(alias).get(pk=current.synthetic_user_id)
        wallet = Wallet.objects.using(alias).get(user_id=user.pk)
    except (User.DoesNotExist, Wallet.DoesNotExist) as error:
        raise xp.DemoIntegrityError("Vinculación sintética incompleta; no se repara.") from error
    if (re.fullmatch(r"rew-demo-[0-9a-f]{32}", user.username) is None
            or user.is_active or user.is_staff or user.is_superuser or user.has_usable_password()
            or user.email or user.first_name or user.last_name
            or type(wallet.available_balance) is not int or not 0 <= wallet.available_balance <= bank_service.MAX_BALANCE
            or user.groups.using(alias).exists() or user.user_permissions.using(alias).exists()
            or xp.DemoTargetProgress.objects.using(alias).filter(synthetic_user_id=user.pk).exclude(pk=current.pk).exists()):
        raise xp.DemoIntegrityError("Usuario sintético incompatible o compartido.")
    return user, wallet


def _bank_snapshot(entry, current, identity, alias):
    """Verify real Bank rows; never equate today's balance with a past result."""
    user, wallet = _wallet(current, alias)
    key = _bank_key(identity)
    semantics = {"version": 1, "transaction_type": "REWARD", "amount": 5,
        "source": rules.ORIGIN, "issuing_entity": "EcomotorDemo",
        "reference_type": "demo_reward_fact_v1", "reference_id": key}
    # Bank's documented public encoding, not an import of its private helper.
    fingerprint = sha256(json.dumps(semantics, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()
    if (type(entry) is not Transaction or entry._state.db != alias or entry.wallet_id != wallet.pk
            or type(entry.pk) is not int or entry.pk <= 0
            or entry.operation_key != key or entry.transaction_type != "REWARD"
            or type(entry.amount) is not int or entry.amount != 5
            or type(entry.balance_after) is not int or not 5 <= entry.balance_after <= bank_service.MAX_BALANCE
            or entry.source_platform != rules.ORIGIN or entry.issuing_entity != "EcomotorDemo"
            or entry.reference_type != "demo_reward_fact_v1" or entry.reference_id != key
            or entry.request_fingerprint != fingerprint):
        raise xp.DemoIntegrityError("Causa Bank incompatible con la identidad Rewards.")
    return DemoBankSnapshot(user.pk, wallet.pk, entry.pk, key, entry.transaction_type,
        entry.amount, entry.balance_after - entry.amount, entry.balance_after,
        entry.source_platform, entry.issuing_entity, entry.reference_type, entry.reference_id,
        entry.request_fingerprint, entry.created_at.isoformat(timespec="microseconds"))


def _decision(value):
    if type(value) is not RewardDecision:
        raise DemoRewardConfigurationError("Se requiere propuesta F1-A válida.")
    checked = RewardDecision(value.rule_set_version, value.matched_rule_id, value.eligible,
                             value.proposed_effects, value.reason_codes)
    if (len(checked.rule_set_version) > 64 or (checked.matched_rule_id is not None and len(checked.matched_rule_id) > 64)
            or (checked.proposed_effects and (len(checked.proposed_effects) != 1
                or checked.proposed_effects[0].effect_type not in ("XP", "DUCKYCOINS")))):
        raise DemoRewardConfigurationError("Solo se admite un efecto XP o cinco monedas, sin combinarlos.")
    if checked.proposed_effects:
        xp._integer(checked.proposed_effects[0].quantity, positive=True)
        if checked.proposed_effects[0].effect_type == "DUCKYCOINS" and checked.proposed_effects[0].quantity != 5:
            raise DemoRewardConfigurationError("La actividad monetaria requiere exactamente cinco monedas.")
    return checked


def _snapshot(result, current, *, anchor, schema=SNAPSHOT_VERSION):
    value = {"schema": schema,
        "identity": asdict(result.identity), "activity_type": result.activity_type,
        "occurred_at": result.occurred_at.isoformat(timespec="microseconds"),
        "fingerprint_version": result.fingerprint_version, "fingerprint": result.fingerprint,
        "status": result.status, "rule_set_version": result.decision.rule_set_version,
        "matched_rule_id": result.decision.matched_rule_id, "eligible": result.decision.eligible,
        "effects": [[e.effect_type, e.quantity] for e in result.decision.proposed_effects],
        "reason_codes": list(result.decision.reason_codes), "xp_amount": result.xp_amount,
        "xp_event_id": result.xp_event_id, "evolution_ids": list(result.evolution_ids),
        "catalog": {"pk": current.catalog_id, "catalog_id": current.catalog.catalog_id, "version": current.catalog.version},
        "anchor_xp_event_id": anchor,
        "progression": json.loads(_json(asdict(result.progression)))}
    if schema == SNAPSHOT_VERSION:
        value.update(coin_amount=result.coin_amount, bank=asdict(result.bank) if result.bank is not None else None)
    return value


def _stationary(current, events, anchor):
    """Recover a NO_REWARD observation from a real XP anchor, not today's total."""
    if anchor is None:
        return TargetProgressionResult(current.catalog.version, 0, 0, 1, 1,
            _initial_epoch(current, events), _initial_epoch(current, events), (), (), False, False, False)
    if type(anchor) is not int or anchor <= 0:
        raise xp.DemoIntegrityError("Ancla histórica inválida.")
    event = next((e for e in events if e.pk == anchor), None)
    if event is None:
        raise xp.DemoIntegrityError("Ancla XP ausente o ajena.")
    p = xp._historical(event, current, current._state.db, replay=True).progression
    return TargetProgressionResult(p.catalog_version, p.xp_after, p.xp_after, p.level_after, p.level_after,
        p.epoch_after_code, p.epoch_after_code, (), (), p.choice_unlocked_after, p.choice_unlocked_after, False)


def _initial_epoch(current, events):
    # Initial epoch is an observed catalog reference, not an invented evolution.
    if events:
        return events[0].epoch_before.code
    return current.current_epoch.code


def _recorded(row, current, events, alias):
    """Cross-check JSON with stored identity, proposal, actual XP and causal rows."""
    try:
        if (row.progress_id != current.pk or row.origin_code != rules.ORIGIN
                or row.recipient_id != f"demo-progress:{current.pk}" or type(row.fact_id) is not str
                or re.fullmatch("[0-9a-f]{32}", row.fact_id) is None or row.fingerprint_version != rules.FINGERPRINT_VERSION
            or type(row.snapshot) is not dict
                or row.snapshot.get("schema") not in (V1_SNAPSHOT_VERSION, SNAPSHOT_VERSION)):
            raise xp.DemoIntegrityError("Identidad Rewards histórica incoherente.")
        fact = rules.synthetic_fact(current.pk, row.fact_id, row.occurred_at, row.activity_type)
        if semantic_fingerprint(fact) != row.fingerprint:
            raise xp.DemoIntegrityError("Huella Rewards histórica incoherente.")
        snap = row.snapshot
        schema = snap["schema"]
        effects = snap.get("effects")
        if type(effects) is not list or any(type(e) is not list or len(e) != 2 for e in effects):
            raise xp.DemoIntegrityError("Propuesta histórica incompleta.")
        if type(row.reason_codes) is not list:
            raise xp.DemoIntegrityError("Motivos históricos inválidos.")
        decision = _decision(RewardDecision(row.rule_set_version, row.matched_rule_id, snap.get("eligible"),
            tuple(ProposedEffect(*e) for e in effects), tuple(row.reason_codes)))
        effect = decision.proposed_effects[0] if decision.proposed_effects else None
        amount = effect.quantity if effect is not None and effect.effect_type == "XP" else 0
        coins = effect.quantity if effect is not None and effect.effect_type == "DUCKYCOINS" else 0
        if (type(row.xp_amount) is not int or row.xp_amount != amount
                or type(getattr(row, "coin_amount", 0)) is not int or getattr(row, "coin_amount", 0) != coins
                or (schema == V1_SNAPSHOT_VERSION and (coins or getattr(row, "bank_transaction_id", None) is not None))
                or (coins and fact.activity_type != "coin_challenge")
                or (fact.activity_type == "coin_challenge" and not coins)):
            raise xp.DemoIntegrityError("Importe Rewards contradictorio.")
        bank = None
        if row.status == "APPLIED" and amount > 0 and row.xp_event_id is not None:
            event = next((e for e in events if e.pk == row.xp_event_id), None)
            if event is None or event.operation_key != _xp_key(fact.identity) or event.amount != amount:
                raise xp.DemoIntegrityError("Causa XP Rewards ausente o incompatible.")
            grant = xp._historical(event, current, alias, replay=True)
            progression = grant.progression
            causal = tuple(Evolution.objects.using(alias).filter(xp_event=event).order_by("ordinal").values_list("id", flat=True))
            anchor = event.pk
        elif row.status == "APPLIED" and coins == 5 and row.xp_event_id is None:
            _bank_default(alias)
            try:
                entry = Transaction.objects.using(alias).get(pk=row.bank_transaction_id)
            except Transaction.DoesNotExist as error:
                raise xp.DemoIntegrityError("Causa Bank ausente.") from error
            bank = _bank_snapshot(entry, current, fact.identity, alias)
            anchor = snap.get("anchor_xp_event_id")
            progression = _stationary(current, events, anchor)
            causal = ()
        elif row.status == "NO_REWARD" and amount == 0 and coins == 0 and row.xp_event_id is None:
            anchor = snap.get("anchor_xp_event_id")
            progression = _stationary(current, events, anchor)
            causal = ()
        else:
            raise xp.DemoIntegrityError("Estado Rewards incompatible con sus efectos.")
        if not coins and getattr(row, "bank_transaction_id", None) is not None:
            raise xp.DemoIntegrityError("Causa Bank incompatible con una recompensa sin monedas.")
        result = DemoRewardResult(row.pk, fact.identity, fact.activity_type, fact.occurred_at,
            row.status, row.fingerprint_version, row.fingerprint, decision, amount, row.xp_event_id,
            causal, progression, coin_amount=coins, bank=bank)
        if _json(snap) != _json(_snapshot(result, current, anchor=anchor, schema=schema)):
            raise xp.DemoIntegrityError("Snapshot Rewards no corresponde a sus causas.")
        return result
    except (ValueError, TypeError, OverflowError) as error:
        if isinstance(error, xp.DemoIntegrityError):
            raise
        raise xp.DemoIntegrityError("Historia Rewards no representable.") from error


def _history(current, alias):
    events, _ = xp._history(current, alias)
    if Reward.objects.using(alias).filter(xp_event__progress=current).exclude(progress=current).exists():
        raise xp.DemoIntegrityError("Causa XP utilizada por una recompensa ajena.")
    rows = tuple(Reward.objects.using(alias).filter(progress=current).order_by("id"))
    results = tuple(_recorded(row, current, events, alias) for row in rows)
    causes = {result.xp_event_id for result in results if result.xp_event_id is not None}
    if {e.pk for e in events if e.operation_key.startswith("rx1:")} != causes:
        raise xp.DemoIntegrityError("XP de namespace Rewards sin recompensa coherente; no se reconstruye.")
    if getattr(current, "synthetic_user_id", None) is not None:
        _, wallet = _wallet(current, alias)
        causes = {result.bank.transaction_id for result in results if result.bank is not None}
        if (set(Transaction.objects.using(alias).filter(wallet=wallet, operation_key__startswith="rb1:")
                .values_list("pk", flat=True)) != causes
                or Reward.objects.using(alias).filter(bank_transaction__wallet=wallet).exclude(progress=current).exists()):
            raise xp.DemoIntegrityError("Movimiento Bank Rewards huérfano o causa cruzada; no se adopta.")
    return results


def apply_demo_reward(progress, *, activity, fact_token, session_token):
    if type(progress) is not xp.DemoTargetProgress or progress.pk is None:
        raise xp.DemoInputError("Se requiere una partida persistida.")
    fact = _fact(fact_token, progress, xp._owner(session_token), activity)
    fingerprint = semantic_fingerprint(fact)
    if activity == "coin_challenge":
        # Resolve the protected connection before any write. Historical XP-only
        # fixtures keep their own alias; Bank may never be routed to that alias.
        _bank_default(xp._connection().alias)
    with xp._xp_transaction(progress, session_token=session_token) as context:
        current, alias = xp._check_xp_transaction(context)
        history = _history(current, alias)
        existing = next((result for result in history if result.identity == fact.identity), None)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise xp.DemoConflictError("La identidad Rewards ya contiene otro hecho semántico.")
            return replace(existing, replay=True)
        _, catalog = exact_catalog(current.catalog_id, alias)
        observation = calculate_target_progression(current.xp_total, current.xp_total, catalog)
        if (observation.level_after != current.current_level or observation.epoch_after_code != current.current_epoch.code):
            raise xp.DemoIntegrityError("Progreso Rewards incoherente con el catálogo.")
        decision = _decision(evaluate_reward(fact, rules.RULE_SET))
        effect = decision.proposed_effects[0] if decision.proposed_effects else None
        coins = effect.quantity if effect is not None and effect.effect_type == "DUCKYCOINS" else 0
        amount = effect.quantity if effect is not None and effect.effect_type == "XP" else 0
        if (bool(coins) != (activity == "coin_challenge")):
            raise DemoRewardConfigurationError("Propuesta incompatible con la actividad sintética.")
        bank = None
        if amount:
            key = _xp_key(fact.identity)
            if XPEvent.objects.using(alias).filter(progress=current, operation_key=key).exists():
                raise xp.DemoIntegrityError("Colisión causal Rewards no recuperable automáticamente.")
            grant = xp._grant_xp_in_transaction(context, amount=amount, operation_key=key)
            current = xp._progress(current.pk, context.owner, alias)
            observation = grant.progression
            xp_id = grant.event_id
            causal = tuple(Evolution.objects.using(alias).filter(xp_event_id=xp_id).order_by("ordinal").values_list("id", flat=True))
            anchor = xp_id
        else:
            xp_id, causal = None, ()
            last = XPEvent.objects.using(alias).filter(progress=current).order_by("-xp_after").first()
            anchor = last.pk if last else None
        if coins:
            _bank_default(alias)
            key = _bank_key(fact.identity)
            if Transaction.objects.using(alias).filter(operation_key=key).exists():
                raise xp.DemoIntegrityError("Causa Bank previa sin recompensa; no se adopta.")
            user, wallet = _wallet(current, alias, provision=True)
            before_balance = wallet.available_balance
            ledger = bank_service.credit_coins(user, 5, source=rules.ORIGIN,
                issuing_entity="EcomotorDemo", operation_key=key,
                reference_type="demo_reward_fact_v1", reference_id=key)
            xp._check_xp_transaction(context)  # Bank's inner savepoint is over.
            if (type(ledger) is not bank_service.LedgerResult or ledger.created is not True
                    or type(ledger.transaction) is not Transaction):
                raise xp.DemoIntegrityError("Bank no confirmó una causa nueva inequívoca.")
            try:
                entry = Transaction.objects.using(alias).get(pk=ledger.transaction.pk)
            except Transaction.DoesNotExist as error:
                raise xp.DemoIntegrityError("Resultado Bank sin movimiento persistente.") from error
            bank = _bank_snapshot(entry, current, fact.identity, alias)
            wallet.refresh_from_db(using=alias)
            if (bank.balance_before != before_balance or bank.balance_after != wallet.available_balance
                    or ledger.transaction._state.db != alias or ledger.transaction.wallet_id != wallet.pk):
                raise xp.DemoIntegrityError("Resultado Bank no corresponde al crédito confirmado.")
        result = DemoRewardResult(0, fact.identity, fact.activity_type, fact.occurred_at,
            "APPLIED" if amount or coins else "NO_REWARD", rules.FINGERPRINT_VERSION, fingerprint,
            decision, amount, xp_id, causal, observation, coin_amount=coins, bank=bank)
        row = Reward.objects.using(alias).create(progress=current, origin_code=fact.identity.origin_code,
            fact_id=fact.identity.fact_id, recipient_id=fact.identity.recipient_id, activity_type=fact.activity_type,
            occurred_at=fact.occurred_at, fingerprint_version=rules.FINGERPRINT_VERSION, fingerprint=fingerprint,
            rule_set_version=decision.rule_set_version, matched_rule_id=decision.matched_rule_id,
            status=result.status, reason_codes=list(decision.reason_codes), xp_amount=amount, xp_event_id=xp_id,
            coin_amount=coins, bank_transaction_id=bank.transaction_id if bank is not None else None,
            snapshot=_snapshot(result, current, anchor=anchor))
        # Includes the new row and actual causal tables; any failure rolls back XP too.
        observed = next(r for r in _history(current, alias) if r.event_id == row.pk)
        return observed


def read_demo_rewards(progress, *, session_token):
    with xp._xp_transaction(progress, session_token=session_token) as context:
        current, alias = xp._check_xp_transaction(context)
        return _history(current, alias)
