"""0002 → 0004 en SQLite temporal file-backed, sin revertir la BD local."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from django.db import connections
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


PREVIOUS = ("ecomotor", "0002_characterstats")
HISTORIES = ("ecomotor", "0003_xp_and_evolution_events")
USERS = ("users", "0002_ecomotor_progress")


class HistoryMigrationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-history-migrations-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "part_a_history_migration_test"
        configuration = connections["default"].settings_dict.copy()
        configuration["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        configuration["OPTIONS"] = {"transaction_mode": "IMMEDIATE", "timeout": 5}
        connections.databases[self.alias] = configuration
        self.connection = connections[self.alias]
        self.addCleanup(self.close_connection)
        executor = MigrationExecutor(self.connection)
        auth_targets = executor.loader.graph.leaf_nodes("auth")
        self.before_targets = [PREVIOUS] + auth_targets
        self.after_targets = [HISTORIES] + auth_targets
        apps = self.migrate(self.before_targets)
        user = apps.get_model("auth", "User").objects.using(self.alias).create(
            username="history-migration-test-user"
        )
        self.profile = apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).create(
            user_id=user.pk, current_level=2, current_stage_code="test-stage-2",
            historical_xp_total=34,
        )
        self.stage = apps.get_model("ecomotor", "EvolutionStage").objects.using(self.alias).create(
            code="test-stage-2", name="Etapa ficticia", ordinal=2, minimum_xp=19,
        )
        self.stats = apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).create(
            profile_id=self.profile.pk, atk=2, def_stat=3, log_stat=4,
            spe=6, vel=7, int_stat=8, available_points=9,
        )

    def close_connection(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self, targets):
        executor = MigrationExecutor(self.connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def schema(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type IN ('table', 'index') ORDER BY name"
            )
            return cursor.fetchall()

    def test_migrate_only_adds_two_tables_without_changing_existing_data(self):
        tables_before = set(self.connection.introspection.table_names())
        old_values = [self.profile.__dict__.copy(), self.stats.__dict__.copy(), self.stage.__dict__.copy()]
        apps = self.migrate(self.after_targets)
        tables_after = set(self.connection.introspection.table_names())
        self.assertEqual(tables_after - tables_before, {"ecomotor_xpevent", "ecomotor_evolutionevent"})
        self.assertEqual(tables_before - tables_after, set())
        for instance, values in zip([self.profile, self.stats, self.stage], old_values):
            instance.refresh_from_db(using=self.alias)
            for field in instance._meta.concrete_fields:
                self.assertEqual(getattr(instance, field.attname), values[field.attname])
        for name in ["XPEvent", "EvolutionEvent"]:
            self.assertEqual(apps.get_model("ecomotor", name).objects.using(self.alias).count(), 0)

    def test_final_schema_constraints_and_dependencies(self):
        self.migrate(self.after_targets)
        with self.connection.cursor() as cursor:
            xp_constraints = self.connection.introspection.get_constraints(cursor, "ecomotor_xpevent")
            evolution_constraints = self.connection.introspection.get_constraints(cursor, "ecomotor_evolutionevent")
            for table in ["ecomotor_xpevent", "ecomotor_evolutionevent"]:
                cursor.execute('PRAGMA table_info("' + table + '")')
                for row in cursor.fetchall():
                    self.assertEqual(row[3], 1, row[1])
                    self.assertIsNone(row[4], row[1])
        self.assertTrue(xp_constraints["ecomotor_xp_profile_key_unique"]["unique"])
        self.assertEqual(xp_constraints["ecomotor_xp_profile_key_unique"]["columns"], ["profile_id", "operation_key"])
        for name in ["ecomotor_xp_amount_positive", "ecomotor_xp_snapshot_sum", "ecomotor_xp_key_not_empty"]:
            self.assertTrue(xp_constraints[name]["check"])
        self.assertTrue(evolution_constraints["ecomotor_evolution_unique"]["unique"])
        self.assertEqual(evolution_constraints["ecomotor_evolution_unique"]["columns"], ["profile_id", "stage_id"])
        executor = MigrationExecutor(self.connection)
        self.assertEqual(set(executor.loader.get_migration(*HISTORIES).dependencies), {PREVIOUS, USERS})
        self.assertEqual(executor.loader.detect_conflicts(), {})
        self.assertEqual(executor.migration_plan(self.after_targets), [])

    def test_reversal_preserves_existing_histories_and_schema(self):
        apps = self.migrate(self.after_targets)
        event = apps.get_model("ecomotor", "XPEvent").objects.using(self.alias).create(
            profile_id=self.profile.pk, amount=23, xp_before=11, xp_after=34,
            operation_key="test-migration-operation",
        )
        evolution = apps.get_model("ecomotor", "EvolutionEvent").objects.using(self.alias).create(
            profile_id=self.profile.pk, stage_id=self.stage.pk, xp_event_id=event.pk,
        )
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.before_targets)
        self.assertEqual(self.schema(), before)
        event.refresh_from_db(using=self.alias)
        evolution.refresh_from_db(using=self.alias)
        self.assertEqual((event.amount, event.xp_before, event.xp_after), (23, 11, 34))
        self.assertEqual(event.operation_key, "test-migration-operation")
        self.assertEqual(evolution.xp_event_id, event.pk)
        self.assertIn(HISTORIES, MigrationRecorder(self.connection).applied_migrations())

    def test_reversal_is_also_blocked_with_empty_histories(self):
        self.migrate(self.after_targets)
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.before_targets)
        self.assertEqual(self.schema(), before)


PROGRESS = ("ecomotor", "0004_user_specialization_progress")


class SpecializationProgressMigrationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-domain-migrations-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "part_a_domain_migration_test"
        configuration = connections["default"].settings_dict.copy()
        configuration["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        configuration["OPTIONS"] = {"transaction_mode": "IMMEDIATE", "timeout": 5}
        connections.databases[self.alias] = configuration
        self.connection = connections[self.alias]
        self.addCleanup(self.close_connection)
        executor = MigrationExecutor(self.connection)
        auth_targets = executor.loader.graph.leaf_nodes("auth")
        self.before_targets = [HISTORIES] + auth_targets
        self.after_targets = [PROGRESS] + auth_targets
        apps = self.migrate(self.before_targets)

        def create(app, model_name, **fields):
            return apps.get_model(app, model_name).objects.using(self.alias).create(**fields)

        user = create("auth", "User", username="domain-migration-test-user")
        self.profile = create(
            "users", "UserProfileEcomotor", user_id=user.pk,
            historical_xp_total=34, current_level=2, current_stage_code="test-stage",
        )
        stats = create(
            "ecomotor", "CharacterStats", profile_id=self.profile.pk,
            atk=2, def_stat=3, log_stat=4, spe=6, vel=7, int_stat=8, available_points=9,
        )
        level = create("ecomotor", "LevelThreshold", level=1, minimum_xp=0, stat_points_awarded=0)
        stage = create("ecomotor", "EvolutionStage", code="test-stage", name="Etapa ficticia", ordinal=2, minimum_xp=19)
        self.specialization = create("ecomotor", "Specialization", code="test-spec", name="Especialización ficticia")
        xp = create("ecomotor", "XPEvent", profile_id=self.profile.pk, amount=23, xp_before=11, xp_after=34, operation_key="test-operation")
        evolution = create("ecomotor", "EvolutionEvent", profile_id=self.profile.pk, stage_id=stage.pk, xp_event_id=xp.pk)
        self.existing = [user, self.profile, stats, level, stage, self.specialization, xp, evolution]

    def close_connection(self):
        self.connection.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self, targets):
        executor = MigrationExecutor(self.connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def schema(self):
        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type IN ('table', 'index') ORDER BY name"
            )
            return cursor.fetchall()

    def test_migration_only_adds_progress_table_and_preserves_all_previous_rows(self):
        table = "ecomotor_userspecializationprogress"
        tables_before = set(self.connection.introspection.table_names())
        self.assertNotIn(table, tables_before)
        values_before = [
            {field.attname: getattr(row, field.attname) for field in row._meta.concrete_fields}
            for row in self.existing
        ]
        apps = self.migrate(self.after_targets)
        tables_after = set(self.connection.introspection.table_names())
        self.assertEqual(tables_after - tables_before, {table})
        self.assertEqual(tables_before - tables_after, set())
        for row, fields in zip(self.existing, values_before):
            row.refresh_from_db(using=self.alias)
            for name, value in fields.items():
                self.assertEqual(getattr(row, name), value)
            self.assertEqual(type(row).objects.using(self.alias).count(), 1)
        self.assertEqual(apps.get_model("ecomotor", "UserSpecializationProgress").objects.using(self.alias).count(), 0)

    def test_final_columns_foreign_keys_constraints_and_graph(self):
        apps = self.migrate(self.after_targets)
        table = "ecomotor_userspecializationprogress"
        with self.connection.cursor() as cursor:
            cursor.execute('PRAGMA table_info("' + table + '")')
            columns = cursor.fetchall()
            constraints = self.connection.introspection.get_constraints(cursor, table)
        self.assertEqual({row[1] for row in columns}, {"id", "profile_id", "specialization_id", "domain_xp_total"})
        self.assertTrue(all(row[3] == 1 for row in columns))
        self.assertTrue(constraints["ecomotor_progress_profile_spec"]["unique"])
        self.assertEqual(constraints["ecomotor_progress_profile_spec"]["columns"], ["profile_id", "specialization_id"])
        self.assertTrue(constraints["ecomotor_domain_xp_nonnegative"]["check"])
        self.assertEqual(
            {value["foreign_key"] for value in constraints.values() if value["foreign_key"]},
            {("users_userprofileecomotor", "id"), ("ecomotor_specialization", "id")},
        )
        field = apps.get_model("ecomotor", "UserSpecializationProgress")._meta.get_field("domain_xp_total")
        self.assertEqual(field.default, 0)
        executor = MigrationExecutor(self.connection)
        self.assertEqual(set(executor.loader.get_migration(*PROGRESS).dependencies), {HISTORIES, USERS})
        self.assertEqual(executor.loader.detect_conflicts(), {})
        self.assertEqual(executor.migration_plan(self.after_targets), [])

    def test_empty_progress_table_cannot_be_reversed(self):
        self.migrate(self.after_targets)
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.before_targets)
        self.assertEqual(self.schema(), before)
        self.assertIn(PROGRESS, MigrationRecorder(self.connection).applied_migrations())

    def test_reversal_preserves_existing_domain_progress_and_schema(self):
        apps = self.migrate(self.after_targets)
        progress = apps.get_model("ecomotor", "UserSpecializationProgress").objects.using(self.alias).create(
            profile_id=self.profile.pk, specialization_id=self.specialization.pk, domain_xp_total=53,
        )
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.before_targets)
        progress.refresh_from_db(using=self.alias)
        self.assertEqual(progress.domain_xp_total, 53)
        self.assertEqual(progress.profile_id, self.profile.pk)
        self.assertEqual(progress.specialization_id, self.specialization.pk)
        self.assertEqual(self.schema(), before)
        self.assertIn(PROGRESS, MigrationRecorder(self.connection).applied_migrations())
