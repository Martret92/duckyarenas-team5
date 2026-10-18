"""F1-A: valores internos puros. La estructura no autentica emisor ni User."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType


class InvalidRewardIdentityError(ValueError):
    """Identidad lógica estructuralmente inválida."""


class InvalidRewardFactError(ValueError):
    """Hecho semántico estructuralmente inválido."""


class RewardCanonicalizationError(ValueError):
    """No puede representarse el hecho mediante el contrato canónico."""


class InvalidRewardRuleSetError(ValueError):
    """Configuración declarativa o propuesta inválida."""


class AmbiguousRewardRulesError(ValueError):
    """Más de una regla coincide; no se elige ni acumula por orden."""


def _text(value, error, *, maximum=None, nonempty=True):
    if type(value) is not str or (nonempty and not value) or (maximum is not None and len(value) > maximum):
        raise error("Cadena fuera del contrato estructural.")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise error("Texto no representable en UTF-8.") from None


def _freeze(value, error, active=None, depth=0):
    if type(value) in (str, int, bool, type(None)):
        if type(value) is str:
            _text(value, error, nonempty=False)
        elif type(value) is int:
            try:
                str(value)  # Detectar límites técnicos de representación del intérprete.
            except ValueError:
                raise error("Entero no representable como JSON.") from None
        return value
    if not isinstance(value, Mapping) and type(value) not in (list, tuple):
        raise error("Tipo semántico no admitido.")
    if depth >= 64:
        raise error("Profundidad técnica excedida.")
    active = set() if active is None else active
    if id(value) in active:
        raise error("Estructura semántica cíclica.")
    active.add(id(value))
    try:
        if isinstance(value, Mapping):
            copied = {}
            for key, item in value.items():
                _text(key, error, nonempty=False)
                copied[key] = _freeze(item, error, active, depth + 1)
            return MappingProxyType(copied)
        return tuple(_freeze(item, error, active, depth + 1) for item in value)
    except RecursionError:
        raise error("Profundidad técnica excedida.") from None
    finally:
        active.remove(id(value))


@dataclass(frozen=True)
class RewardIdentity:
    origin_code: str
    fact_id: str
    recipient_id: str

    def __post_init__(self):
        _text(self.origin_code, InvalidRewardIdentityError)
        _text(self.fact_id, InvalidRewardIdentityError, maximum=255)
        _text(self.recipient_id, InvalidRewardIdentityError)


@dataclass(frozen=True)
class ValidatedRewardFact:
    identity: RewardIdentity
    activity_type: str
    occurred_at: datetime
    result: Mapping
    context: Mapping

    def __post_init__(self):
        if type(self.identity) is not RewardIdentity:
            raise InvalidRewardFactError("Se requiere identidad lógica válida.")
        try:
            self.identity.__post_init__()
        except InvalidRewardIdentityError:
            raise InvalidRewardFactError("Identidad del hecho inválida.") from None
        _text(self.activity_type, InvalidRewardFactError)
        if not isinstance(self.occurred_at, datetime):
            raise InvalidRewardFactError("Se requiere datetime con zona explícita.")
        try:
            if self.occurred_at.utcoffset() is None:
                raise InvalidRewardFactError("Datetime sin zona explícita.")
            instant = self.occurred_at.astimezone(timezone.utc)
        except (ValueError, OverflowError, TypeError):
            raise InvalidRewardFactError("Instante no representable en UTC.") from None
        object.__setattr__(self, "occurred_at", instant)
        for name in ("result", "context"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise InvalidRewardFactError("Resultado/contexto deben ser objetos JSON.")
            object.__setattr__(self, name, _freeze(value, InvalidRewardFactError))


def _checked_fact(fact):
    if type(fact) is not ValidatedRewardFact:
        raise InvalidRewardFactError("Se requiere un hecho validado estructuralmente.")
    return ValidatedRewardFact(fact.identity, fact.activity_type, fact.occurred_at, fact.result, fact.context)


def _collection(value):
    if type(value) not in (tuple, list):
        raise InvalidRewardRuleSetError("Se requiere una colección explícita ordenada.")
    return tuple(value)


@dataclass(frozen=True)
class ProposedEffect:
    effect_type: str
    quantity: int

    def __post_init__(self):
        _text(self.effect_type, InvalidRewardRuleSetError)
        if type(self.quantity) is not int or self.quantity <= 0:
            raise InvalidRewardRuleSetError("Cantidad propuesta debe ser entero positivo sin bool.")


def _effects(value):
    items = _collection(value)
    if any(type(item) is not ProposedEffect for item in items):
        raise InvalidRewardRuleSetError("Propuestas de efectos inválidas.")
    for item in items:
        item.__post_init__()
    return items


@dataclass(frozen=True)
class RewardRule:
    rule_id: str
    activity_type: str
    result_equals: Mapping
    proposed_effects: tuple[ProposedEffect, ...]

    def __post_init__(self):
        _text(self.rule_id, InvalidRewardRuleSetError)
        _text(self.activity_type, InvalidRewardRuleSetError)
        if not isinstance(self.result_equals, Mapping):
            raise InvalidRewardRuleSetError("Condiciones deben ser objeto de escalares JSON.")
        conditions = _freeze(self.result_equals, InvalidRewardRuleSetError)
        if any(type(value) not in (str, int, bool, type(None)) for value in conditions.values()):
            raise InvalidRewardRuleSetError("Solo igualdad de valores escalares JSON.")
        object.__setattr__(self, "result_equals", conditions)
        object.__setattr__(self, "proposed_effects", _effects(self.proposed_effects))


@dataclass(frozen=True)
class RewardRuleSet:
    version: str
    rules: tuple[RewardRule, ...]

    def __post_init__(self):
        _text(self.version, InvalidRewardRuleSetError)
        rules = _collection(self.rules)
        if any(type(rule) is not RewardRule for rule in rules):
            raise InvalidRewardRuleSetError("Reglas estructuralmente inválidas.")
        rules = tuple(RewardRule(rule.rule_id, rule.activity_type, rule.result_equals,
                                 rule.proposed_effects) for rule in rules)
        if len({rule.rule_id for rule in rules}) != len(rules):
            raise InvalidRewardRuleSetError("Identidades de regla duplicadas.")
        object.__setattr__(self, "rules", rules)


@dataclass(frozen=True)
class RewardDecision:
    rule_set_version: str
    matched_rule_id: str | None
    eligible: bool
    proposed_effects: tuple[ProposedEffect, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        _text(self.rule_set_version, InvalidRewardRuleSetError)
        effects = _effects(self.proposed_effects)
        reasons = _collection(self.reason_codes)
        if type(self.eligible) is not bool:
            raise InvalidRewardRuleSetError("Elegibilidad debe ser booleana.")
        if self.eligible:
            _text(self.matched_rule_id, InvalidRewardRuleSetError)
            expected = () if effects else ("MATCHED_NO_EFFECT",)
        else:
            if self.matched_rule_id is not None or effects:
                raise InvalidRewardRuleSetError("Decisión sin coincidencia incoherente.")
            expected = ("NO_MATCHING_RULE",)
        if reasons != expected:
            raise InvalidRewardRuleSetError("Motivos de evaluación incoherentes.")
        object.__setattr__(self, "proposed_effects", effects)
        object.__setattr__(self, "reason_codes", reasons)
