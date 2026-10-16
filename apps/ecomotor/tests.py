from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .catalog_validation import (
    validate_evolution_stage_catalog,
    validate_level_catalog,
)
from .models import EvolutionStage, LevelThreshold, Specialization


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
