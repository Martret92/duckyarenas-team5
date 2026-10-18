"""Evaluación mínima; devuelve propuestas, nunca concede ni confirma efectos."""

from .reward_types import (
    AmbiguousRewardRulesError, InvalidRewardRuleSetError, RewardDecision,
    RewardRuleSet, ValidatedRewardFact, _checked_fact,
)


def evaluate_reward(fact: ValidatedRewardFact, rule_set: RewardRuleSet) -> RewardDecision:
    fact = _checked_fact(fact)
    if type(rule_set) is not RewardRuleSet:
        raise InvalidRewardRuleSetError("Se requiere un conjunto versionado explícito.")
    rule_set = RewardRuleSet(rule_set.version, rule_set.rules)
    matched = [rule for rule in rule_set.rules if rule.activity_type == fact.activity_type and all(
        key in fact.result and type(fact.result[key]) is type(expected) and fact.result[key] == expected
        for key, expected in rule.result_equals.items()
    )]
    if len(matched) > 1:
        raise AmbiguousRewardRulesError("Más de una regla coincide con el hecho.")
    if not matched:
        return RewardDecision(rule_set.version, None, False, (), ("NO_MATCHING_RULE",))
    rule = matched[0]
    return RewardDecision(rule_set.version, rule.rule_id, True, rule.proposed_effects,
                          () if rule.proposed_effects else ("MATCHED_NO_EFFECT",))
