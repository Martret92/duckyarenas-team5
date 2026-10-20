"""A3.3 pure tests: synthetic identities/references, no Django or ORM fixtures."""

import ast
from dataclasses import FrozenInstanceError, asdict, fields, replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from . import profile_classification_rules as rules
from .profile_classification_rules import (
    ClassificationAction as Action, ClassificationContentConflictError,
    ClassificationOriginConflictError, ClassificationRequest,
    ClassificationResultKind as Kind, ClassificationRuleResult,
    ConfirmedClassificationEvent, ForbiddenClassificationTransitionError,
    InconsistentClassificationHistoryError, InvalidClassificationInputError,
    PolicySnapshot, ProfileOrigin as Origin, StaleClassificationRevisionError,
    TransitionState as State, evaluate_classification_rules,
)


def request(action=Action.TRANSITION, target=State.V1_VERIFIED, expected=1, **changes):
    return ClassificationRequest(
        changes.pop("profile_id", 17), changes.pop("operation_key", "synthetic-classification"),
        action, changes.pop("origin", Origin.LEGACY_V1), target, expected, **changes,
    )


def policy(state=State.PENDING_REVIEW, revision=1, origin=Origin.LEGACY_V1, profile_id=17):
    return PolicySnapshot(profile_id, origin, state, revision)


def block_event(state=State.TARGET_PREPARED, revision=7, origin=Origin.LEGACY_V1, profile_id=17):
    original = request(Action.BLOCK, State.BLOCKED, revision, operation_key="synthetic-block",
                       origin=origin, profile_id=profile_id, incident_reference="synthetic-incident")
    return ConfirmedClassificationEvent(
        original, policy(state, revision, origin, profile_id), policy(State.BLOCKED, revision + 1, origin, profile_id),
    )


def recovery_request(block):
    return request(Action.RECOVER, block.before.transition_state, block.after.revision,
                   blocking_operation_key=block.request.operation_key, operation_key="synthetic-recover",
                   origin=block.after.origin, profile_id=block.after.profile_id)


class ProfileClassificationRulesTests(TestCase):
    def test_three_valid_initial_origins(self):
        for origin, target in ((Origin.LEGACY_V1, State.PENDING_REVIEW),
                               (Origin.NATIVE_V1, State.V1_VERIFIED),
                               (Origin.NATIVE_TARGET, State.TARGET_CONFIRMED)):
            with self.subTest(origin=origin):
                result = evaluate_classification_rules(request(Action.INITIAL, target, None, origin=origin), current=None)
                self.assertEqual(result.kind, Kind.NEW_CANDIDATE)
                self.assertIsNone(result.before)
                self.assertEqual(result.after, policy(target, 1, origin))

    def test_every_incorrect_initial_origin_state_combination(self):
        initial = {Origin.LEGACY_V1: State.PENDING_REVIEW, Origin.NATIVE_V1: State.V1_VERIFIED,
                   Origin.NATIVE_TARGET: State.TARGET_CONFIRMED}
        for origin in Origin:
            for state in State:
                if state is initial[origin]:
                    continue
                with self.subTest(origin=origin, state=state), self.assertRaises(ForbiddenClassificationTransitionError):
                    evaluate_classification_rules(request(Action.INITIAL, state, None, origin=origin), current=None)

    def test_initial_rejected_when_policy_exists(self):
        with self.assertRaises(ForbiddenClassificationTransitionError):
            evaluate_classification_rules(request(Action.INITIAL, State.PENDING_REVIEW, None), current=policy())

    def test_absent_policy_is_not_pending_review_and_requires_initial_action(self):
        for action in (Action.TRANSITION, Action.BLOCK, Action.RECOVER):
            with self.subTest(action=action), self.assertRaises(ForbiddenClassificationTransitionError):
                evaluate_classification_rules(request(action), current=None)
        result = evaluate_classification_rules(request(), current=policy())
        self.assertEqual(result.after.transition_state, State.V1_VERIFIED)

    def test_initial_revision_none_is_not_zero_or_a_positive_prior_revision(self):
        with self.assertRaises(InvalidClassificationInputError):
            request(Action.INITIAL, State.PENDING_REVIEW, 0)
        with self.assertRaises(StaleClassificationRevisionError):
            evaluate_classification_rules(request(Action.INITIAL, State.PENDING_REVIEW, 1), current=None)

    def test_entire_ordinary_transition_matrix_for_every_origin(self):
        permitted = {(State.PENDING_REVIEW, State.V1_VERIFIED),
                     (State.V1_VERIFIED, State.TARGET_PREPARED),
                     (State.TARGET_PREPARED, State.TARGET_CONFIRMED)}
        for origin in Origin:
            for before in State:
                for after in State:
                    with self.subTest(origin=origin, before=before, after=after):
                        original = request(target=after, expected=41, origin=origin)
                        current = policy(before, 41, origin)
                        if (before, after) in permitted:
                            result = evaluate_classification_rules(original, current=current)
                            self.assertEqual(result.before, current)
                            self.assertEqual(result.after, policy(after, 42, origin))
                        else:
                            with self.assertRaises(ForbiddenClassificationTransitionError):
                                evaluate_classification_rules(original, current=current)

    def test_block_from_every_state_except_blocked(self):
        original = request(Action.BLOCK, State.BLOCKED, 4, incident_reference="synthetic-incident")
        for state in State:
            with self.subTest(state=state):
                current = policy(state, 4)
                if state is State.BLOCKED:
                    with self.assertRaises(ForbiddenClassificationTransitionError):
                        evaluate_classification_rules(original, current=current)
                else:
                    result = evaluate_classification_rules(original, current=current)
                    self.assertEqual(result.before, current)
                    self.assertEqual(result.after, policy(State.BLOCKED, 5))

    def test_block_requires_blocked_destination_and_nonempty_incident(self):
        for incident in (None, ""):
            with self.subTest(incident=incident), self.assertRaises(InvalidClassificationInputError):
                evaluate_classification_rules(request(Action.BLOCK, State.BLOCKED, incident_reference=incident), current=policy())
        with self.assertRaises(ForbiddenClassificationTransitionError):
            evaluate_classification_rules(request(Action.BLOCK, State.V1_VERIFIED, incident_reference="synthetic"), current=policy())
        original = request(Action.BLOCK, State.BLOCKED, incident_reference="  synthetic opaque  ")
        evaluate_classification_rules(original, current=policy())
        self.assertEqual(original.incident_reference, "  synthetic opaque  ")

    def test_recover_to_each_possible_pre_block_state(self):
        for state in State:
            if state is State.BLOCKED:
                continue
            with self.subTest(state=state):
                block = block_event(state)
                result = evaluate_classification_rules(recovery_request(block), current=block.after, blocking_event=block)
                self.assertEqual(result.kind, Kind.NEW_CANDIDATE)
                self.assertEqual(result.before, block.after)
                self.assertEqual(result.after, policy(state, block.after.revision + 1))

    def assert_unchanged_and_frozen(self, values, originals):
        self.assertEqual(tuple(asdict(value) for value in values), originals)
        for value in values:
            self.assertFalse(hasattr(value, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                setattr(value, fields(value)[0].name, None)
        self.assertEqual(tuple(asdict(value) for value in values), originals)

    def test_new_recovery_cannot_reuse_confirmed_block_identity(self):
        block = block_event()
        original = replace(recovery_request(block), operation_key=block.request.operation_key)
        inputs = (original, block, block.after)
        before = tuple(asdict(value) for value in inputs)
        with self.assertRaises(ClassificationContentConflictError):
            evaluate_classification_rules(original, current=block.after, blocking_event=block)
        self.assert_unchanged_and_frozen(inputs, before)

    def test_historical_recovery_with_block_identity_is_inconsistent(self):
        block = block_event()
        original = replace(recovery_request(block), operation_key=block.request.operation_key)
        event = ConfirmedClassificationEvent(original, block.after, policy(State.TARGET_PREPARED, 9))
        current = policy(State.TARGET_CONFIRMED, 30)
        inputs = (original, block, event, current)
        before = tuple(asdict(value) for value in inputs)
        with self.assertRaises(InconsistentClassificationHistoryError):
            evaluate_classification_rules(original, current=current, recorded_event=event, blocking_event=block)
        self.assert_unchanged_and_frozen(inputs, before)

    def test_distinct_recovery_identity_allows_candidate_and_both_historical_replays(self):
        block = block_event()
        original = recovery_request(block)
        self.assertNotEqual(original.operation_key, block.request.operation_key)
        self.assertEqual(original.blocking_operation_key, block.request.operation_key)
        inputs = (original, block, block.after)
        before = tuple(asdict(value) for value in inputs)
        candidate = evaluate_classification_rules(original, current=block.after, blocking_event=block)
        self.assertEqual(candidate.kind, Kind.NEW_CANDIDATE)
        self.assertEqual(candidate.after.transition_state, block.before.transition_state)
        self.assertEqual(candidate.after.revision, block.after.revision + 1)
        event = ConfirmedClassificationEvent(original, candidate.before, candidate.after)
        current = policy(State.TARGET_CONFIRMED, 30)
        history_inputs = (event, current)
        history_before = tuple(asdict(value) for value in history_inputs)
        recovery_replay = evaluate_classification_rules(original, current=current, recorded_event=event, blocking_event=block)
        block_replay = evaluate_classification_rules(block.request, current=current, recorded_event=block)
        self.assertEqual(recovery_replay, ClassificationRuleResult(Kind.HISTORICAL_REPLAY, event.before, event.after))
        self.assertEqual(block_replay, ClassificationRuleResult(Kind.HISTORICAL_REPLAY, block.before, block.after))
        self.assert_unchanged_and_frozen(inputs, before)
        self.assert_unchanged_and_frozen(history_inputs, history_before)
        results = (candidate, recovery_replay, block_replay)
        self.assert_unchanged_and_frozen(results, tuple(asdict(value) for value in results))

    def test_recover_requires_current_blocked_state(self):
        block = block_event()
        for state in State:
            if state is State.BLOCKED:
                continue
            with self.subTest(state=state), self.assertRaises(ForbiddenClassificationTransitionError):
                evaluate_classification_rules(recovery_request(block), current=replace(block.after, transition_state=state), blocking_event=block)

    def test_recover_cannot_choose_arbitrary_destination(self):
        block = block_event()
        for state in State:
            if state is block.before.transition_state:
                continue
            with self.subTest(state=state), self.assertRaises(ForbiddenClassificationTransitionError):
                evaluate_classification_rules(replace(recovery_request(block), target_state=state), current=block.after, blocking_event=block)

    def test_recovery_requires_original_block_and_matching_link(self):
        block = block_event()
        with self.assertRaises(InconsistentClassificationHistoryError):
            evaluate_classification_rules(recovery_request(block), current=block.after)
        for link in (None, "", "synthetic-other-block", " synthetic-block"):
            with self.subTest(link=link), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(replace(recovery_request(block), blocking_operation_key=link), current=block.after, blocking_event=block)

    def test_foreign_block_profile_or_origin_rejected(self):
        block = block_event()
        for foreign in (block_event(profile_id=18), block_event(origin=Origin.NATIVE_V1)):
            with self.subTest(foreign=foreign.request.origin), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(recovery_request(block), current=block.after, blocking_event=foreign)

    def test_blocking_revision_must_be_the_current_blocked_revision(self):
        block = block_event()
        for revision in (block.after.revision - 1, block.after.revision + 1):
            with self.subTest(revision=revision), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(replace(recovery_request(block), expected_revision=revision),
                                              current=replace(block.after, revision=revision), blocking_event=block)

    def test_recovery_rejects_contradictory_block_history(self):
        block = block_event()
        bad_blocks = (
            replace(block, before=None),
            replace(block, before=replace(block.before, transition_state=State.BLOCKED)),
            replace(block, before=replace(block.before, revision=1)),
            replace(block, after=replace(block.after, revision=999)),
            replace(block, request=replace(block.request, incident_reference=None)),
            replace(block, request=replace(block.request, action=Action.TRANSITION)),
        )
        for bad in bad_blocks:
            with self.subTest(before=bad.before), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(recovery_request(block), current=block.after, blocking_event=bad)

    def test_no_automatic_recovery_when_no_recover_action_requested(self):
        block = block_event()
        with self.assertRaises(ForbiddenClassificationTransitionError):
            evaluate_classification_rules(request(target=block.before.transition_state, expected=block.after.revision),
                                          current=block.after, blocking_event=block)

    def test_new_operations_cannot_change_origin(self):
        for origin in (Origin.NATIVE_V1, Origin.NATIVE_TARGET):
            with self.subTest(origin=origin), self.assertRaises(ClassificationOriginConflictError):
                evaluate_classification_rules(request(origin=origin), current=policy())

    def test_expected_revision_exact_current_for_all_new_actions(self):
        for action in (Action.TRANSITION, Action.BLOCK, Action.RECOVER):
            for expected in (None, 1, 3):
                with self.subTest(action=action, expected=expected), self.assertRaises(StaleClassificationRevisionError):
                    evaluate_classification_rules(request(action, expected=expected), current=policy(revision=2))

    def test_revision_and_profile_id_have_no_unapproved_physical_maximum(self):
        large = 10**100
        result = evaluate_classification_rules(request(expected=large, profile_id=large),
                                              current=policy(revision=large, profile_id=large))
        self.assertEqual(result.after.revision, large + 1)
        self.assertEqual(result.after.profile_id, large)

    def test_current_profile_identity_must_match(self):
        with self.assertRaises(InvalidClassificationInputError):
            evaluate_classification_rules(request(), current=policy(profile_id=18))

    def test_request_strict_positive_integer_types(self):
        original = request()
        for name in ("profile_id", "expected_revision"):
            for value in (0, -1, True, False, 1.0, 1.5, "1", Decimal("1"), Fraction(1, 1), [], {}):
                with self.subTest(name=name, kind=type(value)), self.assertRaises(InvalidClassificationInputError):
                    replace(original, **{name: value})
        with self.assertRaises(InvalidClassificationInputError):
            replace(original, profile_id=None)

    def test_request_requires_exact_enums_and_text_not_strings_as_enums(self):
        original = request()
        for name, values in (("action", ("TRANSITION", State.V1_VERIFIED, None, 1)),
                             ("origin", ("LEGACY_V1", State.BLOCKED, None)),
                             ("target_state", ("V1_VERIFIED", Origin.LEGACY_V1, None)),
                             ("operation_key", ("", None, 1, [], {})),
                             ("incident_reference", (1, [], {})),
                             ("blocking_operation_key", (1, [], {}))):
            for value in values:
                with self.subTest(name=name, kind=type(value)), self.assertRaises(InvalidClassificationInputError):
                    replace(original, **{name: value})

    def test_text_is_opaque_exact_and_without_physical_length_limits(self):
        for key in (" ", " synthetic ", "synthetic-" + "x" * 1000):
            original = request(operation_key=key, incident_reference="", blocking_operation_key="")
            result = evaluate_classification_rules(original, current=policy())
            event = ConfirmedClassificationEvent(original, result.before, result.after)
            self.assertEqual(evaluate_classification_rules(original, current=None, recorded_event=event).kind,
                             Kind.HISTORICAL_REPLAY)
            self.assertEqual(event.request.operation_key, key)

    def test_policy_structure_strict(self):
        for name in ("profile_id", "revision"):
            for value in (None, 0, -1, True, False, 1.0, "1", []):
                with self.subTest(name=name, value=value), self.assertRaises(InvalidClassificationInputError):
                    replace(policy(), **{name: value})
        for name in ("origin", "transition_state"):
            with self.subTest(name=name), self.assertRaises(InvalidClassificationInputError):
                replace(policy(), **{name: "invalid"})

    def test_replay_same_content_with_later_current_state_revision(self):
        original = request()
        event = ConfirmedClassificationEvent(original, policy(), policy(State.V1_VERIFIED, 2))
        result = evaluate_classification_rules(original, current=policy(State.TARGET_CONFIRMED, 500), recorded_event=event)
        self.assertEqual(result, ClassificationRuleResult(Kind.HISTORICAL_REPLAY, event.before, event.after))
        self.assertIs(result.after, event.after)

    def test_replay_initial_classification_after_several_transitions(self):
        for origin, state in ((Origin.LEGACY_V1, State.PENDING_REVIEW), (Origin.NATIVE_V1, State.V1_VERIFIED),
                              (Origin.NATIVE_TARGET, State.TARGET_CONFIRMED)):
            with self.subTest(origin=origin):
                original = request(Action.INITIAL, state, None, origin=origin)
                event = ConfirmedClassificationEvent(original, None, policy(state, 1, origin))
                result = evaluate_classification_rules(original, current=policy(State.TARGET_CONFIRMED, 19, origin), recorded_event=event)
                self.assertIsNone(result.before)
                self.assertEqual(result.after.revision, 1)
                self.assertEqual(result.kind, Kind.HISTORICAL_REPLAY)

    def test_replay_block_after_recovery_does_not_block_current_again(self):
        event = block_event()
        current = policy(State.TARGET_CONFIRMED, 19)
        before = asdict(current)
        result = evaluate_classification_rules(event.request, current=current, recorded_event=event)
        self.assertEqual(result.after.transition_state, State.BLOCKED)
        self.assertEqual(result.after.revision, 8)
        self.assertEqual(asdict(current), before)
        self.assertEqual(current.transition_state, State.TARGET_CONFIRMED)

    def test_replay_recovery_requires_historical_block_not_current_eligibility(self):
        for state in State:
            if state is State.BLOCKED:
                continue
            with self.subTest(state=state):
                block = block_event(state)
                original = recovery_request(block)
                event = ConfirmedClassificationEvent(original, block.after, policy(state, 9))
                result = evaluate_classification_rules(original, current=policy(State.TARGET_CONFIRMED, 99),
                                                       recorded_event=event, blocking_event=block)
                self.assertEqual(result.after, event.after)
                self.assertEqual(result.kind, Kind.HISTORICAL_REPLAY)
                with self.assertRaises(InconsistentClassificationHistoryError):
                    evaluate_classification_rules(original, current=policy(State.TARGET_CONFIRMED, 99), recorded_event=event)

    def test_replay_requires_exact_original_content_every_component(self):
        block = block_event()
        original = recovery_request(block)
        event = ConfirmedClassificationEvent(original, block.after, policy(State.TARGET_PREPARED, 9))
        changes = ({"expected_revision": 7}, {"target_state": State.TARGET_CONFIRMED},
                   {"origin": Origin.NATIVE_V1}, {"action": Action.TRANSITION},
                   {"incident_reference": "different-incident"},
                   {"blocking_operation_key": "different-block"})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ClassificationContentConflictError):
                evaluate_classification_rules(replace(original, **change), current=policy(State.TARGET_CONFIRMED, 99),
                                              recorded_event=event, blocking_event=block)

    def test_none_and_empty_text_original_content_are_distinct(self):
        original = request(incident_reference=None)
        event = ConfirmedClassificationEvent(original, policy(), policy(State.V1_VERIFIED, 2))
        with self.assertRaises(ClassificationContentConflictError):
            evaluate_classification_rules(replace(original, incident_reference=""), current=policy(), recorded_event=event)

    def test_other_profile_or_exact_key_is_not_absent_history(self):
        original = request()
        event = ConfirmedClassificationEvent(original, policy(), policy(State.V1_VERIFIED, 2))
        for change in ({"profile_id": 18}, {"operation_key": " synthetic-classification"},
                       {"operation_key": "synthetic-other"}):
            with self.subTest(change=change), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(replace(original, **change), current=None, recorded_event=event)

    def test_historical_integrity_precedes_content_conflict(self):
        original = request()
        bad = ConfirmedClassificationEvent(original, policy(), policy(State.V1_VERIFIED, 3))
        with self.assertRaises(InconsistentClassificationHistoryError):
            evaluate_classification_rules(replace(original, target_state=State.TARGET_PREPARED), current=policy(), recorded_event=bad)

    def test_historical_initial_invariants_no_fabricated_prior_state(self):
        original = request(Action.INITIAL, State.PENDING_REVIEW, None)
        good = ConfirmedClassificationEvent(original, None, policy())
        bad_events = (replace(good, before=policy()), replace(good, after=policy(revision=2)),
                      replace(good, request=replace(original, expected_revision=1)),
                      replace(good, request=replace(original, target_state=State.V1_VERIFIED), after=policy(State.V1_VERIFIED)))
        for event in bad_events:
            with self.subTest(event=event.after), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(event.request, current=None, recorded_event=event)

    def test_historical_transition_identity_origin_and_revisions(self):
        original = request()
        good = ConfirmedClassificationEvent(original, policy(), policy(State.V1_VERIFIED, 2))
        bad_events = (replace(good, before=None),
                      replace(good, before=policy(profile_id=18)),
                      replace(good, before=policy(origin=Origin.NATIVE_V1)),
                      replace(good, before=policy(revision=2)),
                      replace(good, after=policy(State.V1_VERIFIED, 2, profile_id=18)),
                      replace(good, after=policy(State.V1_VERIFIED, 2, origin=Origin.NATIVE_TARGET)),
                      replace(good, after=policy(State.TARGET_PREPARED, 2)),
                      replace(good, after=policy(State.V1_VERIFIED, 1)),
                      replace(good, after=policy(State.V1_VERIFIED, 3)),
                      replace(good, request=replace(original, expected_revision=None)))
        for event in bad_events:
            with self.subTest(event=event.after), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(original, current=policy(State.TARGET_CONFIRMED, 100), recorded_event=event)

    def test_historical_ordinary_action_relationships_entire_matrix(self):
        permitted = {(State.PENDING_REVIEW, State.V1_VERIFIED), (State.V1_VERIFIED, State.TARGET_PREPARED),
                     (State.TARGET_PREPARED, State.TARGET_CONFIRMED)}
        for before in State:
            for after in State:
                original = request(target=after, expected=7)
                event = ConfirmedClassificationEvent(original, policy(before, 7), policy(after, 8))
                with self.subTest(before=before, after=after):
                    if (before, after) in permitted:
                        self.assertEqual(evaluate_classification_rules(original, current=None, recorded_event=event).kind,
                                         Kind.HISTORICAL_REPLAY)
                    else:
                        with self.assertRaises(InconsistentClassificationHistoryError):
                            evaluate_classification_rules(original, current=None, recorded_event=event)

    def test_historical_recovery_cannot_hide_missing_or_wrong_before_state(self):
        block = block_event()
        original = recovery_request(block)
        for before in (None, policy(State.V1_VERIFIED, 8)):
            event = ConfirmedClassificationEvent(original, before, policy(State.TARGET_PREPARED, 9))
            with self.subTest(before=before), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(original, current=None, recorded_event=event, blocking_event=block)

    def test_replay_does_not_run_new_candidate_path(self):
        event = block_event()
        with patch.object(rules, "_new_candidate", side_effect=AssertionError):
            result = evaluate_classification_rules(event.request, current=policy(State.TARGET_CONFIRMED, 900), recorded_event=event)
        self.assertEqual(result.kind, Kind.HISTORICAL_REPLAY)

    def test_request_and_current_validated_before_replay(self):
        event = block_event()
        for original, current in (({}, None), (event.request, {}), (event.request, policy(profile_id=18))):
            with self.subTest(current=type(current)), self.assertRaises(InvalidClassificationInputError):
                evaluate_classification_rules(original, current=current, recorded_event=event)

    def test_history_requires_typed_complete_records_not_mappings_or_mutable_nesting(self):
        event = block_event()
        for value in ({}, [], "history", asdict(event), SimpleNamespace(**asdict(event))):
            with self.subTest(kind=type(value)), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(event.request, current=None, recorded_event=value)
            with self.subTest(kind=type(value)), self.assertRaises(InconsistentClassificationHistoryError):
                evaluate_classification_rules(request(), current=policy(), blocking_event=value)
        for changes in ({"request": {}}, {"before": []}, {"after": None}, {"after": {}}):
            with self.subTest(changes=changes), self.assertRaises(InconsistentClassificationHistoryError):
                replace(event, **changes)

    def test_all_dataclasses_frozen_slots_and_nested_immutable(self):
        event = block_event()
        result = evaluate_classification_rules(event.request, current=None, recorded_event=event)
        for value in (event.request, event.before, event.after, event, result):
            self.assertFalse(hasattr(value, "__dict__"))
            name = fields(value)[0].name
            with self.subTest(kind=type(value)), self.assertRaises(FrozenInstanceError):
                setattr(value, name, None)
        with self.assertRaises(InvalidClassificationInputError):
            ClassificationRuleResult(Kind.NEW_CANDIDATE, [], policy())

    def test_determinism_inputs_unchanged_and_result_has_no_authority_fields(self):
        original, current = request(), policy()
        before = (asdict(original), asdict(current))
        first = evaluate_classification_rules(original, current=current)
        self.assertEqual(first, evaluate_classification_rules(original, current=current))
        self.assertEqual((asdict(original), asdict(current)), before)
        self.assertEqual({field.name for field in fields(first)}, {"kind", "before", "after"})
        self.assertNotIn("APPLIED", Kind.__members__)
        self.assertEqual(first.after.revision, current.revision + 1)

    def test_no_external_access_clock_or_mutable_global_dependency(self):
        original, current = request(), policy()
        with patch("builtins.open", side_effect=AssertionError), patch("socket.socket", side_effect=AssertionError), \
                patch("sqlite3.connect", side_effect=AssertionError), patch("time.time", side_effect=AssertionError):
            result = evaluate_classification_rules(original, current=current)
        self.assertEqual(result.kind, Kind.NEW_CANDIDATE)

    def test_no_calls_to_existing_services_and_imports_only_standard_library(self):
        names = {"apps.ecomotor.xp_service": "grant_historical_xp",
                 "apps.ecomotor.legacy_transition_audit": "audit_legacy_transition",
                 "apps.ecomotor.legacy_inventory_reader": "extract_legacy_audit_snapshot",
                 "apps.ecomotor.progression": "calculate_progression",
                 "apps.ecomotor.target_progression": "calculate_target_progression",
                 "apps.ecomotor.target_xp_plan": "plan_target_xp_grant",
                 "apps.ecomotor.target_catalog_validation": "validate_target_level_epoch_catalog"}
        forbidden = {module: SimpleNamespace(**{name: Mock(side_effect=AssertionError)}) for module, name in names.items()}
        with patch.dict(sys.modules, forbidden):
            evaluate_classification_rules(request(), current=policy())
        for module, name in names.items():
            getattr(forbidden[module], name).assert_not_called()
        tree = ast.parse(Path(rules.__file__).read_text(encoding="utf-8"))
        self.assertEqual([node.module for node in tree.body if isinstance(node, ast.ImportFrom)], ["dataclasses", "enum"])
        self.assertFalse(any(isinstance(node, ast.Import) for node in tree.body))

    def test_isolated_python_execution_without_django_configuration(self):
        code = (
            "import sys; sys.path.insert(0,sys.argv[1]); "
            "from apps.ecomotor.profile_classification_rules import *; "
            "r=ClassificationRequest(1,'synthetic-isolated',ClassificationAction.INITIAL,"
            "ProfileOrigin.NATIVE_TARGET,TransitionState.TARGET_CONFIRMED,None); "
            "x=evaluate_classification_rules(r,current=None); "
            "assert x.kind is ClassificationResultKind.NEW_CANDIDATE and x.after.revision==1; "
            "assert not any(n=='django' or n.startswith('django.') for n in sys.modules); "
            "assert not any(n.startswith('apps.ecomotor.') and n!='apps.ecomotor.profile_classification_rules' for n in sys.modules)"
        )
        completed = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2])],
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_safe_errors_do_not_include_original_key_or_incident(self):
        original = request(Action.BLOCK, State.BLOCKED, incident_reference="synthetic-private-incident",
                           operation_key="synthetic-private-operation")
        event = ConfirmedClassificationEvent(original, policy(), policy(State.BLOCKED, 2))
        with self.assertRaises(ClassificationContentConflictError) as caught:
            evaluate_classification_rules(replace(original, incident_reference="other"), current=None, recorded_event=event)
        self.assertNotIn(original.operation_key, str(caught.exception))
        self.assertNotIn(original.incident_reference, str(caught.exception))
