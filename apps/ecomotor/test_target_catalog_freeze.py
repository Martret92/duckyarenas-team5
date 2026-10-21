"""Synthetic catalogs, isolated files, real SQLite DML and overlapping writers."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, get_ident
from time import monotonic
from unittest import TestCase
from unittest.mock import patch

from django.db import IntegrityError, OperationalError, connections, transaction
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from . import target_catalog_freeze as freeze
from .models import EvolutionStage, LevelThreshold, TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from .target_catalog_validation import InvalidTargetCatalogError
from .test_target_catalog_persistence import synthetic_catalog

BEFORE = ("ecomotor", "0006_target_catalog_preparation")
AFTER = ("ecomotor", "0007_target_catalog_freeze")


class FileDatabase:
    target = AFTER

    def setUp(self):
        super().setUp()
        directory = TemporaryDirectory(prefix="ducky-freeze-")
        self.addCleanup(directory.cleanup)
        self.alias = "target_freeze_test"
        configuration = connections["default"].settings_dict.copy()
        configuration["NAME"] = str(Path(directory.name) / "test.sqlite3")
        configuration["OPTIONS"] = configuration["OPTIONS"].copy()
        connections.databases[self.alias] = configuration
        self.db = connections[self.alias]
        self.addCleanup(self.close_db)
        if isinstance(self, TransactionTestCase):
            previous = type(self).databases
            type(self).databases = previous | {self.alias}
            self.addCleanup(setattr, type(self), "databases", previous)
        self.migrate(self.target)

    def close_db(self):
        self.db.close()
        del connections[self.alias]
        del connections.databases[self.alias]

    def migrate(self, target):
        executor = MigrationExecutor(self.db)
        executor.migrate([target])
        return executor.loader.project_state([target]).apps

    def catalog(self, version="synthetic-v1"):
        return synthetic_catalog(using=self.alias, version=version)

    def call(self, pk):
        return freeze.freeze_target_catalog_version(pk, using=self.alias)

    def rows(self):
        with self.db.cursor() as cursor:
            result = {}
            for table in self.db.introspection.table_names():
                if table != "django_migrations":
                    cursor.execute("SELECT * FROM " + self.db.ops.quote_name(table) + " ORDER BY 1")
                    result[table] = cursor.fetchall()
            return result

    def sql(self, statement, params=()):
        with self.db.cursor() as cursor:
            cursor.execute(statement, params)

    def rejects(self, operation):
        before = self.rows()
        with self.assertRaisesRegex(IntegrityError, "Frozen catalog"), transaction.atomic(using=self.alias):
            operation()
        self.assertEqual(self.rows(), before)


class FreezeServiceTests(FileDatabase, TestCase):
    def setUp(self):
        super().setUp()
        self.version = self.catalog()

    def test_freeze_persists_server_date_and_immutable_result(self):
        now = timezone.now()
        with patch.object(freeze.timezone, "now", return_value=now):
            result = self.call(self.version.pk)
        self.version.refresh_from_db(using=self.alias)
        field = TargetCatalogVersion._meta.get_field("frozen_at")
        self.assertTrue(field.null and field.blank)
        self.assertFalse(field.auto_now or field.auto_now_add or field.has_default())
        self.assertEqual(result.frozen_at, now)
        self.assertEqual(self.version.frozen_at, now)
        self.assertEqual(result.catalog_version_id, self.version.pk)
        with self.assertRaises(FrozenInstanceError):
            result.frozen_at = None
        self.assertFalse(hasattr(result, "__dict__"))

    def test_repeat_revalidates_without_any_business_writes_or_new_clock(self):
        first = self.call(self.version.pk)
        with patch.object(freeze, "validate_target_catalog_version", wraps=freeze.validate_target_catalog_version) as reader:
            with patch.object(freeze.timezone, "now", side_effect=AssertionError("repeat clock")):
                with CaptureQueriesContext(self.db) as queries:
                    second = self.call(self.version.pk)
        self.assertEqual(first, second)
        reader.assert_called_once_with(self.version.pk, using=self.alias)
        self.assertFalse(any(q["sql"].upper().startswith(("UPDATE", "INSERT", "DELETE")) for q in queries))

    def test_repeat_of_directly_marked_invalid_catalog_rejected(self):
        TargetEpoch.objects.using(self.alias).filter(catalog=self.version, ordinal=7).delete()
        TargetCatalogVersion.objects.using(self.alias).filter(pk=self.version.pk).update(frozen_at=timezone.now())
        before = self.rows()
        with self.assertRaises(InvalidTargetCatalogError):
            self.call(self.version.pk)
        self.assertEqual(self.rows(), before)

    def test_incomplete_and_incoherent_catalogs_rejected_without_mark(self):
        TargetLevelThreshold.objects.using(self.alias).filter(catalog=self.version, level=8).delete()
        with self.assertRaises(InvalidTargetCatalogError):
            self.call(self.version.pk)
        other = self.catalog("synthetic-other")
        TargetEpoch.objects.using(self.alias).filter(catalog=other, ordinal=2).update(minimum_xp=14)
        with self.assertRaises(InvalidTargetCatalogError):
            self.call(other.pk)
        self.assertFalse(TargetCatalogVersion.objects.using(self.alias).exclude(frozen_at=None).exists())

    def test_invalid_identity_alias_and_missing_version_are_distinct(self):
        for pk in (None, True, 0, -1, 1.0, "1", 2**63):
            with self.subTest(pk=pk), self.assertRaises(InvalidTargetCatalogError):
                self.call(pk)
        for alias in (None, True, "", "missing"):
            with self.subTest(alias=alias), self.assertRaises(InvalidTargetCatalogError):
                freeze.freeze_target_catalog_version(self.version.pk, using=alias)
        with self.assertRaises(TargetCatalogVersion.DoesNotExist):
            self.call(999999)

    def test_outer_atomic_rejected_without_read_or_new_begin(self):
        with transaction.atomic(using=self.alias):
            with CaptureQueriesContext(self.db) as queries:
                with self.assertRaises(freeze.TargetCatalogFreezeTransactionError):
                    self.call(self.version.pk)
            self.assertEqual(len(queries), 0)

    def test_manual_transaction_and_incompatible_mode_rejected(self):
        self.db.set_autocommit(False)
        try:
            with self.assertRaises(freeze.TargetCatalogFreezeTransactionError):
                self.call(self.version.pk)
        finally:
            self.db.rollback()
            self.db.set_autocommit(True)
        for options in ({"transaction_mode": "DEFERRED", "timeout": 5},
                        {"transaction_mode": "IMMEDIATE", "timeout": 1}):
            with patch.dict(self.db.settings_dict, OPTIONS=options):
                with self.assertRaises(freeze.TargetCatalogFreezeTransactionError):
                    self.call(self.version.pk)
        with patch.object(self.db, "vendor", "postgresql"):
            with self.assertRaises(freeze.TargetCatalogFreezeTransactionError):
                self.call(self.version.pk)
        with patch.object(self.db, "transaction_mode", "DEFERRED"):
            with self.assertRaises(freeze.TargetCatalogFreezeTransactionError):
                self.call(self.version.pk)

    def test_update_and_validation_errors_roll_back_and_preserve_database_cause(self):
        save = TargetCatalogVersion.save
        error = OperationalError("synthetic write failure")
        def fail_after_save(version, *args, **kwargs):
            save(version, *args, **kwargs)
            raise error
        before = self.rows()
        with patch.object(TargetCatalogVersion, "save", fail_after_save):
            with self.assertRaises(OperationalError) as caught:
                self.call(self.version.pk)
        self.assertIs(caught.exception, error)
        self.assertEqual(self.rows(), before)
        with patch.object(freeze, "validate_target_catalog_version", side_effect=InvalidTargetCatalogError("synthetic")):
            with self.assertRaises(InvalidTargetCatalogError):
                self.call(self.version.pk)
        self.assertEqual(self.rows(), before)
        self.assertFalse(self.db.in_atomic_block)
        self.assertFalse(self.db.connection.in_transaction)
        self.call(self.version.pk)

    def test_only_frozen_at_changes_and_alias_is_respected(self):
        before = self.rows()
        with CaptureQueriesContext(connections["default"]) as default_queries:
            with CaptureQueriesContext(self.db) as queries:
                self.call(self.version.pk)
        self.assertEqual(len(default_queries), 0)
        writes = [q["sql"] for q in queries if q["sql"].upper().startswith(("UPDATE", "INSERT", "DELETE"))]
        self.assertEqual(len(writes), 1)
        self.assertIn('SET "frozen_at"', writes[0])
        after = self.rows()
        table = TargetCatalogVersion._meta.db_table
        self.assertEqual({k:v for k,v in before.items() if k != table}, {k:v for k,v in after.items() if k != table})
        self.assertEqual(before[table][0][:-1], after[table][0][:-1])


class FreezeTriggerTests(FileDatabase, TestCase):
    def setUp(self):
        super().setUp()
        self.frozen = self.catalog()
        self.preparatory = self.catalog("synthetic-v2")
        self.call(self.frozen.pk)

    def test_parent_insert_date_rejected_orm_bulk_and_sql(self):
        self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).create(catalog_id="synthetic-new", version="x", frozen_at=timezone.now()))
        self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).bulk_create([TargetCatalogVersion(catalog_id="synthetic-new", version="x", frozen_at=timezone.now())]))
        self.rejects(lambda: self.sql("INSERT INTO ecomotor_targetcatalogversion (catalog_id,version,frozen_at) VALUES (%s,%s,%s)", ["synthetic-new", "x", timezone.now()]))

    def test_all_parent_updates_and_delete_blocked_orm_and_sql(self):
        for field, value in (("frozen_at", None), ("frozen_at", timezone.now()), ("catalog_id", "changed"), ("version", "changed"), ("id", 999999)):
            with self.subTest(field=field):
                self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).filter(pk=self.frozen.pk).update(**{field:value}))
                self.rejects(lambda: self.sql(f"UPDATE ecomotor_targetcatalogversion SET {field}=%s WHERE id=%s", [value, self.frozen.pk]))
        self.rejects(lambda: self.sql("DELETE FROM ecomotor_targetcatalogversion WHERE id=%s", [self.frozen.pk]))
        # ORM collector uses PROTECT first while children exist; QuerySet.update
        # and SQL above demonstrate the trigger rather than ORM relation guards.
        empty = TargetCatalogVersion.objects.using(self.alias).create(catalog_id="synthetic-empty", version="x")
        TargetCatalogVersion.objects.using(self.alias).filter(pk=empty.pk).update(frozen_at=timezone.now())
        self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).filter(pk=empty.pk).delete())

    def test_mark_cannot_change_identity_or_pk_simultaneously(self):
        for field, value in (("catalog_id", "changed"), ("version", "changed"), ("id", 999999)):
            self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).filter(pk=self.preparatory.pk).update(frozen_at=timezone.now(), **{field:value}))
        # Direct marking is intentionally NOT a certificate that A1.1 ran.
        TargetCatalogVersion.objects.using(self.alias).filter(pk=self.preparatory.pk).update(frozen_at=timezone.now())
        self.assertIsNotNone(TargetCatalogVersion.objects.using(self.alias).get(pk=self.preparatory.pk).frozen_at)

    def test_children_insert_update_delete_and_both_transfer_directions(self):
        for model in (TargetLevelThreshold, TargetEpoch):
            table = model._meta.db_table
            frozen = model.objects.using(self.alias).filter(catalog=self.frozen).first()
            preparatory = model.objects.using(self.alias).filter(catalog=self.preparatory).first()
            extra = {"level":9} if model is TargetLevelThreshold else {"ordinal":7,"code":"synthetic-new","name":"Synthetic new"}
            self.rejects(lambda: model.objects.using(self.alias).create(catalog=self.frozen, minimum_xp=999, **extra))
            columns = ["catalog_id", "minimum_xp"] + list(extra)
            self.rejects(lambda: self.sql(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s']*len(columns))})", [self.frozen.pk,999]+list(extra.values())))
            for field, value in (("minimum_xp", 99), ("id", 999999)):
                self.rejects(lambda: model.objects.using(self.alias).filter(pk=frozen.pk).update(**{field:value}))
                self.rejects(lambda: self.sql(f"UPDATE {table} SET {field}=%s WHERE id=%s", [value,frozen.pk]))
            if model is TargetEpoch:
                self.rejects(lambda: model.objects.using(self.alias).filter(pk=frozen.pk).update(name="Synthetic display change"))
            for source, destination in ((frozen,self.preparatory),(preparatory,self.frozen)):
                self.rejects(lambda: model.objects.using(self.alias).filter(pk=source.pk).update(catalog=destination))
                self.rejects(lambda: self.sql(f"UPDATE {table} SET catalog_id=%s WHERE id=%s", [destination.pk,source.pk]))
            self.rejects(lambda: model.objects.using(self.alias).filter(pk=frozen.pk).delete())
            self.rejects(lambda: self.sql(f"DELETE FROM {table} WHERE id=%s", [frozen.pk]))

    def test_preparatory_versions_and_children_remain_editable(self):
        TargetCatalogVersion.objects.using(self.alias).filter(pk=self.preparatory.pk).update(version="synthetic-edit")
        for model in (TargetLevelThreshold, TargetEpoch):
            row = model.objects.using(self.alias).filter(catalog=self.preparatory).first()
            model.objects.using(self.alias).filter(pk=row.pk).update(minimum_xp=3)
            model.objects.using(self.alias).filter(pk=row.pk).delete()
        TargetLevelThreshold.objects.using(self.alias).filter(catalog=self.preparatory).delete()
        TargetEpoch.objects.using(self.alias).filter(catalog=self.preparatory).delete()
        self.preparatory.delete(using=self.alias)

    def test_replace_cannot_implicitly_delete_frozen_parent_or_child(self):
        self.rejects(lambda: self.sql("INSERT OR REPLACE INTO ecomotor_targetcatalogversion (id,catalog_id,version) VALUES (%s,%s,%s)", [self.frozen.pk,"synthetic-replaced","x"]))
        self.rejects(lambda: self.sql("INSERT OR REPLACE INTO ecomotor_targetcatalogversion (catalog_id,version) VALUES (%s,%s)", [self.frozen.catalog_id,self.frozen.version]))
        self.rejects(lambda: self.sql("UPDATE OR REPLACE ecomotor_targetcatalogversion SET catalog_id=%s,version=%s WHERE id=%s", [self.frozen.catalog_id,self.frozen.version,self.preparatory.pk]))
        for model in (TargetLevelThreshold, TargetEpoch):
            row = model.objects.using(self.alias).filter(catalog=self.frozen).first()
            other = model.objects.using(self.alias).filter(catalog=self.preparatory).first()
            table = model._meta.db_table
            extra = {"level":9} if model is TargetLevelThreshold else {"ordinal":7,"code":"synthetic-replace","name":"Synthetic"}
            columns = ["id","catalog_id","minimum_xp"]+list(extra)
            self.rejects(lambda: self.sql(f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s']*len(columns))})", [row.pk,self.preparatory.pk,999]+list(extra.values())))
            self.rejects(lambda: self.sql(f"UPDATE OR REPLACE {table} SET id=%s WHERE id=%s", [row.pk,other.pk]))


class FreezeMigrationTests(FileDatabase, TestCase):
    target = BEFORE

    def test_installation_preserves_rows_and_reverse_is_irreversible(self):
        old_apps = MigrationExecutor(self.db).loader.project_state([BEFORE]).apps
        version = old_apps.get_model("ecomotor", "TargetCatalogVersion").objects.using(self.alias).create(catalog_id="synthetic-old", version="r1")
        old_apps.get_model("ecomotor", "TargetLevelThreshold").objects.using(self.alias).create(catalog_id=version.pk,level=1,minimum_xp=0)
        old_apps.get_model("ecomotor", "TargetEpoch").objects.using(self.alias).create(catalog_id=version.pk,code="synthetic-old",name="Synthetic",ordinal=1,minimum_xp=0)
        LevelThreshold.objects.using(self.alias).create(level=1,minimum_xp=0,stat_points_awarded=13)
        EvolutionStage.objects.using(self.alias).create(code="synthetic-v1",name="Synthetic V1",ordinal=1,minimum_xp=0)
        user = old_apps.get_model("auth", "User").objects.using(self.alias).create(username="synthetic-freeze-migration")
        profile = old_apps.get_model("users", "UserProfileEcomotor").objects.using(self.alias).create(
            user_id=user.pk, historical_xp_total=13, current_level=2, current_stage_code="synthetic-v1")
        old_apps.get_model("ecomotor", "CharacterStats").objects.using(self.alias).create(
            profile_id=profile.pk, atk=1, def_stat=2, log_stat=3, spe=4, vel=5, int_stat=6, available_points=7)
        xp = old_apps.get_model("ecomotor", "XPEvent").objects.using(self.alias).create(
            profile_id=profile.pk,operation_key="synthetic-migration-freeze",amount=13,xp_before=0,xp_after=13)
        stage = EvolutionStage.objects.using(self.alias).get(code="synthetic-v1")
        old_apps.get_model("ecomotor", "EvolutionEvent").objects.using(self.alias).create(
            profile_id=profile.pk,xp_event_id=xp.pk,stage_id=stage.pk)
        before = self.rows()
        self.migrate(AFTER)
        after = self.rows()
        parent = TargetCatalogVersion._meta.db_table
        self.assertEqual({k:v for k,v in before.items() if k!=parent}, {k:v for k,v in after.items() if k!=parent})
        self.assertEqual(after[parent], [(*row,None) for row in before[parent]])
        with self.db.cursor() as cursor:
            cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            installed = cursor.fetchall()
        self.assertEqual(len(installed), 9)
        self.assertTrue(all("RAISE(ABORT" in sql for _,sql in installed))
        self.assertTrue(all("BEFORE" in sql for _,sql in installed))
        catalog = self.catalog()
        self.call(catalog.pk)
        protected = self.rows()
        with self.assertRaises(IrreversibleError):
            self.migrate(BEFORE)
        self.assertEqual(self.rows(),protected)
        with self.db.cursor() as cursor:
            cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            self.assertEqual(cursor.fetchall(),installed)
        self.rejects(lambda: TargetCatalogVersion.objects.using(self.alias).filter(pk=catalog.pk).update(frozen_at=None))
        self.assertIn(AFTER, MigrationExecutor(self.db).loader.applied_migrations)

    def test_operations_are_field_plus_irreversible_unsplit_trigger_statements(self):
        migration = import_module("apps.ecomotor.migrations.0007_target_catalog_freeze")
        self.assertEqual(migration.Migration.dependencies,[BEFORE])
        operations = migration.Migration.operations
        self.assertEqual([type(op).__name__ for op in operations],["AddField","RunSQL"])
        self.assertEqual(operations[0].name,"frozen_at")
        self.assertFalse(operations[1].reversible)
        self.assertEqual(len(operations[1].sql),9)
        self.assertTrue(all("SELECT RAISE(ABORT" in sql and sql.endswith("END") for sql,_ in operations[1].sql))


class FreezeConcurrencyTests(FileDatabase, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.version = self.catalog()

    def overlap(self, first_operation, second_operation):
        locked, attempted = Event(), Event()
        def worker(first, operation):
            db = connections[self.alias]
            statements=[]
            def observe(execute,sql,params,many,context):
                statements.append(sql)
                if first and sql.upper().startswith("SELECT") and not locked.is_set():
                    locked.set()
                    if not attempted.wait(4): raise AssertionError("Second BEGIN not attempted")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"):
                    attempted.set()
                return execute(sql,params,many,context)
            try:
                if not first and not locked.wait(4): raise AssertionError("First lock not held")
                with db.execute_wrapper(observe):
                    try: result=operation(db)
                    except (IntegrityError,InvalidTargetCatalogError,OperationalError) as error: result=error
                return result,get_ident(),id(db.connection),statements
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(worker,True,first_operation)
            b=pool.submit(worker,False,second_operation)
            results=[a.result(timeout=15),b.result(timeout=15)]
        self.assertNotEqual(results[0][1],results[1][1])
        self.assertNotEqual(results[0][2],results[1][2])
        for _,_,_,sql in results:
            self.assertLess(next(i for i,s in enumerate(sql) if s.upper().startswith("BEGIN IMMEDIATE")),next(i for i,s in enumerate(sql) if s.upper().startswith("SELECT")))
        return results[0][0],results[1][0]

    def test_two_freezes_serialize_and_return_same_date(self):
        before=self.rows()
        first,second=self.overlap(lambda db:self.call(self.version.pk),lambda db:self.call(self.version.pk))
        self.assertEqual(first,second)
        self.assertIsInstance(first,freeze.TargetCatalogFreezeResult)
        after=self.rows()
        parent=TargetCatalogVersion._meta.db_table
        self.assertEqual({k:v for k,v in before.items() if k!=parent},{k:v for k,v in after.items() if k!=parent})

    def compete(self, model, mutation_first, invalid):
        def mutate(db):
            with transaction.atomic(using=self.alias):
                row=model.objects.using(self.alias).filter(catalog=self.version).order_by("pk").first()
                if model is TargetEpoch:
                    values={"minimum_xp":1} if invalid else {"name":"Synthetic changed"}
                else:
                    row=model.objects.using(self.alias).get(catalog=self.version,level=8)
                    values={"minimum_xp":0 if invalid else 100}
                model.objects.using(self.alias).filter(pk=row.pk).update(**values)
            return "changed"
        freezer=lambda db:self.call(self.version.pk)
        first,second=self.overlap(mutate if mutation_first else freezer,freezer if mutation_first else mutate)
        self.version.refresh_from_db(using=self.alias)
        if mutation_first and invalid:
            self.assertEqual(first,"changed")
            self.assertIsInstance(second,InvalidTargetCatalogError)
            self.assertIsNone(self.version.frozen_at)
        elif mutation_first:
            self.assertEqual(first,"changed")
            self.assertIsInstance(second,freeze.TargetCatalogFreezeResult)
            self.assertIsNotNone(self.version.frozen_at)
        else:
            self.assertIsInstance(first,freeze.TargetCatalogFreezeResult)
            self.assertIsInstance(second,IntegrityError)
            self.assertIsNotNone(self.version.frozen_at)

    def test_freeze_wins_before_level_change(self): self.compete(TargetLevelThreshold,False,False)
    def test_freeze_wins_before_epoch_change(self): self.compete(TargetEpoch,False,False)
    def test_valid_level_change_wins_before_freeze(self): self.compete(TargetLevelThreshold,True,False)
    def test_valid_epoch_change_wins_before_freeze(self): self.compete(TargetEpoch,True,False)
    def test_invalid_level_change_wins_and_freeze_rejects(self): self.compete(TargetLevelThreshold,True,True)
    def test_invalid_epoch_change_wins_and_freeze_rejects(self): self.compete(TargetEpoch,True,True)

    def test_real_five_second_timeout_rolls_back_then_explicit_retry_succeeds(self):
        locked,attempted,release=Event(),Event(),Event()
        def holder():
            db=connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    locked.set()
                    if not release.wait(12): raise AssertionError("Release not signaled")
            finally: db.close()
        def contender():
            db=connections[self.alias]
            def observe(execute,sql,params,many,context):
                if sql.upper().startswith("BEGIN IMMEDIATE"): attempted.set()
                return execute(sql,params,many,context)
            try:
                start=monotonic()
                with db.execute_wrapper(observe):
                    with self.assertRaises(OperationalError): self.call(self.version.pk)
                elapsed=monotonic()-start
                self.assertFalse(db.in_atomic_block)
                self.assertFalse(db.connection.in_transaction)
                return elapsed
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            holding=pool.submit(holder)
            self.assertTrue(locked.wait(4))
            try:
                waiting=pool.submit(contender)
                self.assertTrue(attempted.wait(4))
                elapsed=waiting.result(timeout=10)
                self.assertGreaterEqual(elapsed,4.5)
            finally: release.set()
            holding.result(timeout=4)
        self.version.refresh_from_db(using=self.alias)
        self.assertIsNone(self.version.frozen_at)
        self.assertIsNotNone(self.call(self.version.pk).frozen_at)
