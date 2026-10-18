"""S14-A: ramas y catálogos sintéticos, sin concesiones ni política de producción."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as IsolatedTestCase
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import OperationalError, connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.users.models import UserProfileBank, UserProfileEcomotor

from . import initialization_config, specialization_service as selection
from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, Specialization,
    StatAllocationEvent, UserSpecializationProgress, XPEvent,
)
from .specialization_switch_service import (
    InconsistentSpecializationStateError, IneligibleSpecializationStageError,
    InvalidSpecializationCodeError, InvalidSpecializationConfigurationError,
    InvalidSpecializationProfileError, SpecializationDatabaseError,
    SpecializationSwitchKind as Kind, StaleSpecializationStateError,
    switch_active_specialization,
)
from .test_xp_service import XP_CONFIGURATION, create_xp_catalogs, create_xp_profile
from .xp_service import grant_historical_xp


class SpecializationSwitchTests(TestCase):
    def setUp(self):
        create_xp_catalogs()
        self.profile = create_xp_profile(username="s14-user")
        self.other = create_xp_profile(username="s14-other")
        UserProfileBank.objects.create(user=self.profile.user)
        self.branches = [Specialization.objects.create(code=f"s14-synthetic-{i}", name=f"Ficticia {i}")
                         for i in range(5)]
        self.alpha, self.beta = self.branches[:2]
        config = patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION)
        config.start()
        self.addCleanup(config.stop)
        grant_historical_xp(self.profile, 102, "s14-actual")
        self.first = selection.select_initial_specialization(self.profile, self.alpha.code)

    def switch(self, target=None, expected=None, profile=None):
        return switch_active_specialization(
            self.profile if profile is None else profile,
            self.beta.code if target is None else target,
            self.alpha.code if expected is None else expected,
        )

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (
            get_user_model(), UserProfileBank, UserProfileEcomotor, CharacterStats,
            XPEvent, EvolutionEvent, StatAllocationEvent, UserSpecializationProgress,
            Specialization, EvolutionStage, LevelThreshold,
        )]

    def reject(self, error, *args, **kwargs):
        before = self.snapshot()
        with self.assertRaises(error) as caught:
            self.switch(*args, **kwargs)
        self.assertEqual(self.snapshot(), before)
        return caught.exception

    def test_first_activation_creates_zero_progress_and_one_active_code(self):
        result = self.switch()
        self.assertEqual(result.kind, Kind.FIRST_ACTIVATION)
        self.assertEqual((result.profile_id, result.specialization_id, result.specialization_code),
                         (self.profile.pk, self.beta.pk, self.beta.code))
        row = UserSpecializationProgress.objects.get(pk=result.progress_id)
        self.assertEqual((row.profile_id, row.specialization_id, row.domain_xp_total),
                         (self.profile.pk, self.beta.pk, 0))
        self.assertEqual(UserSpecializationProgress.objects.filter(profile=self.profile).count(), 2)
        self.assertEqual(UserProfileEcomotor.objects.get(pk=self.profile.pk).active_specialization_code, self.beta.code)

    def test_return_preserves_original_progress_id_and_domain_xp(self):
        UserSpecializationProgress.objects.filter(pk=self.first.progress_id).update(domain_xp_total=123)
        beta = self.switch()
        UserSpecializationProgress.objects.filter(pk=beta.progress_id).update(domain_xp_total=456)
        result = self.switch(self.alpha.code, self.beta.code)
        self.assertEqual(result.kind, Kind.REACTIVATION)
        self.assertEqual(result.progress_id, self.first.progress_id)
        self.assertEqual(list(UserSpecializationProgress.objects.order_by("pk").values_list("domain_xp_total", flat=True)),
                         [123, 456])

    def test_alternate_five_branches_without_reset_or_duplicate(self):
        ids = {self.alpha.code: self.first.progress_id}
        active = self.alpha.code
        for branch in self.branches[1:]:
            result = self.switch(branch.code, active)
            ids[branch.code] = result.progress_id
            UserSpecializationProgress.objects.filter(pk=result.progress_id).update(domain_xp_total=branch.pk)
            active = branch.code
        before = list(UserSpecializationProgress.objects.order_by("pk").values())
        for branch in reversed(self.branches[:-1]):
            result = self.switch(branch.code, active)
            self.assertEqual(result.progress_id, ids[branch.code])
            self.assertEqual(result.kind, Kind.REACTIVATION)
            active = branch.code
        self.assertEqual(list(UserSpecializationProgress.objects.order_by("pk").values()), before)
        self.assertEqual(len(before), 5)
        self.assertEqual(selection.select_initial_specialization(self.profile, active).progress_id, ids[active])

    def test_repeat_preserves_state_without_business_writes(self):
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            result = self.switch(self.alpha.code, self.alpha.code)
        self.assertEqual(result.kind, Kind.UNCHANGED)
        self.assertEqual(result.progress_id, self.first.progress_id)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries))

    def test_repeat_without_configuration_catalogs_or_actual_recheck(self):
        EvolutionEvent.objects.all().delete()
        EvolutionStage.objects.all().delete()
        LevelThreshold.objects.all().delete()
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            historical_xp_total=0, current_level=17, current_stage_code="s14-legacy-stage")
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                patch.object(selection, "_eligible", side_effect=AssertionError), \
                CaptureQueriesContext(connection) as queries:
            result = self.switch(self.alpha.code, self.alpha.code)
        self.assertEqual(result.kind, Kind.UNCHANGED)
        sql = " ".join(q["sql"].lower() for q in queries)
        self.assertNotIn("ecomotor_evolutionstage", sql)
        self.assertNotIn("ecomotor_levelthreshold", sql)

    def test_repeat_with_invalid_configuration_and_modified_catalog(self):
        EvolutionStage.objects.filter(ordinal=7).update(minimum_xp=99999)
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", object()):
            self.assertEqual(self.switch(self.alpha.code).kind, Kind.UNCHANGED)

    def test_stale_expected_rejected_even_if_target_already_active(self):
        with patch.object(initialization_config, "INITIAL_CONFIGURATION", None), \
                patch.object(selection, "_eligible", side_effect=AssertionError):
            self.reject(StaleSpecializationStateError, self.alpha.code, self.beta.code)

    def test_stale_expected_for_effective_change_rejected(self):
        self.reject(StaleSpecializationStateError, self.beta.code, self.branches[2].code)

    def test_aba_cannot_detect_all_historical_requests(self):
        self.switch()
        self.switch(self.alpha.code, self.beta.code)
        result = self.switch(self.beta.code, self.alpha.code)
        self.assertEqual(result.kind, Kind.REACTIVATION)
        self.assertEqual(UserSpecializationProgress.objects.count(), 2)

    def test_invalid_profile_and_local_identity(self):
        for value in (object(), UserProfileEcomotor(), True):
            with self.subTest(value=type(value)):
                self.reject(InvalidSpecializationProfileError, profile=value)
        with self.assertRaises(InvalidSpecializationProfileError):
            switch_active_specialization(None, self.beta.code, self.alpha.code)
        for pk in (True, -1, 0, 10**80, "1"):
            invalid = UserProfileEcomotor.objects.get(pk=self.profile.pk)
            invalid.pk = pk
            with self.subTest(pk=pk):
                self.reject(InvalidSpecializationProfileError, profile=invalid)

    def test_missing_profile(self):
        missing = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        missing.pk = 999999
        self.reject(InvalidSpecializationProfileError, profile=missing)

    def test_no_initial_selection_is_not_initialized_by_switch(self):
        self.reject(InconsistentSpecializationStateError, profile=self.other)

    def test_invalid_codes_and_no_silent_normalization(self):
        for value in ("", 123, True, "x" * 33):
            with self.subTest(value=value):
                self.reject(InvalidSpecializationCodeError, value, self.alpha.code)
                self.reject(InvalidSpecializationCodeError, self.beta.code, value)
        for value in (self.beta.code.upper(), " " + self.beta.code, self.beta.code + " ", "s14-missing"):
            with self.subTest(value=value):
                self.reject(InvalidSpecializationCodeError, value)

    def test_missing_codes_none_are_rejected_by_public_api(self):
        for args in ((self.profile, None, self.alpha.code), (self.profile, self.beta.code, None)):
            with self.assertRaises(InvalidSpecializationCodeError):
                switch_active_specialization(*args)

    def test_before_actual_effective_change_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            historical_xp_total=0, current_stage_code=XP_CONFIGURATION.ordered_stage_codes[0])
        self.reject(IneligibleSpecializationStageError)

    def test_xp_and_stage_inconsistent_rejected(self):
        UserProfileEcomotor.objects.filter(pk=self.profile.pk).update(
            current_stage_code=XP_CONFIGURATION.ordered_stage_codes[0])
        self.reject(InconsistentSpecializationStateError)

    def test_missing_or_invalid_configuration_for_effective_change(self):
        for config in (None, object(), replace(XP_CONFIGURATION, ordered_stage_codes=("dup",) * 7)):
            with self.subTest(config=config), patch.object(initialization_config, "INITIAL_CONFIGURATION", config):
                self.reject(InvalidSpecializationConfigurationError)

    def test_incomplete_and_invalid_stage_catalogs(self):
        EvolutionStage.objects.filter(ordinal=7).update(minimum_xp=0)
        self.reject(InvalidSpecializationConfigurationError)
        EvolutionEvent.objects.all().delete()
        EvolutionStage.objects.all().delete()
        self.reject(InvalidSpecializationConfigurationError)

    def test_no_level_catalog_or_initial_stat_values_required(self):
        self.assertIsNone(XP_CONFIGURATION.atk)
        LevelThreshold.objects.all().delete()
        with CaptureQueriesContext(connection) as queries:
            self.assertEqual(self.switch().kind, Kind.FIRST_ACTIVATION)
        self.assertNotIn("ecomotor_levelthreshold", " ".join(q["sql"].lower() for q in queries))

    def test_active_progress_missing(self):
        UserSpecializationProgress.objects.filter(pk=self.first.progress_id).delete()
        self.reject(InconsistentSpecializationStateError)

    def test_missing_statistics(self):
        CharacterStats.objects.filter(profile=self.profile).delete()
        self.reject(InconsistentSpecializationStateError)

    def test_corrupt_stats_and_inactive_progress_are_rejected(self):
        inactive = UserSpecializationProgress.objects.create(profile=self.profile, specialization=self.beta)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_userspecializationprogress SET domain_xp_total = 0.5 WHERE id = %s", [inactive.pk])
        self.reject(InconsistentSpecializationStateError, self.alpha.code)
        UserSpecializationProgress.objects.filter(pk=inactive.pk).update(domain_xp_total=0)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE ecomotor_characterstats SET atk = 0.5 WHERE profile_id = %s", [self.profile.pk])
        self.reject(InconsistentSpecializationStateError, self.alpha.code)

    def test_progress_owned_by_other_profile_does_not_complete_active(self):
        UserSpecializationProgress.objects.filter(pk=self.first.progress_id).update(profile=self.other)
        self.reject(InconsistentSpecializationStateError)

    def test_missing_referenced_specialization_is_inconsistent(self):
        with patch.object(selection.Specialization.objects, "using") as manager:
            manager.return_value.filter.return_value.first.return_value = None
            self.reject(InconsistentSpecializationStateError)

    def test_duplicate_or_foreign_progress_references_rejected(self):
        current = UserProfileEcomotor.objects.get(pk=self.profile.pk)
        row = UserSpecializationProgress.objects.get(pk=self.first.progress_id)
        for field, value in (("profile_id", self.other.pk), ("specialization_id", 0),
                             ("specialization_id", True), ("specialization_id", 10**80)):
            original = getattr(row, field)
            setattr(row, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                selection._existing_selection(current, [row], "default")
            setattr(row, field, original)
        with self.assertRaises(ValidationError):
            selection._existing_selection(current, [row, row], "default")

    def test_invalid_destination_catalog_row(self):
        Specialization.objects.filter(pk=self.beta.pk).update(name="x" * 101)
        self.reject(InconsistentSpecializationStateError)

    def test_rollback_if_new_progress_creation_fails(self):
        error = OperationalError("s14-create-failure")
        with patch.object(UserSpecializationProgress, "save", side_effect=error):
            caught = self.reject(SpecializationDatabaseError)
        self.assertIs(caught.__cause__, error)

    def test_rollback_after_new_progress_insert(self):
        original = UserSpecializationProgress.save
        error = OperationalError("s14-after-insert")
        def fail(row, *args, **kwargs):
            original(row, *args, **kwargs)
            raise error
        with patch.object(UserSpecializationProgress, "save", fail):
            self.assertIs(self.reject(SpecializationDatabaseError).__cause__, error)

    def test_rollback_if_profile_update_fails_after_progress_created(self):
        error = OperationalError("s14-update-failure")
        with patch.object(UserProfileEcomotor, "save", side_effect=error):
            self.assertIs(self.reject(SpecializationDatabaseError).__cause__, error)

    def test_rollback_after_profile_update(self):
        original = UserProfileEcomotor.save
        error = OperationalError("s14-after-update")
        def fail(row, *args, **kwargs):
            original(row, *args, **kwargs)
            raise error
        with patch.object(UserProfileEcomotor, "save", fail):
            self.assertIs(self.reject(SpecializationDatabaseError).__cause__, error)

    def test_programming_errors_are_not_hidden(self):
        with patch.object(UserSpecializationProgress, "save", side_effect=RuntimeError("s14-bug")):
            self.reject(RuntimeError)

    def test_invariants_and_no_reward_or_rank_evaluation(self):
        before = self.snapshot()
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                patch("apps.ecomotor.rank_progression.evaluate_rank_eligibility", side_effect=AssertionError), \
                patch("apps.ecomotor.reward_rules.evaluate_reward", side_effect=AssertionError), \
                patch("apps.ecomotor.stat_allocation.allocate_stat_points", side_effect=AssertionError):
            self.switch()
        after = self.snapshot()
        for index in range(len(before)):
            if index not in (2, 7):
                self.assertEqual(before[index], after[index])
        old, current = before[2][0].copy(), after[2][0].copy()
        old.pop("active_specialization_code")
        current.pop("active_specialization_code")
        self.assertEqual(old, current)
        self.assertEqual(before[7], after[7][:1])

    def test_stale_input_is_reloaded(self):
        self.profile.active_specialization_code = "s14-stale"
        self.profile.historical_xp_total = -1
        self.assertEqual(self.switch().kind, Kind.FIRST_ACTIVATION)

    def test_result_immutable_and_no_history_event(self):
        result = self.switch()
        with self.assertRaises(FrozenInstanceError):
            result.kind = Kind.UNCHANGED
        self.assertFalse(hasattr(result, "replayed"))
        self.assertFalse(hasattr(result, "event_id"))


class SpecializationSwitchAliasTests(IsolatedTestCase):
    def test_all_operations_use_profile_alias(self):
        with TemporaryDirectory(prefix="s14-alias-") as directory:
            alias = "s14_alias_test"
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
                alpha = Specialization.objects.using(alias).create(code="s14-alias-a", name="Ficticia A")
                beta = Specialization.objects.using(alias).create(code="s14-alias-b", name="Ficticia B")
                with patch.object(initialization_config, "INITIAL_CONFIGURATION", XP_CONFIGURATION):
                    grant_historical_xp(profile, 102, "s14-alias-actual")
                    selection.select_initial_specialization(profile, alpha.code)
                    def no_default(*args):
                        raise AssertionError("El servicio usó default.")
                    with connections["default"].execute_wrapper(no_default):
                        first = switch_active_specialization(profile, beta.code, alpha.code)
                        returned = switch_active_specialization(profile, alpha.code, beta.code)
                        repeated = switch_active_specialization(profile, alpha.code, alpha.code)
                        selected = selection.select_initial_specialization(profile, alpha.code)
                self.assertEqual(first.kind, Kind.FIRST_ACTIVATION)
                self.assertEqual(returned.kind, Kind.REACTIVATION)
                self.assertEqual(repeated.kind, Kind.UNCHANGED)
                self.assertEqual(returned.progress_id, selected.progress_id)
            finally:
                database.close()
                del connections[alias]
                del connections.databases[alias]
