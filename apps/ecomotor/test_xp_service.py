"""Contrato S3 con catálogos y códigos exclusivamente ficticios."""

from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, progression
from .initialization_config import InitializationConfiguration
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold,
    Specialization, UserSpecializationProgress, XPEvent,
)
from .xp_service import (
    IdempotencyConflictError, InconsistentProgressError, InvalidOperationKeyError,
    InvalidProfileError, InvalidXPAmountError, InvalidXPConfigurationError,
    XPDatabaseError, XPOverflowError, grant_historical_xp,
)


# S3 solo necesita códigos; atributos deliberadamente inválidos para inicializar S2.
XP_CONFIGURATION = InitializationConfiguration(
    atk=None, def_stat=None, log_stat=None, spe=None, vel=None, int_stat=None,
    ordered_stage_codes=tuple(f"s3-test-stage-{n}" for n in range(1, 8)),
)


def create_xp_catalogs(using="default"):
    for level, xp, points in [(1, 0, 7), (2, 11, 2), (3, 23, 0), (4, 51, 5)]:
        LevelThreshold.objects.using(using).create(
            level=level, minimum_xp=xp, stat_points_awarded=points,
        )
    for ordinal, code in enumerate(XP_CONFIGURATION.ordered_stage_codes, 1):
        EvolutionStage.objects.using(using).create(
            ordinal=ordinal, code=code, name=f"Etapa ficticia {ordinal}",
            minimum_xp=(ordinal - 1) * 17,
        )


def create_xp_profile(using="default", username="s3-test-user"):
    user = get_user_model().objects.using(using).create(username=username)
    profile = UserProfileEcomotor.objects.using(using).create(
        user=user, current_level=1, current_stage_code=XP_CONFIGURATION.ordered_stage_codes[0],
    )
    CharacterStats.objects.using(using).create(
        profile=profile, atk=2, def_stat=3, log_stat=4, spe=6, vel=7, int_stat=8,
        available_points=7,
    )
    return profile


class XPServiceTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile()
        self.stats = CharacterStats.objects.get(profile=self.profile)
        self.bank = UserProfileBank.objects.create(user=self.profile.user)
        patcher = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        patcher.start()
        self.addCleanup(patcher.stop)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in
                [UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent,
                 UserSpecializationProgress, get_user_model(), UserProfileBank]]

    def assert_rejected_without_change(self, error, amount=1, key="test-operation", profile=None):
        before = self.snapshot()
        with self.assertRaises(error):
            grant_historical_xp(self.profile if profile is None else profile, amount, key)
        self.assertEqual(self.snapshot(), before)

    def test_first_grant_records_exact_snapshots_and_result(self):
        result = grant_historical_xp(self.profile, 3, "test-first")
        self.assertFalse(result.replayed)
        self.assertEqual((result.profile_id, result.amount, result.operation_key),
                         (self.profile.pk, 3, "test-first"))
        self.assertEqual((result.xp_before, result.xp_after), (0, 3))
        event = XPEvent.objects.get(pk=result.xp_event_id)
        self.assertEqual((event.profile_id, event.amount, event.xp_before, event.xp_after),
                         (self.profile.pk, 3, 0, 3))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.historical_xp_total, 3)

    def test_positive_xp_without_level_or_stage_change(self):
        result = grant_historical_xp(self.profile, 10, "test-small")
        self.assertEqual((result.level_before, result.level_after), (1, 1))
        self.assertEqual(result.stage_before_code, result.stage_after_code)
        self.assertEqual((result.crossed_levels, result.crossed_stage_codes), ((), ()))
        self.assertEqual(result.stat_points_awarded, 0)
        self.assertEqual(result.available_points_after, 7)
        self.assertFalse(EvolutionEvent.objects.exists())

    def test_exact_single_level_and_points(self):
        result = grant_historical_xp(self.profile, 11, "test-level")
        self.assertEqual((result.level_before, result.level_after), (1, 2))
        self.assertEqual(result.crossed_levels, (2,))
        self.assertEqual((result.stat_points_awarded, result.available_points_after), (2, 9))

    def test_multiple_levels_include_zero_point_level_without_level_one_points(self):
        result = grant_historical_xp(self.profile, 51, "test-multiple-levels")
        self.assertEqual(result.crossed_levels, (2, 3, 4))
        self.assertEqual((result.stat_points_awarded, result.available_points_after), (7, 14))
        self.assertEqual(result.level_after, 4)

    def test_zero_point_level_does_not_change_existing_points(self):
        grant_historical_xp(self.profile, 11, "test-level-two")
        result = grant_historical_xp(self.profile, 12, "test-level-three")
        self.assertEqual(result.crossed_levels, (3,))
        self.assertEqual((result.stat_points_awarded, result.available_points_after), (0, 9))

    def test_exact_single_stage_has_causal_event(self):
        result = grant_historical_xp(self.profile, 17, "test-stage")
        evolution = EvolutionEvent.objects.get()
        self.assertEqual(evolution.profile_id, self.profile.pk)
        self.assertEqual(evolution.xp_event_id, result.xp_event_id)
        self.assertEqual(evolution.stage.ordinal, 2)
        self.assertEqual(result.evolution_event_ids, (evolution.pk,))
        self.assertEqual(result.evolved_stage_ids, (evolution.stage_id,))
        self.assertEqual(result.crossed_stage_codes, ("s3-test-stage-2",))

    def test_all_stages_and_levels_crossed_in_functional_order(self):
        result = grant_historical_xp(self.profile, 102, "test-full-jump")
        events = list(EvolutionEvent.objects.order_by("pk"))
        self.assertEqual([row.stage.ordinal for row in events], [2, 3, 4, 5, 6, 7])
        self.assertTrue(all(row.xp_event_id == result.xp_event_id and
                            row.profile_id == self.profile.pk for row in events))
        self.assertEqual(result.evolution_event_ids, tuple(row.pk for row in events))
        self.assertEqual(result.evolved_stage_ids, tuple(row.stage_id for row in events))
        self.assertEqual(result.crossed_stage_codes, XP_CONFIGURATION.ordered_stage_codes[1:])
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.current_level, self.profile.current_stage_code),
                         (4, "s3-test-stage-7"))
        self.assertFalse(EvolutionEvent.objects.filter(stage__ordinal=1).exists())
        self.assertEqual(XPEvent.objects.count(), 1)

    def test_calculation_delegates_to_s1(self):
        with patch("apps.ecomotor.xp_service.progression.calculate_progression",
                   wraps=progression.calculate_progression) as calculate:
            grant_historical_xp(self.profile, 51, "test-delegation")
        calculate.assert_called_once()
        self.assertTrue(all(isinstance(row, progression.LevelDefinition)
                            for row in calculate.call_args.args[2]))
        self.assertTrue(all(isinstance(row, progression.StageDefinition)
                            for row in calculate.call_args.args[3]))

    def test_spent_points_are_not_reconstructed(self):
        grant_historical_xp(self.profile, 11, "test-earlier")
        CharacterStats.objects.filter(pk=self.stats.pk).update(available_points=1)
        result = grant_historical_xp(self.profile, 40, "test-after-spend")
        self.assertEqual((result.stat_points_awarded, result.available_points_after), (5, 6))

    def test_replay_preserves_every_row_and_identifiers(self):
        first = grant_historical_xp(self.profile, 51, "test-replay")
        before = self.snapshot()
        result = grant_historical_xp(self.profile, 51, "test-replay")
        self.assertTrue(result.replayed)
        for name in ["profile_id", "xp_event_id", "amount", "operation_key", "xp_before",
                     "xp_after", "evolution_event_ids", "evolved_stage_ids"]:
            self.assertEqual(getattr(result, name), getattr(first, name))
        self.assertEqual(self.snapshot(), before)

    def test_replay_unstored_historical_fields_are_none(self):
        grant_historical_xp(self.profile, 51, "test-none")
        replay = grant_historical_xp(self.profile, 51, "test-none")
        for name in ["level_before", "level_after", "stage_before_code", "stage_after_code",
                     "crossed_levels", "crossed_stage_codes", "stat_points_awarded",
                     "available_points_after"]:
            self.assertIsNone(getattr(replay, name), name)

    def test_old_replay_after_later_grant_returns_old_snapshots(self):
        first = grant_historical_xp(self.profile, 17, "test-old")
        grant_historical_xp(self.profile, 85, "test-later")
        before = self.snapshot()
        replay = grant_historical_xp(self.profile, 17, "test-old")
        self.assertEqual((replay.xp_before, replay.xp_after), (0, 17))
        self.assertEqual(replay.xp_event_id, first.xp_event_id)
        self.assertEqual(UserProfileEcomotor.objects.get().historical_xp_total, 102)
        self.assertEqual(self.snapshot(), before)

    def test_replay_ignores_changed_catalogs_and_absent_configuration(self):
        first = grant_historical_xp(self.profile, 51, "test-catalog-replay")
        LevelThreshold.objects.all().delete()
        EvolutionStage.objects.filter(ordinal=2).update(code="test-renamed", minimum_xp=999)
        before = self.snapshot()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                CaptureQueriesContext(connection) as queries:
            replay = grant_historical_xp(self.profile, 51, "test-catalog-replay")
        self.assertEqual(replay.evolved_stage_ids, first.evolved_stage_ids)
        self.assertIsNone(replay.crossed_stage_codes)
        self.assertEqual(self.snapshot(), before)
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn('from "ecomotor_evolutionstage"', sql)
        self.assertNotIn('from "ecomotor_levelthreshold"', sql)
        self.assertFalse(any(row["sql"].lstrip().upper().startswith(
            ("INSERT ", "UPDATE ", "DELETE ")) for row in queries))

    def test_same_key_different_amount_is_conflict_without_writes(self):
        grant_historical_xp(self.profile, 3, "test-conflict")
        self.assert_rejected_without_change(IdempotencyConflictError, 4, "test-conflict")

    def test_same_key_is_local_to_profile(self):
        other = create_xp_profile(username="s3-test-other")
        first = grant_historical_xp(self.profile, 3, "test-shared")
        second = grant_historical_xp(other, 4, "test-shared")
        self.assertNotEqual(first.xp_event_id, second.xp_event_id)
        self.assertEqual(XPEvent.objects.count(), 2)

    def test_invalid_amounts_do_not_write(self):
        for amount in [0, -1, True, False, 1.0, "2", None]:
            with self.subTest(amount=amount):
                self.assert_rejected_without_change(InvalidXPAmountError, amount)

    def test_invalid_keys_do_not_write(self):
        for key in ["", "x"*256, 3, True, b"key", None]:
            with self.subTest(key=key):
                self.assert_rejected_without_change(InvalidOperationKeyError, key=key)

    def test_maximum_key_and_exact_identity_without_trimming(self):
        result = grant_historical_xp(self.profile, 1, "x"*255)
        self.assertEqual(result.operation_key, "x"*255)
        first = grant_historical_xp(self.profile, 1, " test-key ")
        second = grant_historical_xp(self.profile, 1, "test-key")
        self.assertNotEqual(first.xp_event_id, second.xp_event_id)

    def test_unsaved_or_wrong_profile_is_rejected(self):
        for profile in [None, object(), self.profile.pk, UserProfileEcomotor(),
                        UserProfileEcomotor(pk=self.profile.pk)]:
            before = self.snapshot()
            with self.subTest(profile=type(profile)), self.assertRaises(InvalidProfileError):
                grant_historical_xp(profile, 1, "test-invalid-profile")
            self.assertEqual(self.snapshot(), before)

    def test_deleted_profile_is_rejected(self):
        stale = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        self.profile.delete()
        self.assert_rejected_without_change(InvalidProfileError, profile=stale)

    def test_profile_without_stats_is_not_initialized_or_repaired(self):
        self.stats.delete()
        self.assert_rejected_without_change(InconsistentProgressError)

    def test_invalid_profile_structure_is_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code="x"*33)
        self.assert_rejected_without_change(InconsistentProgressError)

    def test_invalid_stats_structure_is_rejected(self):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_characterstats SET atk=%s WHERE id=%s",
                           ["test-invalid", self.stats.pk])
        self.assert_rejected_without_change(InconsistentProgressError)

    def test_fractional_legacy_xp_or_stats_are_not_silently_normalized(self):
        for table, field, pk in [
            ("users_userprofileecomotor", "historical_xp_total", self.profile.pk),
            ("ecomotor_characterstats", "atk", self.stats.pk),
        ]:
            with self.subTest(field=field), connection.cursor() as cursor:
                cursor.execute(f"UPDATE {table} SET {field}=%s WHERE id=%s", [1.5, pk])
                self.assert_rejected_without_change(InconsistentProgressError)
                cursor.execute(f"UPDATE {table} SET {field}=%s WHERE id=%s", [0, pk])

    def test_incoherent_level_or_stage_is_rejected_without_recalculation(self):
        for fields in [{"current_level": 2}, {"current_stage_code": "test-wrong-stage"}]:
            UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
                current_level=1, current_stage_code="s3-test-stage-1",
            )
            UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(**fields)
            with self.subTest(fields=fields):
                self.assert_rejected_without_change(InconsistentProgressError)

    def test_missing_or_wrong_configuration_is_rejected(self):
        for config in [None, object()]:
            with self.subTest(config=config), patch.object(
                initialization_config, "INITIAL_CONFIGURATION", config,
            ):
                self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_only_codes_are_required_not_initial_stats(self):
        self.assertIsNone(XP_CONFIGURATION.atk)
        self.assertFalse(grant_historical_xp(self.profile, 1, "test-only-codes").replayed)

    def test_invalid_stage_mapping_is_rejected(self):
        for codes in [(), ("x",)*7, tuple(range(7)), ("",)*7, ("x"*33,)*7,
                      tuple(reversed(XP_CONFIGURATION.ordered_stage_codes))]:
            with self.subTest(codes=codes), patch.object(
                initialization_config, "INITIAL_CONFIGURATION",
                replace(XP_CONFIGURATION, ordered_stage_codes=codes),
            ):
                self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_empty_level_catalog_is_rejected(self):
        LevelThreshold.objects.all().delete()
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_gapped_levels_are_rejected(self):
        LevelThreshold.objects.filter(level=2).delete()
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_initial_or_nonincreasing_level_thresholds_are_rejected(self):
        LevelThreshold.objects.filter(level=1).update(minimum_xp=1)
        self.assert_rejected_without_change(InvalidXPConfigurationError)
        LevelThreshold.objects.filter(level=1).update(minimum_xp=0)
        LevelThreshold.objects.filter(level=2).update(minimum_xp=0)
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_empty_or_incomplete_stage_catalog_is_rejected(self):
        EvolutionStage.objects.filter(ordinal=7).delete()
        self.assert_rejected_without_change(InvalidXPConfigurationError)
        EvolutionStage.objects.all().delete()
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_nonincreasing_stage_thresholds_are_rejected(self):
        EvolutionStage.objects.filter(ordinal=2).update(minimum_xp=0)
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_stage_mapping_is_not_derived_from_catalog(self):
        EvolutionStage.objects.filter(ordinal=1).update(code="test-unknown")
        self.assert_rejected_without_change(InvalidXPConfigurationError)

    def test_amount_overflow_is_controlled(self):
        self.assert_rejected_without_change(XPOverflowError, 2**80)

    def test_accumulated_xp_overflow_is_controlled(self):
        upper = connection.ops.integer_field_range("PositiveBigIntegerField")[1]
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            historical_xp_total=upper, current_level=4, current_stage_code="s3-test-stage-7",
        )
        self.assert_rejected_without_change(XPOverflowError)

    def test_largest_representable_xp_has_no_invented_game_limit(self):
        upper = connection.ops.integer_field_range("PositiveBigIntegerField")[1]
        result = grant_historical_xp(self.profile, upper, "test-technical-maximum")
        self.assertEqual(result.xp_after, upper)
        self.assertEqual(result.level_after, 4)

    def test_points_overflow_is_controlled(self):
        upper = connection.ops.integer_field_range("PositiveIntegerField")[1]
        CharacterStats.objects.filter(pk=self.stats.pk).update(available_points=upper)
        self.assert_rejected_without_change(XPOverflowError, 11)

    def test_causal_profile_mismatch_is_rejected_for_new_grant_and_replay(self):
        other = create_xp_profile(username="s3-test-causal-other")
        event = XPEvent.objects.create(profile=self.profile, amount=1, xp_before=0,
                                       xp_after=1, operation_key="test-cause")
        EvolutionEvent.objects.create(profile=other, xp_event=event,
                                      stage=EvolutionStage.objects.get(ordinal=2))
        self.assert_rejected_without_change(InconsistentProgressError, 1, "test-cause")
        self.assert_rejected_without_change(InconsistentProgressError, 1, "test-new-cause")

    def test_already_recorded_crossed_stage_is_rejected(self):
        event = XPEvent.objects.create(profile=self.profile, amount=1, xp_before=0,
                                       xp_after=1, operation_key="test-premature")
        EvolutionEvent.objects.create(profile=self.profile, xp_event=event,
                                      stage=EvolutionStage.objects.get(ordinal=2))
        self.assert_rejected_without_change(InconsistentProgressError, 17)

    def test_replay_with_snapshot_ahead_of_current_xp_is_rejected(self):
        grant_historical_xp(self.profile, 3, "test-ahead")
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(historical_xp_total=0)
        self.assert_rejected_without_change(InconsistentProgressError, 3, "test-ahead")

    def test_fractional_historical_snapshots_are_rejected_without_rewriting(self):
        event_id = grant_historical_xp(self.profile, 3, "test-legacy-snapshot").xp_event_id
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ecomotor_xpevent SET amount=1, xp_before=1.5, xp_after=2.5 WHERE id=%s",
                [event_id],
            )
        self.assert_rejected_without_change(InconsistentProgressError, 1, "test-legacy-snapshot")

    def test_failure_after_first_evolution_rolls_back_all_writes(self):
        original_save = EvolutionEvent.save
        calls = []

        def fail_second(instance, *args, **kwargs):
            calls.append(instance.stage_id)
            if len(calls) == 2:
                raise IntegrityError("test evolution failure")
            return original_save(instance, *args, **kwargs)

        with patch.object(EvolutionEvent, "save", fail_second):
            self.assert_rejected_without_change(XPDatabaseError, 51)
        self.assertEqual(len(calls), 2)

    def test_profile_update_failure_rolls_back_events(self):
        with patch.object(UserProfileEcomotor, "save", side_effect=IntegrityError("test profile failure")):
            self.assert_rejected_without_change(XPDatabaseError, 51)

    def test_stats_update_failure_rolls_back_profile_and_events(self):
        with patch.object(CharacterStats, "save", side_effect=IntegrityError("test stats failure")):
            before = self.snapshot()
            with self.assertRaises(XPDatabaseError) as caught:
                grant_historical_xp(self.profile, 51, "test-stats-failure")
            self.assertIsInstance(caught.exception.__cause__, IntegrityError)
            self.assertEqual(self.snapshot(), before)
        self.assertFalse(grant_historical_xp(self.profile, 51, "test-stats-failure").replayed)

    def test_base_stats_specialization_users_bank_and_catalogs_are_preserved(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            active_specialization_code="test-active",
        )
        models = [get_user_model(), UserProfileBank, UserSpecializationProgress,
                  LevelThreshold, EvolutionStage, Specialization]
        before = [list(model.objects.values()) for model in models]
        base_stats = tuple(getattr(self.stats, name) for name in
                           ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat"])
        grant_historical_xp(self.profile, 102, "test-preserve")
        self.assertEqual([list(model.objects.values()) for model in models], before)
        self.stats.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(tuple(getattr(self.stats, name) for name in
                               ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat"]), base_stats)
        self.assertEqual(self.profile.active_specialization_code, "test-active")

    def test_result_is_immutable(self):
        result = grant_historical_xp(self.profile, 17, "test-frozen")
        with self.assertRaises(FrozenInstanceError):
            result.xp_after = 999
        self.assertIsInstance(result.evolution_event_ids, tuple)
        self.assertIsInstance(result.crossed_levels, tuple)
