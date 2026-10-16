from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .catalog_validation import (
    validate_evolution_stage_catalog,
    validate_level_catalog,
)
from apps.users.models import UserProfileEcomotor

from .models import (
    CharacterStats, EvolutionEvent, EvolutionStage, LevelThreshold, Specialization,
    UserSpecializationProgress, XPEvent,
)


class CatalogModelTests(TestCase):
    def assert_database_rejects(self, model, **fields):
        # No full_clean(): se comprueba la protección real de la BD.
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.create(**fields)

    def test_create_level_threshold_with_zero_points_and_big_xp(self):
        level = LevelThreshold.objects.create(
            level=1, minimum_xp=2**32, stat_points_awarded=0
        )
        level.refresh_from_db()
        self.assertEqual(level.minimum_xp, 2**32)
        self.assertEqual(level.stat_points_awarded, 0)
        self.assertEqual(str(level), f"Nivel 1: {2**32} XP")

    def test_create_evolution_stage(self):
        stage = EvolutionStage.objects.create(
            code="test-stage", name="Etapa de prueba", ordinal=1, minimum_xp=0
        )
        stage.full_clean()
        self.assertIsNotNone(stage.pk)
        self.assertEqual(str(stage), "Etapa de prueba")

    def test_create_specialization(self):
        specialization = Specialization.objects.create(
            code="test-specialization", name="Especialización de prueba"
        )
        specialization.full_clean()
        self.assertIsNotNone(specialization.pk)
        self.assertEqual(str(specialization), "Especialización de prueba")

    def test_duplicate_level_is_rejected_by_database(self):
        fields = dict(level=1, minimum_xp=0, stat_points_awarded=0)
        LevelThreshold.objects.create(**fields)
        self.assert_database_rejects(LevelThreshold, **fields)

    def test_duplicate_stage_code_is_rejected_by_database(self):
        EvolutionStage.objects.create(code="test", name="Prueba", ordinal=1, minimum_xp=0)
        self.assert_database_rejects(
            EvolutionStage, code="test", name="Otra", ordinal=2, minimum_xp=10
        )

    def test_duplicate_specialization_code_is_rejected_by_database(self):
        Specialization.objects.create(code="test", name="Prueba")
        self.assert_database_rejects(Specialization, code="test", name="Otra")

    def test_duplicate_ordinal_is_rejected_by_database(self):
        EvolutionStage.objects.create(code="test-1", name="Prueba", ordinal=1, minimum_xp=0)
        self.assert_database_rejects(
            EvolutionStage, code="test-2", name="Otra", ordinal=1, minimum_xp=10
        )

    def test_nonpositive_levels_are_rejected_by_database(self):
        for level in [0, -1]:
            with self.subTest(level=level):
                self.assert_database_rejects(
                    LevelThreshold, level=level, minimum_xp=0, stat_points_awarded=0
                )

    def test_ordinals_outside_range_are_rejected_by_database(self):
        for ordinal in [-1, 0, 8]:
            with self.subTest(ordinal=ordinal):
                self.assert_database_rejects(
                    EvolutionStage, code="test", name="Prueba", ordinal=ordinal, minimum_xp=0
                )

    def test_negative_level_xp_and_points_are_rejected_by_database(self):
        for field in ["minimum_xp", "stat_points_awarded"]:
            fields = dict(level=1, minimum_xp=0, stat_points_awarded=0)
            fields[field] = -1
            with self.subTest(field=field):
                self.assert_database_rejects(LevelThreshold, **fields)

    def test_negative_stage_xp_is_rejected_by_database(self):
        self.assert_database_rejects(
            EvolutionStage, code="test", name="Prueba", ordinal=1, minimum_xp=-1
        )

    def test_empty_codes_and_names_are_rejected_by_database(self):
        for model in [EvolutionStage, Specialization]:
            for field in ["code", "name"]:
                fields = dict(code="test", name="Prueba")
                if model is EvolutionStage:
                    fields.update(ordinal=1, minimum_xp=0)
                fields[field] = ""
                with self.subTest(model=model.__name__, field=field):
                    self.assert_database_rejects(model, **fields)

    def test_field_validation_rejects_invalid_values(self):
        instances = [
            LevelThreshold(level=0, minimum_xp=0, stat_points_awarded=0),
            LevelThreshold(level=1, minimum_xp=-1, stat_points_awarded=0),
            LevelThreshold(level=1, minimum_xp=0, stat_points_awarded=-1),
            EvolutionStage(code="test", name="Prueba", ordinal=8, minimum_xp=0),
            EvolutionStage(code="", name="Prueba", ordinal=1, minimum_xp=0),
            Specialization(code="test", name=""),
            Specialization(code="x" * 33, name="Prueba"),
            EvolutionStage(code="test", name="x" * 101, ordinal=1, minimum_xp=0),
        ]
        for instance in instances:
            with self.subTest(model=type(instance).__name__, fields=instance.__dict__):
                with self.assertRaises(ValidationError):
                    instance.full_clean()

    def test_progressive_catalog_creation_is_allowed(self):
        LevelThreshold.objects.create(level=3, minimum_xp=20, stat_points_awarded=0)
        EvolutionStage.objects.create(code="test-7", name="Prueba", ordinal=7, minimum_xp=20)
        self.assertEqual(LevelThreshold.objects.count(), 1)
        self.assertEqual(EvolutionStage.objects.count(), 1)


class LevelCatalogValidationTests(TestCase):
    def setUp(self):
        # Valores ficticios: no son umbrales ni puntos oficiales.
        self.levels = [
            LevelThreshold(level=1, minimum_xp=0, stat_points_awarded=0),
            LevelThreshold(level=2, minimum_xp=17, stat_points_awarded=2),
            LevelThreshold(level=3, minimum_xp=53, stat_points_awarded=4),
        ]

    def test_valid_catalog_in_any_input_order(self):
        validate_level_catalog(reversed(self.levels))

    def test_single_initial_level_is_valid(self):
        validate_level_catalog(self.levels[:1])

    def test_default_validation_reads_persisted_catalog(self):
        LevelThreshold.objects.bulk_create(self.levels)
        validate_level_catalog()

    def test_empty_catalog_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_level_catalog([])

    def test_gaps_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_level_catalog([self.levels[0], self.levels[2]])

    def test_missing_first_level_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_level_catalog(self.levels[1:])

    def test_duplicate_unsaved_levels_are_rejected(self):
        self.levels[1].level = 1
        with self.assertRaises(ValidationError):
            validate_level_catalog(self.levels)

    def test_initial_xp_must_be_zero(self):
        self.levels[0].minimum_xp = 1
        with self.assertRaises(ValidationError):
            validate_level_catalog(self.levels)

    def test_equal_or_decreasing_thresholds_are_rejected(self):
        for xp in [17, 16]:
            self.levels[2].minimum_xp = xp
            with self.subTest(xp=xp), self.assertRaises(ValidationError):
                validate_level_catalog(self.levels)

    def test_invalid_row_is_rejected(self):
        self.levels[0].stat_points_awarded = -1
        with self.assertRaises(ValidationError):
            validate_level_catalog(self.levels)


class EvolutionCatalogValidationTests(TestCase):
    def setUp(self):
        # La correspondencia es ficticia y local al test, no un catálogo oficial.
        self.codes = [f"test-stage-{ordinal}" for ordinal in range(1, 8)]
        names = [
            "Prehistoria", "Griega", "Romana", "Renacentista",
            "Contemporánea", "Siglo XX", "Actual",
        ]
        self.stages = [
            EvolutionStage(code=code, name=name, ordinal=ordinal, minimum_xp=(ordinal - 1) * 37)
            for ordinal, (code, name) in enumerate(zip(self.codes, names), start=1)
        ]

    def validate(self, stages=None):
        validate_evolution_stage_catalog(
            self.stages if stages is None else stages, ordered_stage_codes=self.codes
        )

    def test_valid_seven_stages_in_any_input_order(self):
        self.validate(reversed(self.stages))

    def test_default_validation_reads_persisted_catalog(self):
        EvolutionStage.objects.bulk_create(self.stages)
        validate_evolution_stage_catalog(ordered_stage_codes=self.codes)

    def test_display_name_is_not_technical_identity(self):
        self.stages[0].name = "Nombre visible traducido"
        self.validate()

    def test_empty_or_incomplete_catalog_is_rejected(self):
        for stages in [[], self.stages[:3], self.stages[:6]]:
            with self.subTest(count=len(stages)), self.assertRaises(ValidationError):
                self.validate(stages)

    def test_more_than_seven_stages_are_rejected(self):
        with self.assertRaises(ValidationError):
            self.validate(self.stages + [self.stages[0]])

    def test_duplicate_ordinals_are_rejected(self):
        self.stages[1].ordinal = 1
        with self.assertRaises(ValidationError):
            self.validate()

    def test_swapped_functional_stages_are_rejected(self):
        self.stages[0].code, self.stages[1].code = self.stages[1].code, self.stages[0].code
        with self.assertRaises(ValidationError):
            self.validate()

    def test_unrecognized_code_is_rejected(self):
        self.stages[0].code = "test-unknown"
        with self.assertRaises(ValidationError):
            self.validate()

    def test_initial_xp_must_be_zero(self):
        self.stages[0].minimum_xp = 1
        with self.assertRaises(ValidationError):
            self.validate()

    def test_equal_or_decreasing_thresholds_are_rejected(self):
        for xp in [37, 36]:
            self.stages[2].minimum_xp = xp
            with self.subTest(xp=xp), self.assertRaises(ValidationError):
                self.validate()

    def test_invalid_row_is_rejected(self):
        self.stages[0].minimum_xp = -1
        with self.assertRaises(ValidationError):
            self.validate()

    def test_invalid_code_correspondence_is_rejected(self):
        for codes in [[], self.codes[:6], self.codes + ["test-extra"],
                      [self.codes[0]] * 7, [""] + self.codes[1:], [None] + self.codes[1:]]:
            with self.subTest(codes=codes), self.assertRaises(ValidationError):
                validate_evolution_stage_catalog(self.stages, ordered_stage_codes=codes)


class CharacterStatsTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="stats-test-user")
        self.profile = UserProfileEcomotor.objects.create(
            user=user, current_level=1, current_stage_code="test-stage"
        )
        # Valores ficticios, deliberadamente sin imponer el intervalo 1–10.
        self.fields = dict(
            profile=self.profile, atk=0, def_stat=-2, log_stat=13,
            spe=3, vel=4, int_stat=6, available_points=0,
        )

    def test_create_stats_with_explicit_values(self):
        stats = CharacterStats.objects.create(**self.fields)
        stats.refresh_from_db()
        for field, value in self.fields.items():
            self.assertEqual(getattr(stats, field), value)

    def test_duplicate_stats_are_rejected_by_database(self):
        CharacterStats.objects.create(**self.fields)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CharacterStats.objects.create(**self.fields)

    def test_negative_available_points_are_rejected_by_database(self):
        self.fields["available_points"] = -1
        with self.assertRaises(IntegrityError), transaction.atomic():
            CharacterStats.objects.create(**self.fields)

    def test_stats_require_all_values(self):
        for field in ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points"]:
            fields = self.fields.copy()
            del fields[field]
            with self.subTest(field=field):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    CharacterStats.objects.create(**fields)

    def test_profile_does_not_automatically_create_stats(self):
        self.assertFalse(CharacterStats.objects.filter(profile=self.profile).exists())

    def test_provisional_cascade_deletes_dependent_stats(self):
        stats = CharacterStats.objects.create(**self.fields)
        self.profile.delete()
        self.assertFalse(CharacterStats.objects.filter(pk=stats.pk).exists())


class HistoryModelTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="history-test-user")
        self.profile = UserProfileEcomotor.objects.create(
            user=user, current_level=1, current_stage_code="test-stage-1"
        )
        self.stage = EvolutionStage.objects.create(
            code="test-stage-2", name="Etapa ficticia", ordinal=2, minimum_xp=19
        )
        self.xp_fields = dict(
            profile=self.profile, amount=23, xp_before=11, xp_after=34,
            operation_key="test-operation",
        )

    def create_xp(self, **overrides):
        return XPEvent.objects.create(**(self.xp_fields | overrides))

    def test_valid_xp_event_and_automatic_timestamp(self):
        before = timezone.now()
        event = self.create_xp()
        after = timezone.now()
        event.refresh_from_db()
        for field, value in self.xp_fields.items():
            self.assertEqual(getattr(event, field), value)
        self.assertLessEqual(before, event.created_at)
        self.assertLessEqual(event.created_at, after)

    def test_xp_amount_zero_or_negative_is_rejected_by_database(self):
        for amount in [0, -1]:
            with self.subTest(amount=amount):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_xp(amount=amount, xp_after=11 + amount)

    def test_negative_snapshots_are_rejected_by_database(self):
        # Mantener la suma coherente permite comprobar la restricción de signo.
        for values in [dict(xp_before=-1, xp_after=22), dict(xp_before=-24, xp_after=-1)]:
            with self.subTest(values=values):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.create_xp(**values)

    def test_incoherent_snapshot_sum_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_xp(xp_after=35)

    def test_empty_operation_key_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_xp(operation_key="")

    def test_duplicate_key_for_same_profile_is_rejected_by_database(self):
        self.create_xp()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_xp()

    def test_same_key_is_allowed_for_different_profiles(self):
        self.create_xp()
        user = get_user_model().objects.create_user(username="other-history-test-user")
        other = UserProfileEcomotor.objects.create(
            user=user, current_level=1, current_stage_code="test-stage-1"
        )
        self.create_xp(profile=other)
        self.assertEqual(XPEvent.objects.filter(operation_key="test-operation").count(), 2)

    def test_xp_requires_profile(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_xp(profile=None)

    def test_xp_requires_all_amounts_snapshots_and_key(self):
        for field in ["amount", "xp_before", "xp_after", "operation_key"]:
            fields = self.xp_fields.copy()
            del fields[field]
            with self.subTest(field=field):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    XPEvent.objects.create(**fields)

    def test_xp_profile_foreign_key_is_enforced(self):
        fields = self.xp_fields.copy()
        del fields["profile"]
        with self.assertRaises(IntegrityError), transaction.atomic():
            XPEvent.objects.create(**fields, profile_id=self.profile.pk + 1000)
            # SQLite difiere las FK; verificar en el savepoint antes del teardown.
            connection.check_constraints()

    def test_valid_evolution_and_automatic_timestamp(self):
        event = self.create_xp()
        before = timezone.now()
        evolution = EvolutionEvent.objects.create(
            profile=self.profile, stage=self.stage, xp_event=event
        )
        after = timezone.now()
        evolution.refresh_from_db()
        self.assertEqual(evolution.profile, self.profile)
        self.assertEqual(evolution.stage, self.stage)
        self.assertEqual(evolution.xp_event, event)
        self.assertLessEqual(before, evolution.created_at)
        self.assertLessEqual(evolution.created_at, after)

    def test_duplicate_profile_stage_is_rejected_even_with_different_cause(self):
        event = self.create_xp()
        EvolutionEvent.objects.create(profile=self.profile, stage=self.stage, xp_event=event)
        other_event = self.create_xp(operation_key="test-other-operation")
        with self.assertRaises(IntegrityError), transaction.atomic():
            EvolutionEvent.objects.create(
                profile=self.profile, stage=self.stage, xp_event=other_event
            )

    def test_single_xp_event_can_cause_multiple_evolutions(self):
        event = self.create_xp()
        other_stage = EvolutionStage.objects.create(
            code="test-stage-3", name="Otra etapa ficticia", ordinal=3, minimum_xp=29
        )
        for stage in [self.stage, other_stage]:
            EvolutionEvent.objects.create(profile=self.profile, stage=stage, xp_event=event)
        self.assertEqual(EvolutionEvent.objects.filter(xp_event=event).count(), 2)

    def test_evolution_foreign_keys_are_enforced(self):
        event = self.create_xp()
        fields = dict(profile_id=self.profile.pk, stage_id=self.stage.pk, xp_event_id=event.pk)
        for field in fields:
            for value in [None, fields[field] + 1000]:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        EvolutionEvent.objects.create(**(fields | {field: value}))
                        connection.check_constraints()

    def test_referenced_stage_is_protected(self):
        event = self.create_xp()
        EvolutionEvent.objects.create(profile=self.profile, stage=self.stage, xp_event=event)
        with self.assertRaises(ProtectedError):
            self.stage.delete()
        self.assertTrue(EvolutionStage.objects.filter(pk=self.stage.pk).exists())
        self.assertEqual(EvolutionEvent.objects.count(), 1)

    def test_deleting_xp_cascades_to_its_evolutions(self):
        event = self.create_xp()
        EvolutionEvent.objects.create(profile=self.profile, stage=self.stage, xp_event=event)
        event.delete()
        self.assertFalse(XPEvent.objects.exists())
        self.assertFalse(EvolutionEvent.objects.exists())
        self.assertTrue(UserProfileEcomotor.objects.filter(pk=self.profile.pk).exists())
        self.assertTrue(EvolutionStage.objects.filter(pk=self.stage.pk).exists())

    def test_deleting_profile_cascades_to_both_histories(self):
        event = self.create_xp()
        EvolutionEvent.objects.create(profile=self.profile, stage=self.stage, xp_event=event)
        self.profile.delete()
        self.assertFalse(XPEvent.objects.exists())
        self.assertFalse(EvolutionEvent.objects.exists())
        self.assertTrue(EvolutionStage.objects.filter(pk=self.stage.pk).exists())

    def test_creating_xp_does_not_update_profile_or_create_evolutions(self):
        self.create_xp()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.historical_xp_total, 0)
        self.assertEqual(self.profile.current_stage_code, "test-stage-1")
        self.assertFalse(EvolutionEvent.objects.exists())

    def test_profile_does_not_create_initial_history(self):
        self.assertFalse(XPEvent.objects.exists())
        self.assertFalse(EvolutionEvent.objects.exists())


class SpecializationProgressTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="domain-test-user")
        self.profile = UserProfileEcomotor.objects.create(
            user=user, historical_xp_total=34, current_level=2,
            current_stage_code="test-stage-2",
        )
        self.specialization = Specialization.objects.create(
            code="test-specialization", name="Especialización ficticia"
        )
        self.fields = dict(profile=self.profile, specialization=self.specialization)

    def test_create_valid_progress_with_zero_default(self):
        progress = UserSpecializationProgress.objects.create(**self.fields)
        progress.refresh_from_db()
        progress.full_clean()
        self.assertEqual(progress.profile, self.profile)
        self.assertEqual(progress.specialization, self.specialization)
        self.assertEqual(progress.domain_xp_total, 0)

    def test_positive_big_domain_xp_is_preserved(self):
        progress = UserSpecializationProgress.objects.create(
            **self.fields, domain_xp_total=2**32
        )
        progress.refresh_from_db()
        self.assertEqual(progress.domain_xp_total, 2**32)

    def test_negative_domain_xp_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserSpecializationProgress.objects.create(**self.fields, domain_xp_total=-1)

    def test_negative_domain_xp_is_rejected_by_model_validation(self):
        progress = UserSpecializationProgress(**self.fields, domain_xp_total=-1)
        with self.assertRaises(ValidationError):
            progress.full_clean()

    def test_duplicate_profile_specialization_is_rejected_by_database(self):
        UserSpecializationProgress.objects.create(**self.fields)
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserSpecializationProgress.objects.create(**self.fields)

    def test_profile_can_have_multiple_specializations(self):
        UserSpecializationProgress.objects.create(**self.fields)
        other = Specialization.objects.create(code="test-other", name="Otra ficticia")
        UserSpecializationProgress.objects.create(profile=self.profile, specialization=other)
        self.assertEqual(UserSpecializationProgress.objects.filter(profile=self.profile).count(), 2)

    def test_specialization_can_have_multiple_profiles(self):
        UserSpecializationProgress.objects.create(**self.fields)
        user = get_user_model().objects.create_user(username="other-domain-test-user")
        other = UserProfileEcomotor.objects.create(
            user=user, current_level=1, current_stage_code="test-stage-1"
        )
        UserSpecializationProgress.objects.create(profile=other, specialization=self.specialization)
        self.assertEqual(UserSpecializationProgress.objects.filter(specialization=self.specialization).count(), 2)

    def test_foreign_keys_are_required_and_enforced_by_database(self):
        fields = dict(profile_id=self.profile.pk, specialization_id=self.specialization.pk)
        for field in fields:
            for value in [None, fields[field] + 1000]:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        UserSpecializationProgress.objects.create(**(fields | {field: value}))
                        connection.check_constraints()

    def test_domain_xp_cannot_be_null(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserSpecializationProgress.objects.create(**self.fields, domain_xp_total=None)

    def test_referenced_specialization_is_protected(self):
        progress = UserSpecializationProgress.objects.create(**self.fields)
        with self.assertRaises(ProtectedError):
            self.specialization.delete()
        self.assertTrue(UserSpecializationProgress.objects.filter(pk=progress.pk).exists())
        self.assertTrue(Specialization.objects.filter(pk=self.specialization.pk).exists())

    def test_profile_deletion_cascades_to_progress(self):
        progress = UserSpecializationProgress.objects.create(**self.fields)
        self.profile.delete()
        self.assertFalse(UserSpecializationProgress.objects.filter(pk=progress.pk).exists())
        self.assertTrue(Specialization.objects.filter(pk=self.specialization.pk).exists())

    def test_profile_creation_does_not_create_progress(self):
        self.assertFalse(UserSpecializationProgress.objects.filter(profile=self.profile).exists())

    def test_specialization_creation_does_not_create_progress(self):
        self.assertFalse(UserSpecializationProgress.objects.filter(specialization=self.specialization).exists())

    def test_create_and_update_domain_xp_leave_historical_progress_unchanged(self):
        progress = UserSpecializationProgress.objects.create(**self.fields, domain_xp_total=17)
        for amount in [17, 53]:
            progress.domain_xp_total = amount
            progress.save(update_fields=["domain_xp_total"])
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.historical_xp_total, 34)
            self.assertEqual(self.profile.current_level, 2)
            self.assertEqual(self.profile.current_stage_code, "test-stage-2")
            self.assertFalse(XPEvent.objects.exists())
            self.assertFalse(EvolutionEvent.objects.exists())
