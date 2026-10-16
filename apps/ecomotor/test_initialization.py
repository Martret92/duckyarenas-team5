"""S2-A con configuración ficticia explícita; ninguna fixture es dato maestro."""

from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test import TestCase

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config
from .initialization import (
    InitializationDatabaseError,
    InconsistentInitializationStateError,
    InvalidInitializationConfigError,
    InvalidUserError,
    ensure_ecomotor_initialized,
)
from .initialization_config import InitializationConfiguration
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold,
    Specialization, UserSpecializationProgress, XPEvent,
)


TEST_CONFIGURATION = InitializationConfiguration(
    atk=2, def_stat=-3, log_stat=4, spe=6, vel=7, int_stat=8,
    ordered_stage_codes=tuple(f"test-stage-{i}" for i in range(1, 8)),
)


def create_catalogs(using="default"):
    for level, xp, points in [(1, 0, 7), (2, 11, 3), (3, 23, 0)]:
        LevelThreshold.objects.using(using).create(
            level=level, minimum_xp=xp, stat_points_awarded=points,
        )
    for ordinal, code in enumerate(TEST_CONFIGURATION.ordered_stage_codes, 1):
        EvolutionStage.objects.using(using).create(
            code=code, name=f"Etapa ficticia {ordinal}", ordinal=ordinal,
            minimum_xp=(ordinal - 1) * 17,
        )


class InitializationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="initialization-test")
        self.bank = UserProfileBank.objects.create(user=self.user)
        create_catalogs()
        self.config_patch = patch.object(
            initialization_config, "INITIAL_CONFIGURATION", TEST_CONFIGURATION,
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def assert_empty_progress(self):
        for model in [UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent,
                      UserSpecializationProgress]:
            self.assertEqual(model.objects.count(), 0)

    def test_first_call_creates_exact_profile_and_stats(self):
        result = ensure_ecomotor_initialized(self.user)
        self.assertTrue(result.created)
        profile = UserProfileEcomotor.objects.get(pk=result.profile_id)
        stats = CharacterStats.objects.get(pk=result.character_stats_id)
        self.assertEqual(profile.user_id, self.user.pk)
        self.assertEqual((profile.historical_xp_total, profile.current_level,
                          profile.current_stage_code, profile.active_specialization_code),
                         (0, 1, "test-stage-1", None))
        self.assertEqual(stats.profile_id, profile.pk)
        self.assertEqual(tuple(getattr(stats, name) for name in
                              ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat"]),
                         (2, -3, 4, 6, 7, 8))
        self.assertEqual(stats.available_points, 7)

    def test_initial_points_come_from_level_one_including_zero(self):
        LevelThreshold.objects.filter(level=1).update(stat_points_awarded=0)
        result = ensure_ecomotor_initialized(self.user)
        self.assertEqual(CharacterStats.objects.get(pk=result.character_stats_id).available_points, 0)

    def test_retry_returns_same_identifiers_without_duplicates(self):
        first = ensure_ecomotor_initialized(self.user)
        second = ensure_ecomotor_initialized(self.user)
        self.assertFalse(second.created)
        self.assertEqual((first.profile_id, first.character_stats_id),
                         (second.profile_id, second.character_stats_id))
        self.assertEqual(UserProfileEcomotor.objects.count(), 1)
        self.assertEqual(CharacterStats.objects.count(), 1)

    def test_retry_preserves_evolved_progress_stats_and_points(self):
        first = ensure_ecomotor_initialized(self.user)
        UserProfileEcomotor.objects.filter(pk=first.profile_id).update(
            historical_xp_total=999, current_level=12, current_stage_code="test-later-stage",
            active_specialization_code="test-specialization",
        )
        CharacterStats.objects.filter(pk=first.character_stats_id).update(atk=37, available_points=41)
        before_profile = list(UserProfileEcomotor.objects.values())
        before_stats = list(CharacterStats.objects.values())
        result = ensure_ecomotor_initialized(self.user)
        self.assertFalse(result.created)
        self.assertEqual(list(UserProfileEcomotor.objects.values()), before_profile)
        self.assertEqual(list(CharacterStats.objects.values()), before_stats)

    def test_retry_ignores_changed_or_absent_initial_configuration_and_catalogs(self):
        first = ensure_ecomotor_initialized(self.user)
        LevelThreshold.objects.all().delete()
        EvolutionStage.objects.all().delete()
        for config in [None, object(), replace(TEST_CONFIGURATION, atk=99)]:
            with self.subTest(config=config), patch.object(
                initialization_config, "INITIAL_CONFIGURATION", config,
            ):
                result = ensure_ecomotor_initialized(self.user)
                self.assertFalse(result.created)
                self.assertEqual(result.character_stats_id, first.character_stats_id)
                self.assertEqual(CharacterStats.objects.get().atk, 2)
                self.assertEqual(CharacterStats.objects.get().available_points, 7)

    def test_invalid_and_unsaved_users_are_rejected(self):
        for user in [None, object(), self.user.pk, get_user_model()(username="unsaved"),
                     get_user_model()(pk=self.user.pk, username="unsaved-with-id")]:
            with self.subTest(user=type(user)), self.assertRaises(InvalidUserError):
                ensure_ecomotor_initialized(user)
        self.assert_empty_progress()

    def test_deleted_user_is_rejected(self):
        stale_user = get_user_model().objects.get(pk=self.user.pk)
        self.user.delete()
        with self.assertRaises(InvalidUserError):
            ensure_ecomotor_initialized(stale_user)
        self.assert_empty_progress()

    def test_missing_and_wrong_configuration_are_rejected_without_writes(self):
        for config in [None, object()]:
            with self.subTest(config=config), patch.object(
                initialization_config, "INITIAL_CONFIGURATION", config,
            ), self.assertRaises(InvalidInitializationConfigError):
                ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_non_integer_stats_and_technical_overflow_are_rejected(self):
        for value in [True, 1.5, "2", None, 2**80]:
            with self.subTest(value=value), patch.object(
                initialization_config, "INITIAL_CONFIGURATION", replace(TEST_CONFIGURATION, atk=value),
            ), self.assertRaises(InvalidInitializationConfigError):
                ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_invalid_configured_stage_codes_are_rejected(self):
        for codes in [(), ("x",)*7, ("",)*7, tuple(range(7)), ("x"*33,)*7]:
            with self.subTest(codes=codes), patch.object(
                initialization_config, "INITIAL_CONFIGURATION",
                replace(TEST_CONFIGURATION, ordered_stage_codes=codes),
            ), self.assertRaises(InvalidInitializationConfigError):
                ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_empty_level_catalog_is_rejected(self):
        LevelThreshold.objects.all().delete()
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_level_gap_is_rejected(self):
        LevelThreshold.objects.filter(level=2).delete()
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_nonzero_initial_level_threshold_is_rejected(self):
        LevelThreshold.objects.filter(level=1).update(minimum_xp=1)
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_nonincreasing_level_threshold_is_rejected(self):
        LevelThreshold.objects.filter(level=2).update(minimum_xp=0)
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_empty_or_incomplete_stage_catalog_is_rejected(self):
        EvolutionStage.objects.filter(ordinal=7).delete()
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        EvolutionStage.objects.all().delete()
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_nonzero_initial_stage_threshold_is_rejected(self):
        EvolutionStage.objects.filter(ordinal=1).update(minimum_xp=1)
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_nonincreasing_stage_threshold_is_rejected(self):
        EvolutionStage.objects.filter(ordinal=2).update(minimum_xp=0)
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_stage_correspondence_is_not_inferred_from_rows(self):
        EvolutionStage.objects.filter(ordinal=1).update(code="test-unapproved-code")
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()

    def test_partial_profile_is_rejected_without_repair(self):
        profile = UserProfileEcomotor.objects.create(
            user=self.user, current_level=2, current_stage_code="test-stage-2", historical_xp_total=31,
        )
        before = list(UserProfileEcomotor.objects.values())
        with self.assertRaises(InconsistentInitializationStateError):
            ensure_ecomotor_initialized(self.user)
        self.assertEqual(list(UserProfileEcomotor.objects.values()), before)
        self.assertFalse(CharacterStats.objects.filter(profile=profile).exists())

    def test_structurally_invalid_existing_profile_is_rejected(self):
        result = ensure_ecomotor_initialized(self.user)
        # SQLite CharField no impone longitud en BD; estado legacy estructural real.
        UserProfileEcomotor.objects.filter(pk=result.profile_id).update(current_stage_code="x"*33)
        before = list(UserProfileEcomotor.objects.values())
        with self.assertRaises(InconsistentInitializationStateError):
            ensure_ecomotor_initialized(self.user)
        self.assertEqual(list(UserProfileEcomotor.objects.values()), before)

    def test_statistics_creation_failure_rolls_back_profile(self):
        with patch("apps.ecomotor.initialization.CharacterStats.objects.using") as manager:
            manager.return_value.create.side_effect = IntegrityError("test stats failure")
            with self.assertRaises(InitializationDatabaseError) as caught:
                ensure_ecomotor_initialized(self.user)
        self.assertIsInstance(caught.exception.__cause__, IntegrityError)
        self.assert_empty_progress()
        self.assertTrue(ensure_ecomotor_initialized(self.user).created)

    def test_structurally_invalid_existing_stats_are_rejected_without_repair(self):
        result = ensure_ecomotor_initialized(self.user)
        # SQLite no STRICT permite texto legacy en una columna INTEGER.
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE ecomotor_characterstats SET atk = %s WHERE id = %s",
                ["legacy-invalid", result.character_stats_id],
            )
        before = list(CharacterStats.objects.values())
        with self.assertRaises(InconsistentInitializationStateError):
            ensure_ecomotor_initialized(self.user)
        self.assertEqual(list(CharacterStats.objects.values()), before)

    def test_only_profile_and_stats_are_created_without_modifying_user_or_bank(self):
        before_user = list(get_user_model().objects.values())
        before_bank = list(UserProfileBank.objects.values())
        before_catalogs = [list(model.objects.values()) for model in
                           [LevelThreshold, EvolutionStage, Specialization]]
        ensure_ecomotor_initialized(self.user)
        self.assertEqual(list(get_user_model().objects.values()), before_user)
        self.assertEqual(list(UserProfileBank.objects.values()), before_bank)
        self.assertEqual([list(model.objects.values()) for model in
                          [LevelThreshold, EvolutionStage, Specialization]], before_catalogs)
        for model in [XPEvent, EvolutionEvent, UserSpecializationProgress]:
            self.assertEqual(model.objects.count(), 0)

    def test_result_and_configuration_are_immutable(self):
        result = ensure_ecomotor_initialized(self.user)
        with self.assertRaises(FrozenInstanceError):
            result.created = False
        with self.assertRaises(FrozenInstanceError):
            TEST_CONFIGURATION.atk = 99
        codes = list(TEST_CONFIGURATION.ordered_stage_codes)
        config = replace(TEST_CONFIGURATION, ordered_stage_codes=codes)
        codes[0] = "tampered"
        self.assertEqual(config.ordered_stage_codes[0], "test-stage-1")

    def test_default_configuration_is_absent(self):
        self.config_patch.stop()
        self.assertIsNone(initialization_config.INITIAL_CONFIGURATION)
        with self.assertRaises(InvalidInitializationConfigError):
            ensure_ecomotor_initialized(self.user)
        self.assert_empty_progress()
