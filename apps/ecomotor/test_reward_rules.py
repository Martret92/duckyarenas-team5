import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch

from .reward_identity import canonical_reward_bytes, semantic_fingerprint
from .reward_rules import evaluate_reward
from .reward_types import (
    AmbiguousRewardRulesError, InvalidRewardFactError, InvalidRewardRuleSetError,
    ProposedEffect, RewardDecision, RewardRule, RewardRuleSet,
)
from .test_reward_types import make_fact


def rule(**changes):
    return RewardRule(**(dict(rule_id="test-rule-1", activity_type="test.activity",
                             result_equals={"ok": True},
                             proposed_effects=(ProposedEffect("test-proposal", 2),)) | changes))


class RewardRuleTests(TestCase):
    def test_explicit_valid_versioned_rule_set(self):
        value = RewardRuleSet("test-rules-v1", [rule()])
        self.assertEqual(value.version, "test-rules-v1")
        self.assertIsInstance(value.rules, tuple)

    def test_missing_or_invalid_rule_set_not_decision(self):
        for value in (None, {}, [], "test"):
            with self.subTest(value=value), self.assertRaises(InvalidRewardRuleSetError):
                evaluate_reward(make_fact(), value)

    def test_invalid_versions_and_rule_ids(self):
        for value in ("", None, 1, True, "\ud800"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(InvalidRewardRuleSetError):
                    RewardRuleSet(value, ())
                with self.assertRaises(InvalidRewardRuleSetError):
                    rule(rule_id=value)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(InvalidRewardRuleSetError):
            RewardRuleSet("test-v1", (rule(), rule(result_equals={"score": 99})))

    def test_invalid_rule_collections_and_elements(self):
        for value in (None, {}, {"set"}, [object()], [None]):
            with self.subTest(value=value), self.assertRaises(InvalidRewardRuleSetError):
                RewardRuleSet("test-v1", value)

    def test_invalid_rules_and_conditions(self):
        for changes in ({"activity_type": ""}, {"result_equals": None},
                        {"result_equals": {"x": []}}, {"result_equals": {"x": {}}},
                        {"result_equals": {"x": 1.0}}, {"result_equals": {1: True}},
                        {"proposed_effects": [object()]}):
            with self.subTest(changes=changes), self.assertRaises(InvalidRewardRuleSetError):
                rule(**changes)

    def test_effect_requires_positive_integer_not_bool(self):
        for value in (0, -1, True, False, 1.0, "2", None):
            with self.subTest(value=value), self.assertRaises(InvalidRewardRuleSetError):
                ProposedEffect("test-effect", value)
        for value in ("", None, 1, "\ud800"):
            with self.assertRaises(InvalidRewardRuleSetError):
                ProposedEffect(value, 1)
        self.assertEqual(ProposedEffect("arbitrary-test-effect", 10**100).quantity, 10**100)

    def test_no_matching_rule(self):
        decision = evaluate_reward(make_fact(result={"ok": False}), RewardRuleSet("test-v1", (rule(),)))
        self.assertEqual(decision, RewardDecision("test-v1", None, False, (), ("NO_MATCHING_RULE",)))

    def test_explicit_empty_set_means_no_matching_rule(self):
        decision = evaluate_reward(make_fact(), RewardRuleSet("test-empty", ()))
        self.assertFalse(decision.eligible)
        self.assertEqual(decision.reason_codes, ("NO_MATCHING_RULE",))

    def test_exactly_one_match_copies_proposals_and_version(self):
        chosen = rule()
        decision = evaluate_reward(make_fact(), RewardRuleSet("test-original-version", (chosen,)))
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.matched_rule_id, chosen.rule_id)
        self.assertEqual(decision.proposed_effects, chosen.proposed_effects)
        self.assertEqual(decision.rule_set_version, "test-original-version")
        self.assertEqual(decision.reason_codes, ())

    def test_matching_rule_without_effects_explicit(self):
        decision = evaluate_reward(make_fact(), RewardRuleSet("test-v1", (rule(proposed_effects=()),)))
        self.assertTrue(decision.eligible)
        self.assertEqual(decision.proposed_effects, ())
        self.assertEqual(decision.reason_codes, ("MATCHED_NO_EFFECT",))

    def test_absent_field_is_not_null(self):
        rules = RewardRuleSet("test-null", (rule(result_equals={"optional": None}),))
        self.assertFalse(evaluate_reward(make_fact(result={}), rules).eligible)
        self.assertTrue(evaluate_reward(make_fact(result={"optional": None}), rules).eligible)

    def test_boolean_and_integer_equality_is_strict(self):
        for actual, expected, matches in ((True, 1, False), (1, True, False), (False, 0, False),
                                         (True, True, True), (1, 1, True), (-1, -1, True)):
            with self.subTest(actual=actual, expected=expected):
                rules = RewardRuleSet("test-strict", (rule(result_equals={"v": expected}),))
                self.assertEqual(evaluate_reward(make_fact(result={"v": actual}), rules).eligible, matches)

    def test_activity_type_must_match(self):
        rules = RewardRuleSet("test-type", (rule(activity_type="different.test"),))
        self.assertFalse(evaluate_reward(make_fact(), rules).eligible)

    def test_multiple_simple_conditions_all_required(self):
        rules = RewardRuleSet("test-and", (rule(result_equals={"ok": True, "score": 3}),))
        self.assertTrue(evaluate_reward(make_fact(), rules).eligible)
        self.assertFalse(evaluate_reward(make_fact(result={"ok": True, "score": 2}), rules).eligible)

    def test_literal_keys_not_dynamic_paths_or_expressions(self):
        rules = RewardRuleSet("test-direct", (rule(result_equals={"a.b": 2}),))
        self.assertTrue(evaluate_reward(make_fact(result={"a.b": 2}), rules).eligible)
        self.assertFalse(evaluate_reward(make_fact(result={"a": {"b": 2}}), rules).eligible)
        expression = "__import__('os').system('never-executed')"
        rules = RewardRuleSet("test-literal", (rule(result_equals={"v": expression}),))
        self.assertTrue(evaluate_reward(make_fact(result={"v": expression}), rules).eligible)

    def test_unconditional_rule_still_requires_explicit_activity(self):
        rules = RewardRuleSet("test-any", (rule(result_equals={}),))
        self.assertTrue(evaluate_reward(make_fact(result={}), rules).eligible)
        self.assertFalse(evaluate_reward(make_fact(activity_type="other.test"), rules).eligible)

    def test_ambiguous_rules_in_both_orders_never_choose_or_sum(self):
        first, second = rule(), rule(rule_id="test-rule-2", result_equals={})
        for sequence in ((first, second), (second, first)):
            with self.assertRaises(AmbiguousRewardRulesError):
                evaluate_reward(make_fact(), RewardRuleSet("test-ambiguous", sequence))

    def test_invalid_fact_not_silently_no_reward(self):
        for value in (None, {}, "untrusted-http-body"):
            with self.assertRaises(InvalidRewardFactError):
                evaluate_reward(value, RewardRuleSet("test-v1", (rule(),)))

    def test_rule_set_deep_copy_and_no_mutation_during_evaluation(self):
        conditions = {"ok": True}
        effects = [ProposedEffect("test-only", 2)]
        original = rule(result_equals=conditions, proposed_effects=effects)
        sequence = [original]
        rules = RewardRuleSet("test-v1", sequence)
        original_conditions = original.result_equals
        conditions["ok"] = False
        effects.clear()
        sequence.clear()
        decision = evaluate_reward(make_fact(), rules)
        self.assertTrue(decision.eligible)
        self.assertIs(original.result_equals, original_conditions)
        self.assertEqual(len(rules.rules), 1)
        with self.assertRaises(TypeError):
            rules.rules[0].result_equals["ok"] = False
        with self.assertRaises(FrozenInstanceError):
            rules.version = "changed"
        with self.assertRaises(FrozenInstanceError):
            rules.rules[0].rule_id = "changed"

    def test_decision_and_effects_are_frozen(self):
        decision = evaluate_reward(make_fact(), RewardRuleSet("test-v1", (rule(),)))
        with self.assertRaises(FrozenInstanceError):
            decision.eligible = False
        with self.assertRaises(FrozenInstanceError):
            decision.proposed_effects[0].quantity = 99
        with self.assertRaises(AttributeError):
            decision.proposed_effects.append(ProposedEffect("test-only", 1))

    def test_no_application_states_or_persistent_fields(self):
        self.assertEqual({f.name for f in fields(RewardDecision)},
                         {"rule_set_version", "matched_rule_id", "eligible", "proposed_effects", "reason_codes"})
        with self.assertRaises(InvalidRewardRuleSetError):
            RewardDecision("test-v1", None, False, (), ("NO_REWARD",))
        with self.assertRaises(InvalidRewardRuleSetError):
            RewardDecision("test-v1", "test-id", True, (), ("APPLIED",))

    def test_functions_do_not_perform_io_or_apply_proposals(self):
        fact = make_fact()
        rules = RewardRuleSet("test-v1", (rule(),))
        before = canonical_reward_bytes(fact)
        with patch("builtins.open", side_effect=AssertionError("disco")), \
                patch("socket.socket", side_effect=AssertionError("red")):
            decision = evaluate_reward(fact, rules)
            self.assertEqual(before, canonical_reward_bytes(fact))
            self.assertEqual(len(semantic_fingerprint(fact)), 64)
        self.assertEqual(decision.proposed_effects, (ProposedEffect("test-proposal", 2),))

    def test_core_imports_only_standard_library_and_own_pure_modules(self):
        for name in ("reward_types", "reward_identity", "reward_rules"):
            tree = ast.parse(Path(__file__).with_name(name + ".py").read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(item.name.split(".")[0] in sys.stdlib_module_names for item in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertTrue(node.level == 1 and node.module == "reward_types" or
                                    node.level == 0 and node.module.split(".")[0] in sys.stdlib_module_names)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ("now", "today", "save", "create", "update", "delete"))
