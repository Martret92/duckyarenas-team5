"""Migraciones reales en SQLite file-backed aislada; nunca revierten db.sqlite3."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from django.db import IntegrityError, connections, transaction
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


USERS_INITIAL = ("users", "0001_initial")
USERS_PROGRESS = ("users", "0002_ecomotor_progress")
ECOMOTOR_INITIAL = ("ecomotor", "0001_initial")
ECOMOTOR_STATS = ("ecomotor", "0002_characterstats")


class ProgressMigrationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="ducky-migrations-")
        self.addCleanup(self.directory.cleanup)
        self.alias = "part_a_migration_test"
        configuration = connections["default"].settings_dict.copy()
        configuration["NAME"] = str(Path(self.directory.name) / "test.sqlite3")
        configuration["OPTIONS"] = {"transaction_mode": "IMMEDIATE", "timeout": 5}
        connections.databases[self.alias] = configuration
        self.connection = connections[self.alias]
        self.addCleanup(self.close_connection)
        executor = MigrationExecutor(self.connection)
        self.auth_targets = executor.loader.graph.leaf_nodes("auth")
        self.initial_targets = [USERS_INITIAL, ECOMOTOR_INITIAL] + self.auth_targets
        self.progress_targets = [USERS_PROGRESS, ECOMOTOR_INITIAL] + self.auth_targets
        self.final_targets = [ECOMOTOR_STATS] + self.auth_targets
        self.old_apps = self.migrate(self.initial_targets)

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

    def create_user(self):
        return self.old_apps.get_model("auth", "User").objects.using(self.alias).create(
            username="migration-test-user"
        )

    def create_progress(self, apps):
        user = self.create_user()
        return apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).create(
            user_id=user.pk, historical_xp_total=23,
            current_level=2, current_stage_code="test-stage",
        )

    def test_new_database_migrates_without_creating_profiles_or_stats(self):
        apps = self.migrate(self.final_targets)
        for app, model in [
            ("auth", "User"), ("users", "UserProfileEcomotor"),
            ("users", "UserProfileBank"), ("ecomotor", "CharacterStats"),
        ]:
            self.assertEqual(apps.get_model(app, model).objects.using(self.alias).count(), 0)

    def test_existing_user_without_profile_is_preserved(self):
        user = self.create_user()
        apps = self.migrate(self.final_targets)
        self.assertTrue(apps.get_model("auth", "User").objects.using(self.alias).filter(pk=user.pk).exists())
        self.assertEqual(apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).count(), 0)
        self.assertEqual(apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).count(), 0)

    def test_bank_profile_does_not_trigger_m01(self):
        user = self.create_user()
        bank = self.old_apps.get_model("users", "UserProfileBank").objects.using(self.alias).create(user_id=user.pk)
        apps = self.migrate(self.final_targets)
        self.assertTrue(apps.get_model("users", "UserProfileBank").objects.using(self.alias).filter(pk=bank.pk, user_id=user.pk).exists())
        self.assertEqual(apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).count(), 0)

    def test_legacy_profile_aborts_before_any_schema_change(self):
        user = self.create_user()
        profile_model = self.old_apps.get_model("users", "UserProfileEcomotor")
        profile = profile_model.objects.using(self.alias).create(user_id=user.pk)
        before_schema = self.schema()
        before_records = set(MigrationRecorder(self.connection).applied_migrations())
        statements = []
        self.connection.connection.set_trace_callback(statements.append)
        try:
            with self.assertRaisesRegex(RuntimeError, "M-01"):
                self.migrate(self.final_targets)
        finally:
            self.connection.connection.set_trace_callback(None)
        self.assertEqual(self.schema(), before_schema)
        self.assertEqual(set(MigrationRecorder(self.connection).applied_migrations()), before_records)
        self.assertEqual(list(profile_model.objects.using(self.alias).values_list("id", "user_id")), [(profile.pk, user.pk)])
        self.assertFalse(any(sql.lstrip().upper().startswith(("CREATE ", "ALTER ", "DROP ")) for sql in statements))

    def test_failure_after_schema_changes_rolls_back_entire_users_migration(self):
        before = self.schema()
        executor = MigrationExecutor(self.connection)
        migration = executor.loader.get_migration(*USERS_PROGRESS)
        self.assertTrue(migration.atomic)
        self.assertTrue(self.connection.features.can_rollback_ddl)
        # Fallo al final: las columnas y constraints ya se han creado temporalmente.
        with patch.object(migration.operations[-1], "code", side_effect=RuntimeError("test failure")):
            with self.assertRaisesRegex(RuntimeError, "test failure"):
                executor.migrate(self.progress_targets)
        self.assertEqual(self.schema(), before)
        self.assertNotIn(USERS_PROGRESS, MigrationRecorder(self.connection).applied_migrations())
        self.migrate(self.final_targets)

    def test_final_schema_and_constraints(self):
        apps = self.migrate(self.final_targets)
        profile_model = apps.get_model("users", "UserProfileEcomotor")
        stats_model = apps.get_model("ecomotor", "CharacterStats")
        with self.connection.cursor() as cursor:
            cursor.execute('PRAGMA table_info("users_userprofileecomotor")')
            fields = {row[1]: row for row in cursor.fetchall()}
            cursor.execute('PRAGMA table_info("ecomotor_characterstats")')
            stats_fields = {row[1]: row for row in cursor.fetchall()}
        for name in ["historical_xp_total", "current_level", "current_stage_code"]:
            self.assertEqual(fields[name][3], 1, name)
        self.assertEqual(fields["active_specialization_code"][3], 0)
        for name in ["current_level", "current_stage_code"]:
            self.assertIsNone(fields[name][4], name)
            self.assertFalse(profile_model._meta.get_field(name).has_default())
        for name in ["atk", "def_stat", "log_stat", "spe", "vel", "int_stat", "available_points"]:
            self.assertEqual(stats_fields[name][3], 1, name)
            self.assertIsNone(stats_fields[name][4], name)
            self.assertFalse(stats_model._meta.get_field(name).has_default())
        user = self.create_user()
        for field, value in [("current_level", 0), ("historical_xp_total", -1), ("current_stage_code", "")]:
            values = dict(user_id=user.pk, current_level=1, current_stage_code="test-stage")
            values[field] = value
            with self.subTest(field=field):
                with self.assertRaises(IntegrityError), transaction.atomic(using=self.alias):
                    profile_model.objects.using(self.alias).create(**values)

    def test_dependencies_and_no_pending_migrations_for_both_apps(self):
        self.migrate(self.final_targets)
        executor = MigrationExecutor(self.connection)
        self.assertEqual(executor.loader.detect_conflicts(), {})
        self.assertEqual(set(executor.loader.get_migration(*ECOMOTOR_STATS).dependencies), {ECOMOTOR_INITIAL, USERS_PROGRESS})
        self.assertEqual(executor.migration_plan(self.final_targets), [])

    def test_users_reversal_cannot_remove_existing_progress(self):
        apps = self.migrate(self.progress_targets)
        profile = self.create_progress(apps)
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.initial_targets)
        profile.refresh_from_db(using=self.alias)
        self.assertEqual(profile.historical_xp_total, 23)
        self.assertEqual(profile.current_level, 2)
        self.assertEqual(profile.current_stage_code, "test-stage")
        self.assertEqual(self.schema(), before)
        self.assertIn(USERS_PROGRESS, MigrationRecorder(self.connection).applied_migrations())

    def test_stats_reversal_cannot_remove_existing_statistics(self):
        apps = self.migrate(self.final_targets)
        profile = self.create_progress(apps)
        stats = apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).create(
            profile_id=profile.pk, atk=2, def_stat=3, log_stat=4,
            spe=6, vel=7, int_stat=8, available_points=9,
        )
        before = self.schema()
        with self.assertRaises(IrreversibleError):
            self.migrate(self.progress_targets)
        stats.refresh_from_db(using=self.alias)
        self.assertEqual(stats.available_points, 9)
        self.assertEqual([stats.atk, stats.def_stat, stats.log_stat, stats.spe, stats.vel, stats.int_stat], [2, 3, 4, 6, 7, 8])
        self.assertEqual(self.schema(), before)
        self.assertIn(ECOMOTOR_STATS, MigrationRecorder(self.connection).applied_migrations())

    def test_empty_migrations_are_also_irreversible(self):
        self.migrate(self.final_targets)
        with self.assertRaises(IrreversibleError):
            self.migrate(self.progress_targets)
