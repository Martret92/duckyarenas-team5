"""JSON semántico versionado y SHA-256, sin autorización ni persistencia."""

from collections.abc import Mapping
from hashlib import sha256
import json

from .reward_types import InvalidRewardFactError, RewardCanonicalizationError, ValidatedRewardFact, _checked_fact


def _json_value(value):
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_json_value(item) for item in value]
    return value


def canonical_reward_bytes(fact: ValidatedRewardFact) -> bytes:
    try:
        fact = _checked_fact(fact)
        semantic = {
            "schema": "rewards-semantic-v1",
            "identity": {"origin_code": fact.identity.origin_code, "fact_id": fact.identity.fact_id,
                         "recipient_id": fact.identity.recipient_id},
            "activity_type": fact.activity_type,
            "occurred_at": fact.occurred_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            "result": _json_value(fact.result), "context": _json_value(fact.context),
        }
        return json.dumps(semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("utf-8")
    except (InvalidRewardFactError, ValueError, TypeError, OverflowError, RecursionError):
        raise RewardCanonicalizationError("Hecho no representable mediante JSON semántico V1.") from None


def semantic_fingerprint(fact: ValidatedRewardFact) -> str:
    return sha256(canonical_reward_bytes(fact)).hexdigest()
