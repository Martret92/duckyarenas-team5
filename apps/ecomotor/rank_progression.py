"""S13-A1: evaluación pura del siguiente rango, sin confirmación ni efectos.

La política y las evidencias provienen de un futuro adaptador autorizado. Validar
su estructura no autoriza al emisor ni confirma ninguna finalización educativa.
"""

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum


class InvalidRankProgressError(ValueError):
    """Progreso o rango confirmado estructuralmente inválidos."""


class InvalidRankPolicyError(ValueError):
    """Política completa, umbrales o requisitos inválidos."""


class InvalidRankEvidenceError(ValueError):
    """Evidencias estructuralmente inválidas o de otra especialización."""


class Rank(str, Enum):
    JUNIOR = "Junior"
    MIDDLE = "Middle"
    SENIOR = "Senior"
    MAESTRO = "Maestro"


class RankStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    PENDING = "PENDING"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    MAX_RANK = "MAX_RANK"


_ORDER = (Rank.JUNIOR, Rank.MIDDLE, Rank.SENIOR, Rank.MAESTRO)


def _identifier(value):
    # La validación no reescribe el identificador: no strip, alias ni casefold.
    return isinstance(value, str) and bool(value.strip())


def _nonnegative_integer(value):
    return type(value) is int and value >= 0


def _codes(values, error_type, label):
    """Copia defensiva canónica: los conjuntos de códigos no tienen orden lógico."""
    if (not isinstance(values, Collection)
            or isinstance(values, (str, bytes, bytearray, Mapping))):
        raise error_type(f"{label}: se exige una colección explícita de códigos.")
    codes = tuple(values)
    if any(not _identifier(code) for code in codes):
        raise error_type(f"{label}: código inválido.")
    if len(codes) != len(set(codes)):
        raise error_type(f"{label}: códigos duplicados.")
    return tuple(sorted(codes))


@dataclass(frozen=True, slots=True)
class RankProgress:
    specialization_code: str
    confirmed_rank: Rank | None
    domain_xp_total: int

    def __post_init__(self):
        if not _identifier(self.specialization_code):
            raise InvalidRankProgressError("Identidad de especialización inválida.")
        if self.confirmed_rank is not None and type(self.confirmed_rank) is not Rank:
            raise InvalidRankProgressError("Rango confirmado desconocido.")
        if not _nonnegative_integer(self.domain_xp_total):
            raise InvalidRankProgressError("La XP de dominio debe ser un entero no negativo.")


@dataclass(frozen=True, slots=True)
class RankRequirement:
    target_rank: Rank
    minimum_domain_xp: int
    required_course_codes: tuple[str, ...] = ()
    required_challenge_codes: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.target_rank) is not Rank:
            raise InvalidRankPolicyError("Destino de rango desconocido.")
        if not _nonnegative_integer(self.minimum_domain_xp):
            raise InvalidRankPolicyError("El umbral debe ser un entero no negativo.")
        if self.target_rank is Rank.JUNIOR and self.minimum_domain_xp == 0:
            raise InvalidRankPolicyError("Junior requiere XP de dominio positiva.")
        object.__setattr__(self, "required_course_codes", _codes(
            self.required_course_codes, InvalidRankPolicyError, "Cursos requeridos",
        ))
        object.__setattr__(self, "required_challenge_codes", _codes(
            self.required_challenge_codes, InvalidRankPolicyError, "Retos requeridos",
        ))


@dataclass(frozen=True, slots=True)
class RankPolicy:
    policy_code: str
    version: str
    specialization_code: str
    requirements: tuple[RankRequirement, ...]

    def __post_init__(self):
        if any(not _identifier(value) for value in (
                self.policy_code, self.version, self.specialization_code)):
            raise InvalidRankPolicyError("Identidad, versión o especialización inválida.")
        if (not isinstance(self.requirements, Sequence)
                or isinstance(self.requirements, (str, bytes, bytearray))):
            raise InvalidRankPolicyError("Los requisitos deben ser una secuencia ordenada.")
        requirements = tuple(self.requirements)
        if (len(requirements) != len(_ORDER)
                or any(type(row) is not RankRequirement for row in requirements)
                or tuple(row.target_rank for row in requirements) != _ORDER):
            raise InvalidRankPolicyError("Se requieren Junior, Middle, Senior y Maestro en orden.")
        if any(left.minimum_domain_xp >= right.minimum_domain_xp
               for left, right in zip(requirements, requirements[1:])):
            raise InvalidRankPolicyError("Los umbrales deben crecer estrictamente.")
        object.__setattr__(self, "requirements", requirements)


@dataclass(frozen=True, slots=True)
class RankEvidence:
    specialization_code: str
    completed_course_codes: tuple[str, ...] | None
    completed_challenge_codes: tuple[str, ...] | None

    def __post_init__(self):
        if not _identifier(self.specialization_code):
            raise InvalidRankEvidenceError("Identidad de especialización inválida.")
        for name in ("completed_course_codes", "completed_challenge_codes"):
            values = getattr(self, name)
            if values is not None:
                object.__setattr__(self, name, _codes(
                    values, InvalidRankEvidenceError, name,
                ))


@dataclass(frozen=True, slots=True)
class RankAssessment:
    policy_code: str
    policy_version: str
    specialization_code: str
    current_rank: Rank | None
    next_rank: Rank | None
    status: RankStatus
    missing_domain_xp: int
    missing_course_codes: tuple[str, ...]
    missing_challenge_codes: tuple[str, ...]
    unavailable_sources: tuple[str, ...]

    def __post_init__(self):
        for name in ("missing_course_codes", "missing_challenge_codes", "unavailable_sources"):
            object.__setattr__(self, name, tuple(getattr(self, name)))


def evaluate_rank_eligibility(
    progress: RankProgress, evidence: RankEvidence, policy: RankPolicy,
) -> RankAssessment:
    """Evalúa un solo sucesor; nunca persiste ascensos, XP ni recompensas.

    ``unavailable_sources`` utiliza exactamente ``"courses"`` y ``"challenges"``.
    Si faltan evidencias requeridas, EVIDENCE_UNAVAILABLE prevalece sobre PENDING,
    aunque se conservan todos los incumplimientos verificados conocidos.
    """
    if type(progress) is not RankProgress:
        raise InvalidRankProgressError("Se requiere RankProgress.")
    if type(policy) is not RankPolicy:
        raise InvalidRankPolicyError("Se requiere RankPolicy.")
    if type(evidence) is not RankEvidence:
        raise InvalidRankEvidenceError("Se requiere RankEvidence.")
    if progress.specialization_code != policy.specialization_code:
        raise InvalidRankProgressError("Progreso y política corresponden a especializaciones distintas.")
    if evidence.specialization_code != policy.specialization_code:
        raise InvalidRankEvidenceError("Evidencia y política corresponden a especializaciones distintas.")

    def result(next_rank, status, missing_xp=0, missing_courses=(),
               missing_challenges=(), unavailable=()):
        return RankAssessment(
            policy_code=policy.policy_code, policy_version=policy.version,
            specialization_code=policy.specialization_code,
            current_rank=progress.confirmed_rank, next_rank=next_rank,
            status=status, missing_domain_xp=missing_xp,
            missing_course_codes=missing_courses,
            missing_challenge_codes=missing_challenges,
            unavailable_sources=unavailable,
        )

    if progress.confirmed_rank is Rank.MAESTRO:
        return result(None, RankStatus.MAX_RANK)

    index = 0 if progress.confirmed_rank is None else _ORDER.index(progress.confirmed_rank) + 1
    requirement = policy.requirements[index]
    missing_xp = max(0, requirement.minimum_domain_xp - progress.domain_xp_total)
    missing_courses = ()
    missing_challenges = ()
    unavailable = []

    if requirement.required_course_codes:
        if evidence.completed_course_codes is None:
            unavailable.append("courses")
        else:
            completed = set(evidence.completed_course_codes)
            missing_courses = tuple(code for code in requirement.required_course_codes
                                    if code not in completed)
    if requirement.required_challenge_codes:
        if evidence.completed_challenge_codes is None:
            unavailable.append("challenges")
        else:
            completed = set(evidence.completed_challenge_codes)
            missing_challenges = tuple(code for code in requirement.required_challenge_codes
                                       if code not in completed)

    if unavailable:
        status = RankStatus.EVIDENCE_UNAVAILABLE
    elif missing_xp or missing_courses or missing_challenges:
        status = RankStatus.PENDING
    else:
        status = RankStatus.ELIGIBLE
    return result(requirement.target_rank, status, missing_xp,
                  missing_courses, missing_challenges, tuple(unavailable))
