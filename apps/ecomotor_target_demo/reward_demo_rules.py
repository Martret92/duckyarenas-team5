"""Closed, synthetic F1-A facts/rules. No emitter authentication or real awards."""

from apps.ecomotor.reward_types import (RewardIdentity, ValidatedRewardFact,
    RewardRule, RewardRuleSet, ProposedEffect)

ORIGIN = "persist-demo-rewards"
FACT_VERSION = "demo-fact-v1"
FINGERPRINT_VERSION = "rewards-semantic-v1"
ACTIVITIES = (("challenge", "Desafío ficticio completado (+700 XP)"),
              ("visit", "Visita ficticia al archivo (NO_REWARD)"))
RULE_SET = RewardRuleSet("demo-rewards-rules-v1", (
    RewardRule("demo-challenge-700-v1", "challenge", {"completed": True}, (ProposedEffect("XP", 700),)),
))


def synthetic_fact(progress_id, fact_id, occurred_at, activity):
    if type(activity) is not str or activity not in dict(ACTIVITIES):
        raise ValueError("Actividad ficticia no admitida.")
    return ValidatedRewardFact(
        RewardIdentity(ORIGIN, fact_id, f"demo-progress:{progress_id}"), activity, occurred_at,
        {"completed": True} if activity == "challenge" else {"visited": True},
        {"demo": "DEMO-REWARDS-XP-01", "fact_version": FACT_VERSION})
