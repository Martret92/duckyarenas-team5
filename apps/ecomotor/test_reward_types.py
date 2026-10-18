"""Tests estándar: sin Django, BD ni configuración real."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest import TestCase

from .reward_types import (
    InvalidRewardFactError, InvalidRewardIdentityError, RewardIdentity, ValidatedRewardFact,
)


def make_fact(**changes):
    values = dict(identity=RewardIdentity("test.origin", "fact-1", "user-1"), activity_type="test.activity",
                  occurred_at=datetime(2026, 1, 2, 3, 4, 5, 6007, tzinfo=timezone.utc),
                  result={"ok": True, "score": 3}, context={})
    return ValidatedRewardFact(**(values | changes))


class RewardTypeTests(TestCase):
    def test_valid_identity_has_no_profile_dependency(self):
        identity = RewardIdentity("arbitrary.test", "opaque fact", "external-user-test")
        self.assertEqual(identity.fact_id, "opaque fact")

    def test_invalid_identity_components(self):
        for field in ("origin_code", "fact_id", "recipient_id"):
            for value in ("", None, 1, True, "\ud800"):
                with self.subTest(field=field, value=repr(value)), self.assertRaises(InvalidRewardIdentityError):
                    replace(make_fact().identity, **{field: value})

    def test_fact_id_exact_length_and_no_normalization(self):
        identity = RewardIdentity(" origin ", "x" * 255, " user ")
        self.assertEqual(identity.origin_code, " origin ")
        self.assertEqual(len(identity.fact_id), 255)
        self.assertEqual(identity.recipient_id, " user ")
        with self.assertRaises(InvalidRewardIdentityError):
            replace(identity, fact_id="x" * 256)

    def test_invalid_activity_and_identity(self):
        for value in ("", None, True, "\ud800"):
            with self.subTest(value=repr(value)), self.assertRaises(InvalidRewardFactError):
                make_fact(activity_type=value)
        with self.assertRaises(InvalidRewardFactError):
            make_fact(identity={"origin_code": "test"})

    def test_naive_and_wrong_date_types_rejected(self):
        for value in (datetime(2026, 1, 1), date(2026, 1, 1), "2026-01-01Z", None, 1):
            with self.subTest(value=value), self.assertRaises(InvalidRewardFactError):
                make_fact(occurred_at=value)

    def test_aware_datetime_normalized_to_utc(self):
        instant = datetime(2026, 1, 1, 5, tzinfo=timezone(timedelta(hours=3)))
        self.assertEqual(make_fact(occurred_at=instant).occurred_at,
                         datetime(2026, 1, 1, 2, tzinfo=timezone.utc))
        self.assertIs(make_fact(occurred_at=instant).occurred_at.tzinfo, timezone.utc)

    def test_out_of_range_utc_conversion_controlled(self):
        with self.assertRaises(InvalidRewardFactError):
            make_fact(occurred_at=datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=1))))

    def test_exact_scalar_types_and_nested_arrays_objects(self):
        fact = make_fact(result={"all": ["á", -2, 0, 10**100, True, False, None, {"": []}]})
        self.assertEqual(fact.result["all"][:7], ("á", -2, 0, 10**100, True, False, None))
        self.assertIs(type(fact.result["all"][4]), bool)
        self.assertIs(type(fact.result["all"][1]), int)
        self.assertEqual(fact.result["all"][7][""], ())

    def test_result_and_context_must_be_objects(self):
        for field in ("result", "context"):
            for value in ([], (), None, 1, "text"):
                with self.subTest(field=field, value=value), self.assertRaises(InvalidRewardFactError):
                    make_fact(**{field: value})

    def test_prohibited_nested_types(self):
        forbidden = (1.0, float("nan"), float("inf"), Decimal("1"), date(2026, 1, 1),
                     datetime(2026, 1, 1, tzinfo=timezone.utc), {1}, object(), b"bytes")
        for value in forbidden:
            with self.subTest(value=type(value)), self.assertRaises(InvalidRewardFactError):
                make_fact(result={"nested": [value]})

    def test_mapping_keys_must_be_strings(self):
        for key in (1, True, None, ("tuple",)):
            with self.subTest(key=key), self.assertRaises(InvalidRewardFactError):
                make_fact(context={key: "x"})

    def test_unicode_utf8_and_no_implicit_normalization(self):
        fact = make_fact(result={"é": "🌍", "e\u0301": "different"})
        self.assertEqual(len(fact.result), 2)
        for data in ({"x": "\ud800"}, {"\udfff": 1}):
            with self.assertRaises(InvalidRewardFactError):
                make_fact(result=data)

    def test_cycles_and_shared_acyclic_references(self):
        circular = []
        circular.append(circular)
        obj = {}
        obj["self"] = obj
        for value in (circular, obj):
            with self.assertRaises(InvalidRewardFactError):
                make_fact(result={"cycle": value})
        shared = [1, 2]
        self.assertEqual(make_fact(result={"a": shared, "b": shared}).result["a"], (1, 2))

    def test_excessive_depth_controlled(self):
        value = 1
        for _ in range(70):
            value = [value]
        with self.assertRaises(InvalidRewardFactError):
            make_fact(result={"deep": value})

    def test_impossible_integer_serialization_controlled(self):
        import sys
        limit = sys.get_int_max_str_digits()
        if not limit:
            self.skipTest("El intérprete no impone límite de representación decimal.")
        with self.assertRaises(InvalidRewardFactError):
            make_fact(result={"huge": 10 ** (limit + 1)})

    def test_deep_immutability_and_defensive_copy(self):
        source = {"items": [{"score": 2}]}
        context = {"nested": [False]}
        fact = make_fact(result=source, context=context)
        source["items"][0]["score"] = 99
        context["nested"].append(True)
        self.assertEqual(fact.result["items"][0]["score"], 2)
        self.assertEqual(fact.context["nested"], (False,))
        with self.assertRaises(TypeError):
            fact.result["items"][0]["score"] = 3
        with self.assertRaises(AttributeError):
            fact.result["items"].append(1)
        with self.assertRaises(FrozenInstanceError):
            fact.activity_type = "changed"
        with self.assertRaises(FrozenInstanceError):
            fact.identity.fact_id = "changed"

    def test_inputs_not_mutated_and_error_does_not_echo_payload(self):
        source = {"secret-payload": [1, 2]}
        make_fact(result=source)
        self.assertEqual(source, {"secret-payload": [1, 2]})
        with self.assertRaises(InvalidRewardFactError) as caught:
            make_fact(result={"secret-payload": object()})
        self.assertNotIn("secret-payload", str(caught.exception))
