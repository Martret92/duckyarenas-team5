"""Closed, synthetic F1-A facts/rules. No emitter authentication or real awards."""

from dataclasses import dataclass
from types import MappingProxyType

from apps.ecomotor.reward_types import (RewardIdentity, ValidatedRewardFact,
    RewardRule, RewardRuleSet, ProposedEffect)

ORIGIN = "persist-demo-rewards"
FACT_VERSION = "demo-fact-v1"
FINGERPRINT_VERSION = "rewards-semantic-v1"
ACTIVITIES = (("challenge", "Desafío ficticio completado (+700 XP)"),
              ("visit", "Visita ficticia al archivo (NO_REWARD)"))
# Forms explicitly add coins to this historical surface; ITEM stays internal.
INTERNAL_ACTIVITIES = tuple(code for code, _ in ACTIVITIES) + ("coin_challenge", "item_challenge", "combo_challenge")
RULE_SET = RewardRuleSet("demo-rewards-rules-v2", (
    RewardRule("demo-challenge-700-v1", "challenge", {"completed": True}, (ProposedEffect("XP", 700),)),
    RewardRule("demo-coin-challenge-5-v2", "coin_challenge", {"completed": True}, (ProposedEffect("DUCKYCOINS", 5),)),
))


@dataclass(frozen=True, slots=True)
class DemoItemMapping:
    mapping_version: str
    item_code: str
    category: str = "HINT"
    consumable: bool = True
    quantity: int = 1
    item_level: None = None


# Historical definitions never follow the mutable selection for new rewards.
ITEM_MAPPINGS = MappingProxyType({"demo-item-map-v1": DemoItemMapping(
    "demo-item-map-v1", "demo-reward-hint-v1")})
ITEM_MAPPING = ITEM_MAPPINGS["demo-item-map-v1"]
ITEM_RULE_SET = RewardRuleSet("demo-rewards-rules-v3", (
    RewardRule("demo-item-challenge-hint-v3", "item_challenge", {"completed": True}, (ProposedEffect("ITEM", 1),)),
))
COMBO_RULE_SET = RewardRuleSet("demo-rewards-rules-v4", (
    RewardRule("demo-combo-challenge-v4", "combo_challenge", {"completed": True}, (
        ProposedEffect("XP", 700), ProposedEffect("DUCKYCOINS", 5), ProposedEffect("ITEM", 1))),
))


def fact_version(activity):
    if activity == "combo_challenge":
        return "demo-fact-v4"
    if activity == "item_challenge":
        return "demo-fact-v3"
    return "demo-fact-v2" if activity == "coin_challenge" else FACT_VERSION


def synthetic_fact(progress_id, fact_id, occurred_at, activity):
    if type(activity) is not str or activity not in INTERNAL_ACTIVITIES:
        raise ValueError("Actividad ficticia no admitida.")
    if activity == "combo_challenge":
        # Historical V4-01 definition, independent of rules/selection for new grants.
        return ValidatedRewardFact(RewardIdentity(ORIGIN, fact_id, f"demo-progress:{progress_id}"),
            activity, occurred_at, {"completed": True}, {"demo": "REW-MULTI-03",
                "fact_version": "demo-fact-v4", "mapping_version": "demo-item-map-v1",
                "item_code": "demo-reward-hint-v1"})
    if activity == "item_challenge":
        mapping = ITEM_MAPPINGS["demo-item-map-v1"]
        return ValidatedRewardFact(RewardIdentity(ORIGIN, fact_id, f"demo-progress:{progress_id}"),
            activity, occurred_at, {"completed": True}, {"demo": "REW-MULTI-02",
                "fact_version": "demo-fact-v3", "mapping_version": mapping.mapping_version,
                "item_code": mapping.item_code})
    return ValidatedRewardFact(
        RewardIdentity(ORIGIN, fact_id, f"demo-progress:{progress_id}"), activity, occurred_at,
        {"completed": True} if activity in ("challenge", "coin_challenge") else {"visited": True},
        {"demo": "REW-MULTI-01", "fact_version": "demo-fact-v2"} if activity == "coin_challenge"
        else {"demo": "DEMO-REWARDS-XP-01", "fact_version": FACT_VERSION})
