"""0004 → 0005 en archivo temporal; nunca revierte la BD del desarrollador."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from django.db import IntegrityError, connections, transaction
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


BEFORE = ("ecomotor", "0004_user_specialization_progress")
AFTER = ("ecomotor", "0005_stat_allocation_event")


class StatAllocationMigrationTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="s7-migration-")
        self.addCleanup(directory.cleanup)
        self.alias = "s7_migration_test"
        settings = connections["default"].settings_dict.copy()
        settings["NAME"] = str(Path(directory.name) / "test.sqlite3")
        connections.databases[self.alias] = settings
        self.db = connections[self.alias]
        self.addCleanup(self.close_database)
        executor = MigrationExecutor(self.db)
        self.auth = executor.loader.graph.leaf_nodes("auth")
        apps = self.migrate(BEFORE)
        user = apps.get_model("auth", "User").objects.using(self.alias).create(username="s7-migration-only")
        profile = apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).create(
            user_id=user.pk, historical_xp_total=123, current_level=3, current_stage_code="test-actual")
        self.profile_id = profile.pk
        apps.get_model("users", "UserProfileBank").objects.using(self.alias).create(user_id=user.pk)
        apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).create(
            profile_id=profile.pk, atk=-2, def_stat=3, log_stat=4, spe=6, vel=7, int_stat=8, available_points=9)
        stage = apps.get_model("ecomotor", "EvolutionStage").objects.using(self.alias).create(
            ordinal=7, code="test-actual", name="Ficticia", minimum_xp=100)
        apps.get_model("ecomotor", "LevelThreshold").objects.using(self.alias).create(
            level=1, minimum_xp=0, stat_points_awarded=7)
        xp = apps.get_model("ecomotor", "XPEvent").objects.using(self.alias).create(
            profile_id=profile.pk, amount=123, xp_before=0, xp_after=123, operation_key="migration-xp")
        apps.get_model("ecomotor", "EvolutionEvent").objects.using(self.alias).create(
            profile_id=profile.pk, stage_id=stage.pk, xp_event_id=xp.pk)
        spec = apps.get_model("ecomotor", "Specialization").objects.using(self.alias).create(code="test-spec", name="Ficticia")
        apps.get_model("ecomotor", "UserSpecializationProgress").objects.using(self.alias).create(
            profile_id=profile.pk, specialization_id=spec.pk, domain_xp_total=3)

    def close_database(self):
        self.db.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self, target):
        executor = MigrationExecutor(self.db)
        executor.migrate([target] + self.auth)
        return executor.loader.project_state([target] + self.auth).apps

    def snapshot(self):
        result = {}
        with self.db.cursor() as cursor:
            for table in self.db.introspection.table_names():
                if table != "django_migrations":
                    cursor.execute("SELECT * FROM " + self.db.ops.quote_name(table) + " ORDER BY 1")
                    result[table] = cursor.fetchall()
        return result

    def test_adds_only_one_table_preserves_all_existing_rows_and_no_seeds(self):
        before = self.snapshot()
        apps = self.migrate(AFTER)
        after = self.snapshot()
        self.assertEqual(set(after) - set(before), {"ecomotor_statallocationevent"})
        self.assertEqual({key: after[key] for key in before}, before)
        self.assertEqual(apps.get_model("ecomotor", "StatAllocationEvent").objects.using(self.alias).count(), 0)

    def test_schema_constraints_foreign_key_and_graph(self):
        apps = self.migrate(AFTER)
        executor = MigrationExecutor(self.db)
        executor.loader.graph.validate_consistency()
        self.assertIn(BEFORE, {node.key for node in executor.loader.graph.node_map[AFTER].parents})
        self.assertFalse(executor.migration_plan(executor.loader.graph.leaf_nodes("ecomotor")))
        event = apps.get_model("ecomotor", "StatAllocationEvent")
        with self.db.cursor() as cursor:
            constraints = self.db.introspection.get_constraints(cursor, event._meta.db_table)
            columns = self.db.introspection.get_table_description(cursor, event._meta.db_table)
        self.assertEqual({column.name for column in columns}, {field.column for field in event._meta.fields})
        for constraint in event._meta.constraints:
            self.assertIn(constraint.name, constraints)
        self.assertTrue(any(c["foreign_key"] == ("users_userprofileecomotor", "id") for c in constraints.values()))
        self.assertIsNotNone(event._meta.get_field("created_at"))

    def create_event(self, apps, **changes):
        values = dict(profile_id=self.profile_id, operation_key="s7-migration-event", attribute="atk",
                      points_spent=2, increase_applied=2, available_points_before=9, available_points_after=7,
                      attribute_before=-2, attribute_after=0, stage_code_at_allocation="test-actual")
        return apps.get_model("ecomotor", "StatAllocationEvent").objects.using(self.alias).create(**(values | changes))

    def test_real_constraints_on_migrated_schema(self):
        apps = self.migrate(AFTER)
        self.create_event(apps)
        for changes in ({}, {"operation_key": ""}, {"operation_key": "new", "attribute_after": 3},
                        {"operation_key": "new", "available_points_after": -1}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic(using=self.alias):
                self.create_event(apps, **changes)

    def test_reversal_blocked_even_when_empty(self):
        self.migrate(AFTER)
        before = self.snapshot()
        with self.assertRaises(IrreversibleError):
            self.migrate(BEFORE)
        self.assertEqual(self.snapshot(), before)
        self.assertIn(AFTER, MigrationRecorder(self.db).applied_migrations())

    def test_reversal_preserves_history_data_and_schema(self):
        apps = self.migrate(AFTER)
        self.create_event(apps)
        before = self.snapshot()
        with self.assertRaises(IrreversibleError):
            self.migrate(BEFORE)
        self.assertEqual(self.snapshot(), before)
