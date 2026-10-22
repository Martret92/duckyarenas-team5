"""Synthetic Rewards coordinator; one owned IMMEDIATE transaction, no F2-A API."""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from secrets import compare_digest, token_hex

from django.core import signing
from django.utils.timezone import now

from apps.ecomotor.reward_identity import semantic_fingerprint
from apps.ecomotor.reward_rules import evaluate_reward
from apps.ecomotor.reward_types import RewardIdentity, RewardDecision, ProposedEffect, InvalidRewardRuleSetError
from apps.ecomotor.target_progression import TargetProgressionResult, calculate_target_progression

from . import services as xp, reward_demo_rules as rules
from .catalog import exact_catalog
from .models import DemoTargetRewardEvent as Reward, DemoTargetXPEvent as XPEvent, DemoTargetEvolutionEvent as Evolution

SALT = "ecomotor.persistent-demo.reward-fact.v1"
SNAPSHOT_VERSION = "demo-reward-result-v1"


class DemoRewardConfigurationError(ValueError):
    """Rule/effect outside this pilot; never NO_REWARD."""


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
    if type(value) is not str or value not in dict(rules.ACTIVITIES):
        raise xp.DemoInputError("Actividad ficticia inválida.")


def issue_reward_fact(progress, *, activity, session_token):
    _activity(activity)
    with xp._xp_transaction(progress, session_token=session_token) as context:
        return signing.dumps({"progress": context.progress_id, "owner": context.owner,
            "activity": activity, "fact_id": token_hex(16), "fact_version": rules.FACT_VERSION,
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
                or value["activity"] != activity or value["fact_version"] != rules.FACT_VERSION
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


def _decision(value):
    if type(value) is not RewardDecision:
        raise DemoRewardConfigurationError("Se requiere propuesta F1-A válida.")
    checked = RewardDecision(value.rule_set_version, value.matched_rule_id, value.eligible,
                             value.proposed_effects, value.reason_codes)
    if (len(checked.rule_set_version) > 64 or (checked.matched_rule_id is not None and len(checked.matched_rule_id) > 64)
            or (checked.proposed_effects and (len(checked.proposed_effects) != 1 or checked.proposed_effects[0].effect_type != "XP"))):
        raise DemoRewardConfigurationError("Este piloto solo admite un efecto XP positivo o ausencia de efectos.")
    if checked.proposed_effects:
        xp._integer(checked.proposed_effects[0].quantity, positive=True)
    return checked


def _snapshot(result, current, *, anchor):
    return {"schema": SNAPSHOT_VERSION,
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
                or type(row.snapshot) is not dict or row.snapshot.get("schema") != SNAPSHOT_VERSION):
            raise xp.DemoIntegrityError("Identidad Rewards histórica incoherente.")
        fact = rules.synthetic_fact(current.pk, row.fact_id, row.occurred_at, row.activity_type)
        if semantic_fingerprint(fact) != row.fingerprint:
            raise xp.DemoIntegrityError("Huella Rewards histórica incoherente.")
        snap = row.snapshot
        effects = snap.get("effects")
        if type(effects) is not list or any(type(e) is not list or len(e) != 2 for e in effects):
            raise xp.DemoIntegrityError("Propuesta histórica incompleta.")
        if type(row.reason_codes) is not list:
            raise xp.DemoIntegrityError("Motivos históricos inválidos.")
        decision = _decision(RewardDecision(row.rule_set_version, row.matched_rule_id, snap.get("eligible"),
            tuple(ProposedEffect(*e) for e in effects), tuple(row.reason_codes)))
        amount = decision.proposed_effects[0].quantity if decision.proposed_effects else 0
        if type(row.xp_amount) is not int or row.xp_amount != amount:
            raise xp.DemoIntegrityError("Importe Rewards contradictorio.")
        if row.status == "APPLIED" and amount > 0 and row.xp_event_id is not None:
            event = next((e for e in events if e.pk == row.xp_event_id), None)
            if event is None or event.operation_key != _xp_key(fact.identity) or event.amount != amount:
                raise xp.DemoIntegrityError("Causa XP Rewards ausente o incompatible.")
            grant = xp._historical(event, current, alias, replay=True)
            progression = grant.progression
            causal = tuple(Evolution.objects.using(alias).filter(xp_event=event).order_by("ordinal").values_list("id", flat=True))
            anchor = event.pk
        elif row.status == "NO_REWARD" and amount == 0 and row.xp_event_id is None:
            anchor = snap.get("anchor_xp_event_id")
            progression = _stationary(current, events, anchor)
            causal = ()
        else:
            raise xp.DemoIntegrityError("Estado Rewards incompatible con sus efectos.")
        result = DemoRewardResult(row.pk, fact.identity, fact.activity_type, fact.occurred_at,
            row.status, row.fingerprint_version, row.fingerprint, decision, amount, row.xp_event_id, causal, progression)
        if _json(snap) != _json(_snapshot(result, current, anchor=anchor)):
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
    return results


def apply_demo_reward(progress, *, activity, fact_token, session_token):
    if type(progress) is not xp.DemoTargetProgress or progress.pk is None:
        raise xp.DemoInputError("Se requiere una partida persistida.")
    fact = _fact(fact_token, progress, xp._owner(session_token), activity)
    fingerprint = semantic_fingerprint(fact)
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
        amount = decision.proposed_effects[0].quantity if decision.proposed_effects else 0
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
        result = DemoRewardResult(0, fact.identity, fact.activity_type, fact.occurred_at,
            "APPLIED" if amount else "NO_REWARD", rules.FINGERPRINT_VERSION, fingerprint,
            decision, amount, xp_id, causal, observation)
        row = Reward.objects.using(alias).create(progress=current, origin_code=fact.identity.origin_code,
            fact_id=fact.identity.fact_id, recipient_id=fact.identity.recipient_id, activity_type=fact.activity_type,
            occurred_at=fact.occurred_at, fingerprint_version=rules.FINGERPRINT_VERSION, fingerprint=fingerprint,
            rule_set_version=decision.rule_set_version, matched_rule_id=decision.matched_rule_id,
            status=result.status, reason_codes=list(decision.reason_codes), xp_amount=amount, xp_event_id=xp_id,
            snapshot=_snapshot(result, current, anchor=anchor))
        # Includes the new row and actual causal tables; any failure rolls back XP too.
        observed = next(r for r in _history(current, alias) if r.event_id == row.pk)
        return observed


def read_demo_rewards(progress, *, session_token):
    with xp._xp_transaction(progress, session_token=session_token) as context:
        current, alias = xp._check_xp_transaction(context)
        return _history(current, alias)
