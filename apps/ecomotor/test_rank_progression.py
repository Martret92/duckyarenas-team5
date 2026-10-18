"""Pruebas S13-A1 con políticas y evidencias exclusivamente sintéticas."""

from dataclasses import FrozenInstanceError, replace
from itertools import permutations
from unittest import TestCase
from unittest.mock import patch

from .rank_progression import (
    InvalidRankEvidenceError, InvalidRankPolicyError, InvalidRankProgressError,
    Rank, RankAssessment, RankEvidence, RankPolicy, RankProgress, RankRequirement,
    RankStatus, evaluate_rank_eligibility,
)


RANKS = (Rank.JUNIOR, Rank.MIDDLE, Rank.SENIOR, Rank.MAESTRO)


def policy(*, specialization="synthetic-alpha", xp=(10, 20, 30, 40),
           courses=None, challenges=None, version="synthetic-v1", code="synthetic-policy"):
    courses = courses if courses is not None else {}
    challenges = challenges if challenges is not None else {}
    return RankPolicy(code, version, specialization, [
        RankRequirement(rank, threshold, courses.get(rank, ()), challenges.get(rank, ()))
        for rank, threshold in zip(RANKS, xp)
    ])


def progress(rank=None, xp=10, specialization="synthetic-alpha"):
    return RankProgress(specialization, rank, xp)


def evidence(courses=(), challenges=(), specialization="synthetic-alpha"):
    return RankEvidence(specialization, courses, challenges)


class RankSequenceTests(TestCase):
    def test_no_rank_then_four_confirmed_ranks_one_successor_only(self):
        expected = ((None, Rank.JUNIOR), (Rank.JUNIOR, Rank.MIDDLE),
                    (Rank.MIDDLE, Rank.SENIOR), (Rank.SENIOR, Rank.MAESTRO),
                    (Rank.MAESTRO, None))
        for current, next_rank in expected:
            with self.subTest(current=current):
                result = evaluate_rank_eligibility(progress(current, 1000), evidence(), policy())
                self.assertEqual(result.current_rank, current)
                self.assertEqual(result.next_rank, next_rank)
                self.assertEqual(result.status, RankStatus.MAX_RANK if next_rank is None else RankStatus.ELIGIBLE)
                self.assertIsInstance(result, RankAssessment)

    def test_excess_xp_does_not_jump_or_confirm_multiple_ranks(self):
        result = evaluate_rank_eligibility(progress(xp=10**60), evidence(), policy())
        self.assertEqual(result.next_rank, Rank.JUNIOR)
        self.assertEqual(result.status, RankStatus.ELIGIBLE)
        self.assertIsNone(result.current_rank)

    def test_below_exact_and_above_next_threshold(self):
        for amount, expected_status, missing in ((19, RankStatus.PENDING, 1),
                                                 (20, RankStatus.ELIGIBLE, 0),
                                                 (21, RankStatus.ELIGIBLE, 0)):
            with self.subTest(amount=amount):
                result = evaluate_rank_eligibility(progress(Rank.JUNIOR, amount), evidence(), policy())
                self.assertEqual((result.next_rank, result.status, result.missing_domain_xp),
                                 (Rank.MIDDLE, expected_status, missing))

    def test_junior_zero_domain_xp_is_pending(self):
        result = evaluate_rank_eligibility(progress(xp=0), evidence(), policy())
        self.assertEqual(result.missing_domain_xp, 10)
        self.assertEqual(result.status, RankStatus.PENDING)

    def test_max_rank_even_with_less_xp_than_current_policy(self):
        result = evaluate_rank_eligibility(progress(Rank.MAESTRO, 0), evidence(None, None), policy())
        self.assertEqual(result.status, RankStatus.MAX_RANK)
        self.assertIsNone(result.next_rank)
        self.assertEqual(result.missing_domain_xp, 0)
        self.assertEqual(result.missing_course_codes, ())
        self.assertEqual(result.missing_challenge_codes, ())
        self.assertEqual(result.unavailable_sources, ())

    def test_policy_changed_does_not_degrade_confirmed_rank(self):
        newer = policy(xp=(1000, 2000, 3000, 4000), version="synthetic-v2")
        result = evaluate_rank_eligibility(progress(Rank.SENIOR, 50), evidence(), newer)
        self.assertEqual(result.current_rank, Rank.SENIOR)
        self.assertEqual(result.next_rank, Rank.MAESTRO)
        self.assertEqual(result.missing_domain_xp, 3950)
        self.assertEqual(result.policy_version, "synthetic-v2")
        self.assertEqual(result.status, RankStatus.PENDING)

    def test_xp_is_not_consumed_or_converted_and_policy_is_identified(self):
        player = progress(Rank.MIDDLE, 29)
        p = policy(code="synthetic-new-policy", version="synthetic-v3")
        assessment = evaluate_rank_eligibility(player, evidence(), p)
        self.assertEqual(player.domain_xp_total, 29)
        self.assertEqual(assessment.missing_domain_xp, 1)
        self.assertEqual((assessment.policy_code, assessment.policy_version),
                         ("synthetic-new-policy", "synthetic-v3"))
        self.assertFalse(hasattr(assessment, "applied"))
        self.assertFalse(hasattr(assessment, "event_id"))
        self.assertFalse(hasattr(assessment, "replayed"))


class RankEducationalEvidenceTests(TestCase):
    def test_complete_xp_courses_and_challenges_eligible_and_combined_with_and(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-course-1", "synthetic-course-2")},
                   challenges={Rank.JUNIOR: ("synthetic-challenge-1",)})
        yes = evaluate_rank_eligibility(progress(), evidence(("synthetic-course-1", "synthetic-course-2"),
                                                               ("synthetic-challenge-1",)), p)
        self.assertEqual(yes.status, RankStatus.ELIGIBLE)
        self.assertEqual(yes.missing_course_codes, ())
        self.assertEqual(yes.missing_challenge_codes, ())
        no = evaluate_rank_eligibility(progress(), evidence(("synthetic-course-1",),
                                                              ("synthetic-challenge-1",)), p)
        self.assertEqual(no.status, RankStatus.PENDING)
        self.assertEqual(no.missing_course_codes, ("synthetic-course-2",))

    def test_verified_empty_distinct_from_unavailable(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-course",)})
        pending = evaluate_rank_eligibility(progress(), evidence(courses=()), p)
        unavailable = evaluate_rank_eligibility(progress(), evidence(courses=None), p)
        self.assertEqual(pending.status, RankStatus.PENDING)
        self.assertEqual(pending.missing_course_codes, ("synthetic-course",))
        self.assertEqual(pending.unavailable_sources, ())
        self.assertEqual(unavailable.status, RankStatus.EVIDENCE_UNAVAILABLE)
        self.assertEqual(unavailable.missing_course_codes, ())
        self.assertEqual(unavailable.unavailable_sources, ("courses",))

    def test_two_unavailable_sources_and_xp_shortfall(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-c",)},
                   challenges={Rank.JUNIOR: ("synthetic-r",)})
        result = evaluate_rank_eligibility(progress(xp=0), evidence(None, None), p)
        self.assertEqual(result.status, RankStatus.EVIDENCE_UNAVAILABLE)
        self.assertEqual(result.unavailable_sources, ("courses", "challenges"))
        self.assertEqual(result.missing_domain_xp, 10)
        self.assertEqual(result.missing_course_codes, ())
        self.assertEqual(result.missing_challenge_codes, ())

    def test_unavailable_wins_over_known_missing_xp_courses_and_challenges(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-c1", "synthetic-c2")},
                   challenges={Rank.JUNIOR: ("synthetic-r1",)})
        result = evaluate_rank_eligibility(progress(xp=2), evidence(("synthetic-c1",), None), p)
        self.assertEqual(result.status, RankStatus.EVIDENCE_UNAVAILABLE)
        self.assertEqual(result.missing_domain_xp, 8)
        self.assertEqual(result.missing_course_codes, ("synthetic-c2",))
        self.assertEqual(result.missing_challenge_codes, ())
        self.assertEqual(result.unavailable_sources, ("challenges",))

    def test_unavailable_challenge_but_verified_missing_course(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-c1",)},
                   challenges={Rank.JUNIOR: ("synthetic-r1",)})
        result = evaluate_rank_eligibility(progress(xp=10), evidence((), None), p)
        self.assertEqual(result.status, RankStatus.EVIDENCE_UNAVAILABLE)
        self.assertEqual(result.missing_course_codes, ("synthetic-c1",))
        self.assertEqual(result.unavailable_sources, ("challenges",))

    def test_xp_sufficient_but_verified_challenge_absent_is_pending(self):
        p = policy(challenges={Rank.JUNIOR: ("synthetic-r1", "synthetic-r2")})
        result = evaluate_rank_eligibility(progress(xp=100), evidence((), ("synthetic-r2",)), p)
        self.assertEqual(result.status, RankStatus.PENDING)
        self.assertEqual(result.missing_challenge_codes, ("synthetic-r1",))

    def test_unrequired_sources_never_block_even_when_unavailable(self):
        result = evaluate_rank_eligibility(progress(xp=10), evidence(None, None), policy())
        self.assertEqual(result.status, RankStatus.ELIGIBLE)
        self.assertEqual(result.unavailable_sources, ())

    def test_no_requirements_of_future_ranks_consulted(self):
        p = policy(courses={Rank.MAESTRO: ("synthetic-future-c",)},
                   challenges={Rank.SENIOR: ("synthetic-future-r",)})
        result = evaluate_rank_eligibility(progress(xp=1000), evidence(None, None), p)
        self.assertEqual(result.status, RankStatus.ELIGIBLE)
        self.assertEqual(result.next_rank, Rank.JUNIOR)
        self.assertEqual(result.unavailable_sources, ())

    def test_extra_verified_codes_not_considered_errors(self):
        p = policy(courses={Rank.JUNIOR: ("synthetic-required",)})
        result = evaluate_rank_eligibility(progress(), evidence(("synthetic-extra", "synthetic-required")), p)
        self.assertEqual(result.status, RankStatus.ELIGIBLE)


class RankInvalidPolicyTests(TestCase):
    def test_policy_requires_full_ordered_exactly_four_ranks(self):
        valid = policy()
        for bad in (valid.requirements[:-1],
                    (valid.requirements[0], valid.requirements[0], *valid.requirements[2:]),
                    (valid.requirements[1], valid.requirements[0], *valid.requirements[2:]),
                    (*valid.requirements, valid.requirements[-1]),
                    ("Junior", *valid.requirements[1:]),
                    (), "Junior", None, set(valid.requirements)):
            with self.subTest(bad=repr(bad)), self.assertRaises(InvalidRankPolicyError):
                RankPolicy("synthetic", "v1", "synthetic-alpha", bad)

    def test_strictly_increasing_thresholds_and_junior_positive(self):
        for xp in ((0, 20, 30, 40), (10, 10, 30, 40), (10, 20, 20, 40),
                   (10, 20, 30, 29), (10, 20, 30, 30)):
            with self.subTest(xp=xp), self.assertRaises(InvalidRankPolicyError):
                policy(xp=xp)

    def test_thresholds_must_be_exact_integer_not_bool_float_str(self):
        for value in (True, False, 3.0, "3", -1, None):
            with self.subTest(value=value), self.assertRaises(InvalidRankPolicyError):
                RankRequirement(Rank.JUNIOR, value)

    def test_reject_unknown_rank_targets_without_implicit_normalization(self):
        for rank in ("Junior", "junior", 0, None, True):
            with self.subTest(rank=rank), self.assertRaises(InvalidRankPolicyError):
                RankRequirement(rank, 10)

    def test_identifiers_and_version_required_not_coerced(self):
        for attribute in ("policy_code", "version", "specialization_code"):
            for value in ("", "   ", 1, True, None):
                with self.subTest(attribute=attribute, value=value):
                    params = dict(policy_code="synthetic", version="v1", specialization_code="synthetic-alpha",
                                  requirements=policy().requirements)
                    params[attribute] = value
                    with self.assertRaises(InvalidRankPolicyError):
                        RankPolicy(**params)

    def test_requirements_codes_reject_duplicates_and_invalid_collections(self):
        for value in (("synthetic-course", "synthetic-course"), "synthetic-course",
                      {"synthetic-course": 1}, [""], [" "], [123], [None], None):
            with self.subTest(value=repr(value)), self.assertRaises(InvalidRankPolicyError):
                RankRequirement(Rank.JUNIOR, 10, required_course_codes=value)

    def test_challenge_codes_reject_duplicates_and_invalid_values(self):
        for value in (("synthetic-c", "synthetic-c"), [True], "synthetic-challenge"):
            with self.subTest(value=value), self.assertRaises(InvalidRankPolicyError):
                RankRequirement(Rank.JUNIOR, 10, required_challenge_codes=value)

    def test_empty_requirements_allowed_on_all_ranks(self):
        p = policy()
        self.assertTrue(all(row.required_course_codes == () and
                            row.required_challenge_codes == () for row in p.requirements))

    def test_arbitrarily_large_thresholds_have_no_invented_orm_limit(self):
        big = 10**80
        p = policy(xp=(big, big + 1, big + 2, big + 3))
        result = evaluate_rank_eligibility(progress(xp=big), evidence(), p)
        self.assertEqual(result.status, RankStatus.ELIGIBLE)


class RankInvalidProgressEvidenceTests(TestCase):
    def test_invalid_progress_types(self):
        for amount in (-1, True, False, 1.1, "1", None):
            with self.subTest(amount=amount), self.assertRaises(InvalidRankProgressError):
                progress(xp=amount)
        for rank in ("Junior", "MAESTRO", 1, True, False):
            with self.subTest(rank=rank), self.assertRaises(InvalidRankProgressError):
                progress(rank)
        for specialization in (None, "", "   ", 12):
            with self.subTest(specialization=specialization), self.assertRaises(InvalidRankProgressError):
                progress(specialization=specialization)

    def test_progress_specialization_mismatch_fails_not_pending(self):
        with self.assertRaises(InvalidRankProgressError):
            evaluate_rank_eligibility(progress(specialization="synthetic-other"), evidence(), policy())

    def test_evidence_specialization_mismatch_fails_not_unavailable(self):
        with self.assertRaises(InvalidRankEvidenceError):
            evaluate_rank_eligibility(progress(), evidence(specialization="synthetic-other"), policy())

    def test_evidence_codes_reject_invalid_containers_and_duplicates(self):
        bad = ("synthetic-c", {"synthetic-c": True}, [""], [" "], [True], [1],
               ["synthetic-c", "synthetic-c"], 1.5)
        for value in bad:
            with self.subTest(value=repr(value)):
                with self.assertRaises(InvalidRankEvidenceError):
                    evidence(courses=value)
                with self.assertRaises(InvalidRankEvidenceError):
                    evidence(challenges=value)

    def test_evidence_specialization_identity_validated(self):
        for value in (None, "", "  ", 1):
            with self.subTest(value=value), self.assertRaises(InvalidRankEvidenceError):
                evidence(specialization=value)

    def test_structure_type_errors_are_separate_and_explicit(self):
        with self.assertRaises(InvalidRankProgressError):
            evaluate_rank_eligibility(None, evidence(), policy())
        with self.assertRaises(InvalidRankEvidenceError):
            evaluate_rank_eligibility(progress(), None, policy())
        with self.assertRaises(InvalidRankPolicyError):
            evaluate_rank_eligibility(progress(), evidence(), None)

    def test_max_rank_does_not_relax_structural_evidence_identity(self):
        with self.assertRaises(InvalidRankEvidenceError):
            evaluate_rank_eligibility(progress(Rank.MAESTRO), evidence(specialization="other"), policy())

    def test_verified_empty_collection_not_coerced_into_unavailable(self):
        source = evidence((), ())
        self.assertEqual(source.completed_course_codes, ())
        self.assertEqual(source.completed_challenge_codes, ())
        offline = evidence(None, None)
        self.assertIsNone(offline.completed_course_codes)
        self.assertIsNone(offline.completed_challenge_codes)


class RankPureDeterminismTests(TestCase):
    def test_assessment_rejects_invalid_diagnostic_collections(self):
        valid = evaluate_rank_eligibility(progress(), evidence(), policy())
        for field in ("missing_course_codes", "missing_challenge_codes", "unavailable_sources"):
            for value in ("course", b"course", bytearray(b"course"),
                          {"course": True}, None, 1, True):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    replace(valid, **{field: value})

    def test_assessment_rejects_invalid_or_nested_diagnostic_elements(self):
        valid = evaluate_rank_eligibility(progress(), evidence(), policy())
        for field in ("missing_course_codes", "missing_challenge_codes", "unavailable_sources"):
            for element in (None, 1, True, 1.5, b"course", "", "  ",
                            ["course"], {"course": True}, {"course"}, ("course",)):
                with self.subTest(field=field, element=element), self.assertRaises(ValueError):
                    replace(valid, **{field: [element]})

    def test_assessment_preserves_diagnostic_order_and_text(self):
        valid = evaluate_rank_eligibility(progress(), evidence(), policy())
        result = replace(
            valid, missing_course_codes=["synthetic-z", " synthetic-a "],
            missing_challenge_codes=["synthetic-r2", "synthetic-r1"],
            unavailable_sources=["courses", "challenges"],
        )
        self.assertEqual(result.missing_course_codes, ("synthetic-z", " synthetic-a "))
        self.assertEqual(result.missing_challenge_codes, ("synthetic-r2", "synthetic-r1"))
        self.assertEqual(result.unavailable_sources, ("courses", "challenges"))

    def test_assessment_defensively_copies_diagnostic_collections(self):
        courses = ["synthetic-course"]
        challenges = ["synthetic-challenge"]
        unavailable = ["courses"]
        result = RankAssessment(
            "synthetic-policy", "synthetic-v1", "synthetic-alpha",
            None, Rank.JUNIOR, RankStatus.EVIDENCE_UNAVAILABLE, 1,
            courses, challenges, unavailable,
        )
        courses.clear()
        challenges.clear()
        unavailable.clear()
        self.assertEqual(result.missing_course_codes, ("synthetic-course",))
        self.assertEqual(result.missing_challenge_codes, ("synthetic-challenge",))
        self.assertEqual(result.unavailable_sources, ("courses",))

    def test_defensive_copy_of_requirements_and_codes(self):
        courses = ["synthetic-c1", "synthetic-c2"]
        challenges = ["synthetic-r1"]
        row = RankRequirement(Rank.JUNIOR, 10, courses, challenges)
        rows = [row, RankRequirement(Rank.MIDDLE, 20), RankRequirement(Rank.SENIOR, 30),
                RankRequirement(Rank.MAESTRO, 40)]
        p = RankPolicy("synthetic", "v1", "synthetic-alpha", rows)
        original_rows = tuple(rows)
        completed = ["synthetic-c1", "synthetic-c2"]
        ev = evidence(completed, ["synthetic-r1"])
        before = evaluate_rank_eligibility(progress(), ev, p)
        courses.append("synthetic-late")
        challenges.clear()
        rows.pop()
        completed.clear()
        self.assertEqual(evaluate_rank_eligibility(progress(), ev, p), before)
        self.assertEqual(p.requirements, original_rows)
        self.assertEqual(row.required_course_codes, ("synthetic-c1", "synthetic-c2"))
        self.assertEqual(ev.completed_course_codes, ("synthetic-c1", "synthetic-c2"))

    def test_collections_canonical_across_permutations(self):
        codes = ("synthetic-a", "synthetic-b", "synthetic-c")
        for ordering in permutations(codes):
            with self.subTest(ordering=ordering):
                a = RankRequirement(Rank.JUNIOR, 10, ordering)
                b = RankRequirement(Rank.JUNIOR, 10, set(ordering))
                self.assertEqual(a, b)
                self.assertEqual(a.required_course_codes, codes)
                self.assertEqual(evidence(ordering).completed_course_codes, codes)

    def test_frozen_results_and_inputs(self):
        entities = [progress(), evidence(), policy(), policy().requirements[0]]
        entities.append(evaluate_rank_eligibility(*[entities[0], entities[1], entities[2]]))
        for obj in entities:
            field = "minimum_domain_xp" if isinstance(obj, RankRequirement) else "specialization_code"
            with self.subTest(type=type(obj)), self.assertRaises(FrozenInstanceError):
                setattr(obj, field, "tampered")
        with self.assertRaises(TypeError):
            entities[-1].missing_course_codes[0] = "tampered"

    def test_same_inputs_same_results_no_mutations(self):
        p = policy(courses={Rank.JUNIOR: ["synthetic-c1"]})
        xp = progress(xp=9)
        ev = evidence(None, None)
        before = (p, xp, ev)
        first = evaluate_rank_eligibility(xp, ev, p)
        for _ in range(30):
            self.assertEqual(evaluate_rank_eligibility(xp, ev, p), first)
        self.assertEqual((p, xp, ev), before)

    def test_two_specializations_independent_even_when_xp_matches(self):
        a, b = "synthetic-alpha", "synthetic-beta"
        p1, p2 = policy(specialization=a), policy(specialization=b)
        one = evaluate_rank_eligibility(progress(Rank.JUNIOR, 20, a), evidence(specialization=a), p1)
        two = evaluate_rank_eligibility(progress(None, 20, b), evidence(specialization=b), p2)
        self.assertEqual(one.next_rank, Rank.MIDDLE)
        self.assertEqual(two.next_rank, Rank.JUNIOR)
        self.assertEqual(one.specialization_code, a)
        self.assertEqual(two.specialization_code, b)
        with self.assertRaises(InvalidRankProgressError):
            evaluate_rank_eligibility(progress(Rank.JUNIOR, 20, a), evidence(specialization=b), p2)

    def test_no_file_or_database_operations_during_evaluation(self):
        p, xp, ev = policy(), progress(), evidence()
        with patch("builtins.open", side_effect=AssertionError("file accessed")), \
                patch("sqlite3.connect", side_effect=AssertionError("database accessed")):
            self.assertEqual(evaluate_rank_eligibility(xp, ev, p).status, RankStatus.ELIGIBLE)

    def test_module_has_no_django_imports(self):
        import ast
        from pathlib import Path
        file = Path(__file__).with_name("rank_progression.py")
        module = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                self.assertFalse(any(entry.name.startswith("django") for entry in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("django"))
