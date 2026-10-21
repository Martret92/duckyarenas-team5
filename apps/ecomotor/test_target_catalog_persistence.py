"""Synthetic preparatory data only; no frozen versions or real progression use."""

from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as PlainTestCase
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, connections, models, transaction
from django.db.migrations import CreateModel
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from . import target_catalog_validation
from .models import (
    EvolutionEvent, EvolutionStage, LevelThreshold, StatAllocationEvent,
    TargetCatalogVersion, TargetEpoch, TargetLevelThreshold, XPEvent,
)
from .target_catalog_persistence import validate_target_catalog_version
from .target_catalog_validation import InvalidTargetCatalogError, TargetCatalogSnapshot


BEFORE = ("ecomotor", "0005_stat_allocation_event")
AFTER = ("ecomotor", "0006_target_catalog_preparation")
TARGET_MODELS = (TargetCatalogVersion, TargetLevelThreshold, TargetEpoch)


def synthetic_catalog(*, using="default", version="synthetic-r1", catalog_id="synthetic-catalog", levels=8):
    catalog = TargetCatalogVersion.objects.using(using).create(catalog_id=catalog_id, version=version)
    TargetLevelThreshold.objects.using(using).bulk_create([
        TargetLevelThreshold(catalog=catalog, level=n, minimum_xp=(n - 1) * 13)
        for n in range(1, levels + 1)
    ])
    TargetEpoch.objects.using(using).bulk_create([
        TargetEpoch(catalog=catalog, code=f"synthetic-epoch-{n}", name=f"Synthetic epoch {n}",
                    ordinal=n, minimum_xp=(n - 1) * 13) for n in range(1, 8)
    ])
    return catalog


class TargetCatalogModelTests(TestCase):
    def setUp(self):
        self.catalog = TargetCatalogVersion.objects.create(catalog_id="synthetic", version="r1")

    def assert_db_rejects(self, model, **values):
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.create(**values)

    def test_create_and_query_models_with_exact_field_types(self):
        for model in TARGET_MODELS:
            self.assertIs(type(model._meta.pk), models.BigAutoField)
        self.assertEqual(TargetCatalogVersion._meta.get_field("catalog_id").max_length, 64)
        self.assertEqual(TargetCatalogVersion._meta.get_field("version").max_length, 64)
        self.assertEqual(TargetEpoch._meta.get_field("code").max_length, 64)
        self.assertEqual(TargetEpoch._meta.get_field("name").max_length, 100)
        self.assertIs(type(TargetLevelThreshold._meta.get_field("level")), models.PositiveIntegerField)
        self.assertIs(type(TargetEpoch._meta.get_field("ordinal")), models.PositiveSmallIntegerField)
        for model in (TargetLevelThreshold, TargetEpoch):
            self.assertIs(type(model._meta.get_field("minimum_xp")), models.PositiveBigIntegerField)
            self.assertIs(model._meta.get_field("catalog").remote_field.on_delete, models.PROTECT)
        level = TargetLevelThreshold.objects.create(catalog=self.catalog, level=1, minimum_xp=0)
        epoch = TargetEpoch.objects.create(catalog=self.catalog, code="synthetic", name="Synthetic", ordinal=1, minimum_xp=0)
        self.assertEqual(TargetLevelThreshold.objects.get(pk=level.pk).catalog, self.catalog)
        self.assertEqual(TargetEpoch.objects.get(pk=epoch.pk).catalog, self.catalog)

    def test_catalog_identity_pair_unique_but_each_dimension_can_repeat(self):
        self.assert_db_rejects(TargetCatalogVersion, catalog_id="synthetic", version="r1")
        second = TargetCatalogVersion.objects.create(catalog_id="synthetic", version="r2")
        third = TargetCatalogVersion.objects.create(catalog_id="synthetic-other", version="r1")
        self.assertEqual(len({self.catalog.pk, second.pk, third.pk}), 3)

    def test_empty_catalog_identity_and_version_rejected_by_database(self):
        for values in (dict(catalog_id="", version="r2"), dict(catalog_id="other", version="")):
            with self.subTest(values=values):
                self.assert_db_rejects(TargetCatalogVersion, **values)

    def test_level_unique_within_catalog_only(self):
        TargetLevelThreshold.objects.create(catalog=self.catalog, level=1, minimum_xp=0)
        self.assert_db_rejects(TargetLevelThreshold, catalog=self.catalog, level=1, minimum_xp=13)
        second = TargetCatalogVersion.objects.create(catalog_id="synthetic", version="r2")
        TargetLevelThreshold.objects.create(catalog=second, level=1, minimum_xp=0)

    def test_level_zero_negative_and_xp_negative_rejected_by_database(self):
        for level, xp in ((0, 0), (-1, 0), (1, -1)):
            with self.subTest(level=level, xp=xp):
                self.assert_db_rejects(TargetLevelThreshold, catalog=self.catalog, level=level, minimum_xp=xp)

    def test_epoch_code_and_ordinal_unique_per_version(self):
        TargetEpoch.objects.create(catalog=self.catalog, code="synthetic", name="Synthetic", ordinal=1, minimum_xp=0)
        for code, ordinal in (("synthetic", 2), ("synthetic-other", 1)):
            with self.subTest(code=code, ordinal=ordinal):
                self.assert_db_rejects(TargetEpoch, catalog=self.catalog, code=code, name="Synthetic", ordinal=ordinal, minimum_xp=13)
        second = TargetCatalogVersion.objects.create(catalog_id="synthetic", version="r2")
        TargetEpoch.objects.create(catalog=second, code="synthetic", name="Synthetic", ordinal=1, minimum_xp=0)

    def test_epoch_ranges_xp_and_empty_text_rejected_by_database(self):
        for change in (dict(ordinal=0), dict(ordinal=-1), dict(ordinal=8), dict(minimum_xp=-1), dict(code=""), dict(name="")):
            values = dict(catalog=self.catalog, code="synthetic", name="Synthetic", ordinal=1, minimum_xp=0) | change
            with self.subTest(change=change):
                self.assert_db_rejects(TargetEpoch, **values)

    def test_full_clean_checks_text_lengths_and_local_values(self):
        invalid = (TargetCatalogVersion(catalog_id="x" * 65, version="r1"),
                   TargetCatalogVersion(catalog_id="synthetic", version="x" * 65),
                   TargetLevelThreshold(catalog=self.catalog, level=0, minimum_xp=0),
                   TargetEpoch(catalog=self.catalog, code="x" * 65, name="Synthetic", ordinal=1, minimum_xp=0),
                   TargetEpoch(catalog=self.catalog, code="synthetic", name="x" * 101, ordinal=1, minimum_xp=0),
                   TargetEpoch(catalog=self.catalog, code="synthetic", name="Synthetic", ordinal=8, minimum_xp=0))
        for row in invalid:
            with self.subTest(model=type(row)), self.assertRaises(ValidationError):
                row.full_clean()

    def test_sqlite_does_not_enforce_max_length_or_nonblank_whitespace(self):
        if connections["default"].vendor != "sqlite":
            self.skipTest("Documents the current SQLite boundary")
        row = TargetCatalogVersion.objects.create(catalog_id="x" * 65, version=" ")
        self.assertEqual(len(TargetCatalogVersion.objects.get(pk=row.pk).catalog_id), 65)
        TargetEpoch.objects.create(catalog=row, code=" ", name=" ", ordinal=1, minimum_xp=0)
        with self.assertRaises(ValidationError):
            row.full_clean()
        with self.assertRaises(InvalidTargetCatalogError):
            validate_target_catalog_version(row.pk, using="default")

    def test_protect_is_only_parent_child_deletion_protection(self):
        level = TargetLevelThreshold.objects.create(catalog=self.catalog, level=1, minimum_xp=0)
        with self.assertRaises(ProtectedError):
            self.catalog.delete()
        # Preparatory children are mutable/deletable; phase 2 is not implemented.
        TargetLevelThreshold.objects.filter(pk=level.pk).update(minimum_xp=13)
        self.assertEqual(TargetLevelThreshold.objects.get(pk=level.pk).minimum_xp, 13)
        level.delete()
        self.catalog.delete()

    def test_no_points_authority_or_real_progression_fields(self):
        self.assertEqual({f.name for f in TargetLevelThreshold._meta.fields}, {"id", "catalog", "level", "minimum_xp"})
        self.assertEqual({f.name for f in TargetCatalogVersion._meta.fields}, {"id", "catalog_id", "version", "frozen_at"})
        self.assertEqual({f.name for f in TargetEpoch._meta.fields}, {"id", "catalog", "code", "name", "ordinal", "minimum_xp"})


class TargetCatalogReaderTests(TestCase):
    def setUp(self):
        self.catalog = synthetic_catalog()

    def read(self):
        return validate_target_catalog_version(self.catalog.pk, using="default")

    def test_valid_catalog_has_seven_epochs_eight_levels_and_zero_adapter_points(self):
        result = self.read()
        self.assertIs(type(result), TargetCatalogSnapshot)
        self.assertEqual((len(result.levels), len(result.epochs)), (8, 7))
        self.assertEqual(result.catalog_version, "synthetic-r1")
        self.assertEqual(tuple(row.stat_points_awarded for row in result.levels), (0,) * 8)
        self.assertEqual(result.ordered_epoch_codes, tuple(f"synthetic-epoch-{n}" for n in range(1, 8)))

    def test_delegate_to_public_a11_with_explicit_codes_and_version(self):
        with patch.object(target_catalog_validation, "validate_target_level_epoch_catalog",
                          wraps=target_catalog_validation.validate_target_level_epoch_catalog) as validate:
            result = self.read()
        validate.assert_called_once()
        self.assertEqual(validate.call_args.kwargs, dict(ordered_epoch_codes=result.ordered_epoch_codes,
                                                       catalog_version="synthetic-r1"))
        self.assertTrue(all(row.stat_points_awarded == 0 for row in validate.call_args.args[0]))

    def test_versions_are_selected_by_technical_id_without_mixing(self):
        other = synthetic_catalog(version="synthetic-r2", levels=9)
        TargetEpoch.objects.filter(catalog=other, ordinal=2).update(minimum_xp=999)
        self.assertEqual(len(self.read().levels), 8)
        with self.assertRaises(InvalidTargetCatalogError):
            validate_target_catalog_version(other.pk, using="default")
        same_version = synthetic_catalog(catalog_id="synthetic-other")
        self.assertNotEqual(self.catalog.pk, same_version.pk)
        self.assertEqual(validate_target_catalog_version(same_version.pk, using="default"), self.read())
        # The pure snapshot preserves version text, not an authorization/catalog ID certificate.

    def test_missing_version_and_invalid_inputs_are_explicit(self):
        with self.assertRaises(TargetCatalogVersion.DoesNotExist):
            validate_target_catalog_version(2**63 - 1, using="default")
        for value in (0, -1, True, 1.0, "1", None, self.catalog, 2**63):
            with self.subTest(value=repr(value)), self.assertRaises(InvalidTargetCatalogError):
                validate_target_catalog_version(value, using="default")
        for alias in (None, 1, "", "unknown"):
            with self.subTest(alias=alias), self.assertRaises(InvalidTargetCatalogError):
                validate_target_catalog_version(self.catalog.pk, using=alias)

    def test_incomplete_catalog_or_missing_level_eight_rejected(self):
        for model, key, value in ((TargetEpoch, "ordinal", 7), (TargetLevelThreshold, "level", 8),
                                  (TargetLevelThreshold, "level", 3)):
            with self.subTest(model=model, value=value), transaction.atomic():
                model.objects.filter(catalog=self.catalog, **{key: value}).delete()
                with self.assertRaises(InvalidTargetCatalogError):
                    self.read()
                transaction.set_rollback(True)

    def test_empty_catalog_rejected(self):
        empty = TargetCatalogVersion.objects.create(catalog_id="synthetic-empty", version="r1")
        with self.assertRaises(InvalidTargetCatalogError):
            validate_target_catalog_version(empty.pk, using="default")

    def test_initial_xp_nonzero_and_nongrowing_thresholds_rejected(self):
        cases = ((TargetLevelThreshold, "level", 1, 1), (TargetEpoch, "ordinal", 1, 1),
                 (TargetLevelThreshold, "level", 3, 13), (TargetEpoch, "ordinal", 3, 13))
        for model, key, value, xp in cases:
            with self.subTest(model=model, value=value), transaction.atomic():
                model.objects.filter(catalog=self.catalog, **{key: value}).update(minimum_xp=xp)
                with self.assertRaises(InvalidTargetCatalogError):
                    self.read()
                transaction.set_rollback(True)

    def test_each_level_epoch_mismatch_rejected(self):
        for ordinal in range(2, 8):
            with self.subTest(ordinal=ordinal), transaction.atomic():
                TargetEpoch.objects.filter(catalog=self.catalog, ordinal=ordinal).update(minimum_xp=(ordinal - 1) * 13 + 1)
                with self.assertRaises(InvalidTargetCatalogError):
                    self.read()
                transaction.set_rollback(True)

    def test_metadata_invalid_or_overlong_despite_sqlite_affinity_rejected(self):
        cases = ((TargetCatalogVersion, "catalog_id", " "), (TargetCatalogVersion, "version", "x" * 65),
                 (TargetEpoch, "name", " "), (TargetEpoch, "code", "x" * 65))
        for model, name, value in cases:
            with self.subTest(model=model, name=name), transaction.atomic():
                model.objects.filter(pk=self.catalog.pk if model is TargetCatalogVersion else
                                     TargetEpoch.objects.filter(catalog=self.catalog).first().pk).update(**{name: value})
                with self.assertRaises(InvalidTargetCatalogError):
                    self.read()
                transaction.set_rollback(True)

    def test_fractional_observed_xp_is_not_silently_truncated(self):
        with connections["default"].cursor() as cursor:
            cursor.execute("UPDATE ecomotor_targetlevelthreshold SET minimum_xp=13.5 WHERE catalog_id=%s AND level=2",
                           [self.catalog.pk])
        with self.assertRaises(InvalidTargetCatalogError):
            self.read()

    def test_extra_levels_do_not_add_epoch_and_names_are_not_historical_codes(self):
        TargetLevelThreshold.objects.create(catalog=self.catalog, level=9, minimum_xp=104)
        TargetEpoch.objects.filter(catalog=self.catalog, ordinal=7).update(name="Synthetic renamed display")
        result = self.read()
        self.assertEqual((len(result.levels), len(result.epochs)), (9, 7))
        self.assertEqual(result.epochs[-1].code, "synthetic-epoch-7")

    def test_read_only_preserves_all_data_and_never_calls_writers(self):
        from apps.users.models import UserProfileEcomotor
        from .models import CharacterStats
        observed = (*TARGET_MODELS, LevelThreshold, EvolutionStage, XPEvent, EvolutionEvent,
                    CharacterStats, UserProfileEcomotor, StatAllocationEvent)
        before = [list(model.objects.order_by("pk").values()) for model in observed]
        with patch("apps.ecomotor.xp_service.grant_historical_xp", side_effect=AssertionError), \
                patch("apps.ecomotor.target_xp_plan.plan_target_xp_grant", side_effect=AssertionError), \
                patch("apps.ecomotor.target_stats_resolution.resolve_target_stats_configuration", side_effect=AssertionError), \
                CaptureQueriesContext(connections["default"]) as queries:
            self.read()
        self.assertEqual(len(queries), 3)
        self.assertTrue(all(row["sql"].lstrip().upper().startswith("SELECT") for row in queries))
        self.assertEqual([list(model.objects.order_by("pk").values()) for model in observed], before)

    def test_database_error_is_not_empty_or_successful_catalog(self):
        error = OperationalError("synthetic read failure")
        with patch.object(TargetCatalogVersion.objects, "using", side_effect=error), self.assertRaises(OperationalError) as caught:
            self.read()
        self.assertIs(caught.exception, error)


class TargetCatalogMigrationTests(PlainTestCase):
    """0005 -> 0006 only in a temporary file, never local developer SQLite."""

    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-target-catalog-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "target_catalog_migration_test"
        configuration = connections["default"].settings_dict.copy()
        configuration["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        configuration["OPTIONS"] = configuration["OPTIONS"].copy()
        connections.databases[self.alias] = configuration
        self.db = connections[self.alias]
        self.addCleanup(self.close_db)
        apps = self.migrate(BEFORE)
        with self.db.cursor() as cursor:
            cursor.execute("INSERT INTO ecomotor_levelthreshold (level, minimum_xp, stat_points_awarded) VALUES (1,0,17)")
            cursor.execute("INSERT INTO ecomotor_evolutionstage (code,name,ordinal,minimum_xp) VALUES ('synthetic-v1','Synthetic V1',1,0)")
        user = apps.get_model("auth", "User").objects.using(self.alias).create(username="synthetic-catalog-migration")
        stage = apps.get_model("ecomotor", "EvolutionStage").objects.using(self.alias).create(
            code="synthetic-v1-next", name="Synthetic V1 next", ordinal=2, minimum_xp=13)
        profile = apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).create(
            user_id=user.pk, current_level=2, current_stage_code=stage.code, historical_xp_total=13)
        apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).create(
            profile_id=profile.pk, atk=2, def_stat=3, log_stat=4, spe=5, vel=6, int_stat=7, available_points=8)
        xp = apps.get_model("ecomotor", "XPEvent").objects.using(self.alias).create(
            profile_id=profile.pk, operation_key="synthetic-migration-xp", amount=13, xp_before=0, xp_after=13)
        apps.get_model("ecomotor", "EvolutionEvent").objects.using(self.alias).create(
            profile_id=profile.pk, xp_event_id=xp.pk, stage_id=stage.pk)

    def close_db(self):
        self.db.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self, target):
        executor = MigrationExecutor(self.db)
        executor.migrate([target])
        return executor.loader.project_state([target]).apps

    def state(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','index','trigger') AND name NOT LIKE 'sqlite_%' ORDER BY name")
            schema = cursor.fetchall()
            rows = {}
            for table in self.db.introspection.table_names():
                if table != "django_migrations":
                    cursor.execute("SELECT * FROM " + self.db.ops.quote_name(table) + " ORDER BY 1")
                    rows[table] = cursor.fetchall()
        return schema, rows

    def test_structural_migration_only_adds_three_empty_tables_and_preserves_v1(self):
        schema_before, rows_before = self.state()
        self.migrate(AFTER)
        schema_after, rows_after = self.state()
        self.assertTrue(set(schema_before).issubset(set(schema_after)))
        new_tables = {model._meta.db_table for model in TARGET_MODELS}
        self.assertEqual(set(rows_after) - set(rows_before), new_tables)
        self.assertEqual({table: rows_after[table] for table in rows_before}, rows_before)
        self.assertTrue(all(rows_after[table] == [] for table in new_tables))
        with self.db.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            self.assertEqual(cursor.fetchall(), [])

    def test_migration_operations_and_database_constraints_match_models(self):
        migration = import_module("apps.ecomotor.migrations.0006_target_catalog_preparation").Migration
        self.assertEqual(migration.dependencies, [BEFORE])
        self.assertTrue(all(type(operation) is CreateModel for operation in migration.operations))
        self.assertEqual({operation.name for operation in migration.operations}, {m.__name__ for m in TARGET_MODELS})
        historical = self.migrate(AFTER)
        with self.db.cursor() as cursor:
            for current_model in TARGET_MODELS:
                model = historical.get_model("ecomotor", current_model.__name__)
                constraints = self.db.introspection.get_constraints(cursor, model._meta.db_table)
                self.assertTrue({item.name for item in model._meta.constraints}.issubset(constraints))
                columns = self.db.introspection.get_table_description(cursor, model._meta.db_table)
                self.assertEqual({column.name for column in columns}, {field.column for field in model._meta.fields})

    def test_alternative_alias_reader_never_reads_default(self):
        executor = MigrationExecutor(self.db)
        executor.migrate(executor.loader.graph.leaf_nodes())
        catalog = synthetic_catalog(using=self.alias)
        with CaptureQueriesContext(connections["default"]) as queries:
            result = validate_target_catalog_version(catalog.pk, using=self.alias)
        self.assertEqual(len(queries), 0)
        self.assertEqual(result.catalog_version, "synthetic-r1")
