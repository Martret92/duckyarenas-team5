from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from unittest import TestCase

from .reward_identity import canonical_reward_bytes, semantic_fingerprint
from .reward_types import InvalidRewardFactError, RewardCanonicalizationError
from .test_reward_types import make_fact


VECTOR_BYTES = (
    b'{"activity_type":"test.activity","context":{},"identity":{"fact_id":"fact-1",'
    b'"origin_code":"test.origin","recipient_id":"user-1"},'
    b'"occurred_at":"2026-01-02T03:04:05.006007Z","result":{"ok":true,"score":3},'
    b'"schema":"rewards-semantic-v1"}'
)
VECTOR_SHA256 = "cd06ef621a4aa6f49994e0e4840e626a908fd5ddf7bea3475ef7c0f6a6ee42b8"


class RewardIdentityTests(TestCase):
    def test_fixed_canonical_bytes_and_hash_vector(self):
        self.assertEqual(canonical_reward_bytes(make_fact()), VECTOR_BYTES)
        self.assertEqual(semantic_fingerprint(make_fact()), VECTOR_SHA256)

    def test_exact_top_level_and_identity_keys(self):
        data = json.loads(canonical_reward_bytes(make_fact()))
        self.assertEqual(set(data), {"schema", "identity", "activity_type", "occurred_at", "result", "context"})
        self.assertEqual(set(data["identity"]), {"origin_code", "fact_id", "recipient_id"})
        self.assertEqual(data["schema"], "rewards-semantic-v1")

    def test_mapping_insertion_order_does_not_change_bytes(self):
        first = make_fact(result={"z": {"b": 2, "a": 1}, "a": []}, context={"y": 1, "x": 2})
        second = make_fact(result={"a": [], "z": {"a": 1, "b": 2}}, context={"x": 2, "y": 1})
        self.assertEqual(canonical_reward_bytes(first), canonical_reward_bytes(second))

    def test_array_order_matters_and_array_is_not_object(self):
        self.assertNotEqual(canonical_reward_bytes(make_fact(result={"v": [1, 2]})),
                            canonical_reward_bytes(make_fact(result={"v": [2, 1]})))
        self.assertNotEqual(canonical_reward_bytes(make_fact(result={"v": []})),
                            canonical_reward_bytes(make_fact(result={"v": {}})))

    def test_unicode_is_utf8_not_ascii_escaped_or_normalized(self):
        value = canonical_reward_bytes(make_fact(result={"é": "🌍"}))
        self.assertIn('"é":"🌍"'.encode(), value)
        self.assertNotIn(b"\\u", value)
        self.assertNotEqual(semantic_fingerprint(make_fact(result={"v": "é"})),
                            semantic_fingerprint(make_fact(result={"v": "e\u0301"})))

    def test_equivalent_timezones_and_six_microseconds(self):
        utc = datetime(2026, 1, 2, 3, 4, 5, 6007, tzinfo=timezone.utc)
        other = utc.astimezone(timezone(timedelta(hours=-7)))
        self.assertEqual(canonical_reward_bytes(make_fact(occurred_at=utc)),
                         canonical_reward_bytes(make_fact(occurred_at=other)))
        value = json.loads(canonical_reward_bytes(make_fact(occurred_at=utc.replace(microsecond=0))))
        self.assertEqual(value["occurred_at"], "2026-01-02T03:04:05.000000Z")

    def test_early_year_format_is_four_digits(self):
        data = json.loads(canonical_reward_bytes(make_fact(occurred_at=datetime(1, 1, 1, tzinfo=timezone.utc))))
        self.assertEqual(data["occurred_at"], "0001-01-01T00:00:00.000000Z")

    def test_naive_rejected_before_serialization(self):
        with self.assertRaises(InvalidRewardFactError):
            make_fact(occurred_at=datetime(2026, 1, 1))

    def test_identity_components_all_affect_hash(self):
        fact = make_fact()
        for field in ("origin_code", "fact_id", "recipient_id"):
            with self.subTest(field=field):
                altered = replace(fact, identity=replace(fact.identity, **{field: "changed-test-id"}))
                self.assertNotEqual(semantic_fingerprint(fact), semantic_fingerprint(altered))

    def test_all_semantic_components_affect_hash(self):
        fact = make_fact()
        changes = ({"activity_type": "other.test"}, {"result": {}}, {"context": {"new": 1}},
                   {"occurred_at": fact.occurred_at + timedelta(microseconds=1)})
        for change in changes:
            with self.subTest(change=change):
                self.assertNotEqual(semantic_fingerprint(fact), semantic_fingerprint(replace(fact, **change)))

    def test_boolean_and_integer_are_distinct_bytes(self):
        self.assertNotEqual(canonical_reward_bytes(make_fact(result={"v": True})),
                            canonical_reward_bytes(make_fact(result={"v": 1})))

    def test_external_http_retry_and_calculated_effects_excluded(self):
        outside = {"request_id": 1, "headers": {}, "csrf": "test", "rewards": 999, "rule_version": "later"}
        fact = make_fact()
        first = semantic_fingerprint(fact)
        outside.update(request_id=2, rewards=0)
        self.assertEqual(semantic_fingerprint(fact), first)
        text = canonical_reward_bytes(fact).decode()
        for field in outside:
            self.assertNotIn('"' + field + '"', text)

    def test_hash_matches_sha256_lowercase_and_is_repeatable(self):
        fact = make_fact()
        value = semantic_fingerprint(fact)
        self.assertRegex(value, r"^[0-9a-f]{64}$")
        self.assertEqual(value, sha256(canonical_reward_bytes(fact)).hexdigest())
        self.assertEqual(value, semantic_fingerprint(fact))

    def test_source_mutation_cannot_change_bytes_or_hash(self):
        source = {"nested": [{"x": 1}]}
        fact = make_fact(result=source)
        before = canonical_reward_bytes(fact), semantic_fingerprint(fact)
        source["nested"][0]["x"] = 2
        source["nested"].append(None)
        self.assertEqual(before, (canonical_reward_bytes(fact), semantic_fingerprint(fact)))

    def test_invalid_canonical_input_controlled_without_payload(self):
        for value in (None, {}, "secret-payload"):
            with self.assertRaises(RewardCanonicalizationError) as caught:
                canonical_reward_bytes(value)
            self.assertNotIn("secret-payload", str(caught.exception))
