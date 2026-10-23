"""Closed, synthetic F1-A facts/rules. No emitter authentication or real awards."""

from apps.ecomotor.reward_types import (RewardIdentity, ValidatedRewardFact,
    RewardRule, RewardRuleSet, ProposedEffect)

ORIGIN = "persist-demo-rewards"
FACT_VERSION = "demo-fact-v1"
FINGERPRINT_VERSION = "rewards-semantic-v1"
ACTIVITIES = (("challenge", "Desafío ficticio completado (+700 XP)"),
              ("visit", "Visita ficticia al archivo (NO_REWARD)"))
# ACTIVITIES is the existing HTTP surface; the monetary pilot is internal only.
INTERNAL_ACTIVITIES = tuple(code for code, _ in ACTIVITIES) + ("coin_challenge",)
RULE_SET = RewardRuleSet("demo-rewards-rules-v2", (
    RewardRule("demo-challenge-700-v1", "challenge", {"completed": True}, (ProposedEffect("XP", 700),)),
    RewardRule("demo-coin-challenge-5-v2", "coin_challenge", {"completed": True}, (ProposedEffect("DUCKYCOINS", 5),)),
))


def fact_version(activity):
    return "demo-fact-v2" if activity == "coin_challenge" else FACT_VERSION


def synthetic_fact(progress_id, fact_id, occurred_at, activity):
    if type(activity) is not str or activity not in INTERNAL_ACTIVITIES:
        raise ValueError("Actividad ficticia no admitida.")
    return ValidatedRewardFact(
        RewardIdentity(ORIGIN, fact_id, f"demo-progress:{progress_id}"), activity, occurred_at,
        {"completed": True} if activity in ("challenge", "coin_challenge") else {"visited": True},
        {"demo": "REW-MULTI-01", "fact_version": "demo-fact-v2"} if activity == "coin_challenge"
        else {"demo": "DEMO-REWARDS-XP-01", "fact_version": FACT_VERSION})
