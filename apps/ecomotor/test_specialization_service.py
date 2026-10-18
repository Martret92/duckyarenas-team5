"""S11-A-01/02 con configuraciones y especializaciones exclusivamente sintéticas."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as IsolatedTestCase
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import OperationalError, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, Specialization,
    StatAllocationEvent, UserSpecializationProgress, XPEvent,
)
from .specialization_service import (
    InconsistentSpecializationStateError, IneligibleSpecializationStageError,
    InvalidSpecializationCodeError, InvalidSpecializationConfigurationError,
    InvalidSpecializationProfileError, SpecializationConflictError, SpecializationDatabaseError,
    select_initial_specialization,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class SpecializationServiceTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s11-test-user")
        self.other = create_xp_profile(username="s11-test-other")
        UserProfileBank.objects.create(user=self.profile.user)
        self.alpha = Specialization.objects.create(code="s11-test-alpha", name="Especialidad ficticia A")
        self.beta = Specialization.objects.create(code="s11-test-beta", name="Especialidad ficticia B")
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s11-test-reach-actual")

    def select(self, code=None, profile=None):
        return select_initial_specialization(self.profile if profile is None else profile,
                                             self.alpha.code if code is None else code)

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, StatAllocationEvent, UserSpecializationProgress,
            Specialization, EvolutionStage, LevelThreshold,
        )]

    def reject(self, error, code=None, profile=None):
        before = self.snapshot()
        with self.assertRaises(error):
            self.select(code, profile)
        self.assertEqual(self.snapshot(), before)

    def test_first_selection_persists_code_and_zero_domain_xp_together(self):
        result = self.select()
        self.assertTrue(result.created)
        self.assertEqual((result.profile_id, result.specialization_id, result.specialization_code),
                         (self.profile.pk, self.alpha.pk, self.alpha.code))
        current = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        progress = UserSpecializationProgress.objects.get(pk=result.progress_id)
        self.assertEqual(current.active_specialization_code, self.alpha.code)
        self.assertEqual((progress.profile_id, progress.specialization_id, progress.domain_xp_total),
                         (self.profile.pk, self.alpha.pk, 0))
        self.assertEqual(UserSpecializationProgress.objects.count(), 1)

    def test_first_selection_without_level_catalog(self):
        LevelThreshold.objects.all().delete()
        self.assertTrue(self.select().created)

    def test_first_selection_with_invalid_level_catalog(self):
        LevelThreshold.objects.filter(level=2).update(minimum_xp=0)
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_level=42)
        self.assertTrue(self.select().created)
        self.assertEqual(UserProfileEcomotor.objects.get(pk=self.profile.pk).current_level, 42)

    def test_only_stage_catalog_and_codes_required_not_initial_stats(self):
        self.assertIsNone(XP_CONFIGURATION.atk)
        with CaptureQueriesContext(connection) as queries:
            self.select()
        sql = " ".join(row["sql"].lower() for row in queries)
        for table in ("ecomotor_levelthreshold", "auth_user", "users_userprofilebank"):
            self.assertNotIn('"' + table + '"', sql)

    def test_before_actual_rejected(self):
        self.reject(IneligibleSpecializationStageError, profile=self.other)

    def test_exact_actual_threshold_accepted(self):
        self.assertEqual(UserProfileEcomotor.objects.get(pk=self.profile.pk).historical_xp_total, 102)
        self.assertTrue(self.select().created)

    def test_stage_incompatible_with_xp_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(current_stage_code=XP_CONFIGURATION.ordered_stage_codes[0])
        self.reject(InconsistentSpecializationStateError)

    def test_missing_or_invalid_configuration_rejected(self):
        invalid = (None, object(), replace(XP_CONFIGURATION, ordered_stage_codes=("duplicate",) * 7),
                   replace(XP_CONFIGURATION, ordered_stage_codes=("short",)),
                   replace(XP_CONFIGURATION, ordered_stage_codes=(1, 2, 3, 4, 5, 6, 7)))
        for config in invalid:
            with self.subTest(config=config), patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
                self.reject(InvalidSpecializationConfigurationError)

    def test_incomplete_stage_catalog_rejected(self):
        EvolutionStage.objects.filter(ordinal=1).delete()
        self.reject(InvalidSpecializationConfigurationError)

    def test_invalid_stage_thresholds_rejected(self):
        EvolutionStage.objects.filter(ordinal=2).update(minimum_xp=0)
        self.reject(InvalidSpecializationConfigurationError)

    def test_incompatible_stage_codes_rejected(self):
        EvolutionStage.objects.filter(ordinal=7).update(code="s11-changed-code")
        self.reject(InvalidSpecializationConfigurationError)

    def test_invalid_codes_and_nonexistent_specialization(self):
        for code in ("", 1, True, 1.0, [], "x" * 33, "s11-missing"):
            with self.subTest(code=code):
                before = self.snapshot()
                with self.assertRaises(InvalidSpecializationCodeError):
                    select_initial_specialization(self.profile, code)
                self.assertEqual(self.snapshot(), before)

    def test_no_silent_case_space_or_alias_normalization(self):
        for code in (self.alpha.code.upper(), " " + self.alpha.code, self.alpha.code + " "):
            with self.subTest(code=code):
                self.reject(InvalidSpecializationCodeError, code)

    def test_invalid_or_unpersisted_profile(self):
        for profile in (None, object(), UserProfileEcomotor(), True):
            with self.subTest(profile=profile), self.assertRaises(InvalidSpecializationProfileError):
                select_initial_specialization(profile, self.alpha.code)
        invalid = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        for pk in (True, "1", -1, 2**64):
            invalid.pk = pk
            with self.subTest(pk=pk), self.assertRaises(InvalidSpecializationProfileError):
                select_initial_specialization(invalid, self.alpha.code)

    def test_deleted_profile_rejected(self):
        stale = UserProfileEcomotor.objects.get(pk=self.other.pk)
        self.other.delete()
        self.reject(InvalidSpecializationProfileError, profile=stale)

    def test_missing_character_stats_rejected_without_repair(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        self.reject(InconsistentSpecializationStateError)

    def test_legacy_fractional_stats_rejected_without_conversion(self):
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_characterstats SET atk = 2.5 WHERE profile_id = %s", [self.profile.pk])
        self.reject(InconsistentSpecializationStateError)

    def test_invalid_persisted_profile_codes_rejected(self):
        for field in ("current_stage_code", "active_specialization_code"):
            with self.subTest(field=field):
                UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(**{field: "x" * 33})
                self.reject(InconsistentSpecializationStateError)
                UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(**{
                    field: XP_CONFIGURATION.ordered_stage_codes[6] if field == "current_stage_code" else None,
                })

    def test_invalid_persisted_numeric_fields_rejected(self):
        for table, field, value in (("users_userprofileecomotor", "current_level", 0),
                                    ("users_userprofileecomotor", "historical_xp_total", -1),
                                    ("ecomotor_characterstats", "available_points", -1)):
            # Identificadores fijos de test, sin contenido externo.
            column = "id" if table.startswith("users_") else "profile_id"
            with self.subTest(field=field), connection.cursor() as cursor:
                cursor.execute(f"SELECT {field} FROM {table} WHERE {column} = %s", [self.profile.pk])
                original = cursor.fetchone()[0]
                cursor.execute("PRAGMA ignore_check_constraints = ON")
                try:
                    cursor.execute(f"UPDATE {table} SET {field} = %s WHERE {column} = %s", [value, self.profile.pk])
                    self.reject(InconsistentSpecializationStateError)
                    cursor.execute(f"UPDATE {table} SET {field} = %s WHERE {column} = %s", [original, self.profile.pk])
                finally:
                    cursor.execute("PRAGMA ignore_check_constraints = OFF")

    def test_repetition_same_ids_without_business_writes_preserves_domain_xp(self):
        first = self.select()
        UserSpecializationProgress.objects.filter(pk=first.progress_id).update(domain_xp_total=345)
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            repeated = self.select()
        self.assertFalse(repeated.created)
        self.assertEqual(replace(repeated, created=True), first)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(any(row["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for row in queries))

    def test_repetition_without_configuration_catalogs_or_current_eligibility(self):
        first = self.select()
        EvolutionEvent.objects.all().delete()
        EvolutionStage.objects.all().delete()
        LevelThreshold.objects.all().delete()
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            historical_xp_total=0, current_level=17, current_stage_code="s11-changed-stage",
        )
        before = self.snapshot()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                patch("apps.ecomotor.specialization_service.progression.resolve_stage", side_effect=AssertionError), \
                CaptureQueriesContext(connection) as queries:
            repeated = self.select()
        self.assertEqual(repeated.progress_id, first.progress_id)
        self.assertFalse(repeated.created)
        self.assertEqual(self.snapshot(), before)
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn("ecomotor_evolutionstage", sql)
        self.assertNotIn("ecomotor_levelthreshold", sql)

    def test_repetition_after_modified_catalog_configuration(self):
        self.select()
        EvolutionStage.objects.filter(ordinal=7).update(minimum_xp=99999)
        config = replace(XP_CONFIGURATION, ordered_stage_codes=("invalid",))
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
            self.assertFalse(self.select().created)

    def test_different_code_conflict_even_without_configuration(self):
        self.select()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None):
            self.reject(SpecializationConflictError, self.beta.code)

    def test_progress_without_active_selection_rejected(self):
        UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.alpha)
        self.reject(InconsistentSpecializationStateError)

    def test_active_selection_without_progress_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(active_specialization_code=self.alpha.code)
        self.reject(InconsistentSpecializationStateError)

    def test_active_selection_with_incompatible_progress_rejected(self):
        self.select()
        UserSpecializationProgress.objects.filter(profile=self.profile).update(specialization=self.beta)
        self.reject(InconsistentSpecializationStateError)
        UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.alpha)
        self.assertFalse(self.select().created)

    def test_multiple_coherent_progress_preserved_and_repeat_without_configuration(self):
        first = self.select()
        UserSpecializationProgress.objects.filter(pk=first.progress_id).update(domain_xp_total=123)
        UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.beta, domain_xp_total=456)
        before = self.snapshot()
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                CaptureQueriesContext(connection) as queries:
            repeated = self.select()
            with self.assertRaises(SpecializationConflictError):
                self.select(self.beta.code)
        self.assertEqual(repeated.progress_id, first.progress_id)
        self.assertFalse(repeated.created)
        self.assertEqual(self.snapshot(), before)
        sql = " ".join(row["sql"].lower() for row in queries)
        self.assertNotIn("ecomotor_evolutionstage", sql)
        self.assertFalse(any(row["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for row in queries))

    def test_inactive_progress_is_also_validated(self):
        self.select()
        inactive = UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.beta)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_userspecializationprogress SET domain_xp_total = 0.5 WHERE id = %s",
                           [inactive.pk])
        self.reject(InconsistentSpecializationStateError)

    def test_multiple_rows_without_active_progress_still_rejected(self):
        self.select()
        UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.beta)
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(active_specialization_code="s11-missing-active")
        self.reject(InconsistentSpecializationStateError)

    def test_progress_owned_by_another_profile_does_not_complete_selection(self):
        first = self.select()
        UserSpecializationProgress.objects.filter(pk=first.progress_id).update(profile=self.other)
        self.reject(InconsistentSpecializationStateError)
        self.reject(InconsistentSpecializationStateError, profile=self.other)

    def test_missing_referenced_specialization_rejected(self):
        self.select()
        with patch("apps.ecomotor.specialization_service.Specialization.objects.using") as manager:
            manager.return_value.filter.return_value.first.return_value = None
            self.reject(InconsistentSpecializationStateError)

    def test_invalid_domain_xp_rejected(self):
        result = self.select()
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_userspecializationprogress SET domain_xp_total = 0.5 WHERE id = %s",
                           [result.progress_id])
        self.reject(InconsistentSpecializationStateError)

    def test_invalid_specialization_row_rejected(self):
        Specialization.objects.filter(pk=self.alpha.pk).update(name="x" * 101)
        self.reject(InconsistentSpecializationStateError)

    def test_rollback_if_progress_creation_fails(self):
        error = OperationalError("s11-test-create-failure")
        with patch.object(UserSpecializationProgress, "save", side_effect=error):
            self.reject(SpecializationDatabaseError)

    def test_rollback_after_profile_write_and_database_cause(self):
        original = UserProfileEcomotor.save
        error = OperationalError("s11-test-after-write")
        def fail(instance, *args, **kwargs):
            original(instance, *args, **kwargs)
            raise error
        before = self.snapshot()
        with patch.object(UserProfileEcomotor, "save", fail), self.assertRaises(SpecializationDatabaseError) as caught:
            self.select()
        self.assertIs(caught.exception.__cause__, error)
        self.assertEqual(self.snapshot(), before)

    def test_programming_error_not_hidden(self):
        with patch.object(UserSpecializationProgress, "save", side_effect=RuntimeError("s11-test-bug")):
            self.reject(RuntimeError)

    def test_only_selection_and_progress_change_no_external_effects(self):
        before = self.snapshot()
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                patch("apps.ecomotor.stat_allocation.allocate_stat_points", side_effect=AssertionError), \
                patch("apps.ecomotor.reward_rules.evaluate_reward", side_effect=AssertionError):
            self.select()
        after = self.snapshot()
        for index in range(len(before)):
            if index not in (2, 7):
                self.assertEqual(before[index], after[index])
        prior, current = before[2][0].copy(), after[2][0].copy()
        prior.pop("active_specialization_code")
        current.pop("active_specialization_code")
        self.assertEqual(prior, current)

    def test_stale_input_is_reloaded_and_user_identity_is_opaque(self):
        self.profile.current_stage_code = ""
        self.profile.historical_xp_total = -1
        current = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        current.user_id = UUID("12345678-1234-5678-1234-567812345678")
        with patch("apps.ecomotor.specialization_service.UserProfileEcomotor.objects.using") as manager:
            manager.return_value.filter.return_value.first.return_value = current
            result = self.select()
        self.assertTrue(result.created)
        self.assertEqual(UserProfileEcomotor.objects.get(pk=self.profile.pk).active_specialization_code, self.alpha.code)

    def test_result_is_immutable(self):
        result = self.select()
        with self.assertRaises(FrozenInstanceError):
            result.created = False


class SpecializationAliasTests(IsolatedTestCase):
    def test_select_and_repeat_use_profile_alias(self):
        with TemporaryDirectory(prefix="s11-alias-") as directory:
            alias = "s11_alias_test"
            settings = connections["default"].settings_dict.copy()
            settings["NAME"] = str(Path(directory) / "test.sqlite3")
            settings["OPTIONS"] = settings["OPTIONS"].copy()
            connections.databases[alias] = settings
            database = connections[alias]
            try:
                executor = MigrationExecutor(database)
                executor.migrate(executor.loader.graph.leaf_nodes())
                create_xp_catalogs(alias)
                profile = create_xp_profile(alias)
                specialization = Specialization.objects.using(alias).create(code="s11-alias", name="Ficticia")
                with patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
                    grant_historical_xp(profile, 102, "s11-alias-actual")
                    def no_default(*args):
                        raise AssertionError("El servicio usó default.")
                    with connections["default"].execute_wrapper(no_default):
                        first = select_initial_specialization(profile, specialization.code)
                        repeated = select_initial_specialization(profile, specialization.code)
                self.assertTrue(first.created)
                self.assertFalse(repeated.created)
                self.assertEqual(first.progress_id, repeated.progress_id)
                self.assertEqual(UserSpecializationProgress.objects.using(alias).count(), 1)
            finally:
                database.close()
                del connections[alias]
                del connections.databases[alias]
