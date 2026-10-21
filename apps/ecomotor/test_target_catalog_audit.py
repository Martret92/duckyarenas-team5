"""Synthetic file-backed audits. DDL corruption exists only in disposable files."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from importlib import import_module
from io import StringIO
from threading import Event, get_ident
from time import monotonic
from unittest import TestCase
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from . import target_catalog_audit as audit
from .models import TargetCatalogVersion, TargetEpoch, TargetLevelThreshold
from .target_catalog_freeze import freeze_target_catalog_version
from .test_target_catalog_freeze import FileDatabase
from .test_target_catalog_persistence import synthetic_catalog
from .test_xp_service import create_xp_catalogs, create_xp_profile

REFERENCE = tuple(import_module("apps.ecomotor.migrations.0007_target_catalog_freeze").TRIGGERS)
NOTICE = "CONFORMIDAD TÉCNICA OBSERVADA — No constituye autorización funcional ni habilita concesiones XP."
COMMAND_MODULE = "apps.ecomotor.management.commands.audit_target_catalog"


class AuditDatabase(FileDatabase):
    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(self.db)
        executor.migrate(executor.loader.graph.leaf_nodes())
        self.version = synthetic_catalog(using=self.alias)

    def observe(self, pk=None):
        return audit.audit_target_catalog(self.version.pk if pk is None else pk, using=self.alias)

    def codes(self, result):
        return tuple(check.issue_code for check in result.issues)

    def trigger_name(self, sql):
        return sql.split()[2]

    def drop_trigger(self, reference):
        with connections[self.alias].cursor() as cursor:
            cursor.execute('DROP TRIGGER "' + self.trigger_name(reference) + '"')

    def schema(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
            return cursor.fetchall()

    def command(self, stdout=None, **options):
        output = StringIO() if stdout is None else stdout
        call_command("audit_target_catalog", "--catalog-version-id", str(self.version.pk),
                     "--database", self.alias, stdout=output, **options)
        return output.getvalue()


class CatalogAuditTests(AuditDatabase, TestCase):
    def test_complete_preparatory_catalog_and_all_nine_exact_triggers(self):
        result = self.observe()
        self.assertTrue(result.technically_conformant)
        self.assertEqual(result.issues, ())
        self.assertEqual((result.using,result.catalog_version_id),(self.alias,self.version.pk))
        self.assertEqual((result.catalog_id,result.version),(self.version.catalog_id,self.version.version))
        self.assertIs(result.state, audit.CatalogAuditState.PREPARATORY)
        self.assertIsNone(result.frozen_at)
        triggers = [c for c in result.checks if c.name == "TRIGGER"]
        self.assertEqual({c.subject for c in triggers},{self.trigger_name(s) for s in REFERENCE})
        self.assertEqual(len(triggers),9)
        self.assertTrue(all(c.passed for c in result.checks))

    def test_frozen_catalog_valid_but_not_an_authorization(self):
        frozen = freeze_target_catalog_version(self.version.pk,using=self.alias)
        result = self.observe()
        self.assertTrue(result.technically_conformant)
        self.assertIs(result.state,audit.CatalogAuditState.FROZEN)
        self.assertEqual(result.frozen_at,self.db.ops.adapt_datetimefield_value(frozen.frozen_at))
        self.assertFalse(hasattr(result,"authorized"))
        self.assertFalse(hasattr(result,"published"))

    def test_each_missing_trigger_detected_even_with_migration_record(self):
        for reference in REFERENCE:
            with self.subTest(trigger=self.trigger_name(reference)):
                self.drop_trigger(reference)
                result = self.observe()
                self.assertEqual(self.codes(result),("TRIGGER_MISSING",))
                self.assertEqual(result.issues[0].subject,self.trigger_name(reference))
                self.assertFalse(result.technically_conformant)
                self.assertTrue(next(c for c in result.checks if c.name=="MIGRATION_0007").passed)
                self.sql(reference)

    def test_sql_semantic_changes_never_accepted_by_name(self):
        mutations = ((0," OR EXISTS"," AND EXISTS"),(1,"OLD.frozen_at","NEW.frozen_at"),
                     (0,"NEW.frozen_at","NEW.version"),(0,"RAISE(ABORT","RAISE(FAIL"),
                     (0,"id = NEW.id","id != NEW.id"),(0,"is forbidden","is  forbidden"))
        for index,original,changed in mutations:
            reference=REFERENCE[index]
            with self.subTest(change=changed):
                self.drop_trigger(reference)
                altered=reference.replace(original,changed)
                self.assertNotEqual(altered,reference)
                self.sql(altered)
                result=self.observe()
                self.assertEqual(self.codes(result),("TRIGGER_SQL_MISMATCH",))
                self.assertFalse(result.technically_conformant)
                self.drop_trigger(reference)
                self.sql(reference)

    def test_wrong_target_table_detected(self):
        reference=REFERENCE[0]
        self.drop_trigger(reference)
        self.sql(reference.replace("ON ecomotor_targetcatalogversion","ON ecomotor_targetepoch",1))
        result=self.observe()
        self.assertEqual(self.codes(result),("TRIGGER_SQL_MISMATCH",))

    def test_unexpected_trigger_on_protected_table_is_not_favorable(self):
        self.sql("CREATE TRIGGER synthetic_extra BEFORE UPDATE ON ecomotor_targetcatalogversion BEGIN SELECT RAISE(IGNORE); END")
        result=self.observe()
        self.assertIn("TRIGGER_SQL_MISMATCH",self.codes(result))
        self.assertFalse(result.technically_conformant)

    def test_composite_pk_cannot_impersonate_exact_version_identity(self):
        self.sql("DROP TABLE ecomotor_targetlevelthreshold")
        self.sql("CREATE TABLE ecomotor_targetlevelthreshold (id INTEGER NOT NULL, catalog_id BIGINT NOT NULL REFERENCES ecomotor_targetcatalogversion(id), level INTEGER UNSIGNED NOT NULL, minimum_xp BIGINT UNSIGNED NOT NULL, extra INTEGER, PRIMARY KEY(id,extra))")
        with patch.object(audit,"validate_target_catalog_version",side_effect=AssertionError("reader called")):
            result=self.observe()
        self.assertTrue(any("primary_key" in issue.subject for issue in result.issues))
        self.assertFalse(result.technically_conformant)

    def test_only_outer_whitespace_and_final_delimiter_tolerated(self):
        reference=REFERENCE[0]
        self.drop_trigger(reference)
        self.sql("  "+reference+"  ;  ")
        self.assertTrue(self.observe().technically_conformant)
        self.drop_trigger(reference)
        self.sql(reference.replace("WHEN NEW", "WHEN  NEW",1))
        self.assertIn("TRIGGER_SQL_MISMATCH",self.codes(self.observe()))

    def test_record_missing_with_intact_schema_and_triggers(self):
        self.sql("DELETE FROM django_migrations WHERE app='ecomotor' AND name='0007_target_catalog_freeze'")
        result=self.observe()
        self.assertEqual(self.codes(result),("MIGRATION_0007_MISSING",))
        self.assertFalse(result.technically_conformant)
        self.assertTrue(next(c for c in result.checks if c.name=="CATALOG_A1_1").passed)

    def test_migration_registry_missing_never_created(self):
        self.sql("DROP TABLE django_migrations")
        before=self.schema()
        result=self.observe()
        self.assertIn("SCHEMA_INCOMPLETE",self.codes(result))
        self.assertIn("MIGRATION_0007_MISSING",self.codes(result))
        self.assertEqual(self.schema(),before)
        self.assertNotIn("django_migrations",self.db.introspection.table_names())

    def test_migration_registry_columns_missing_are_diagnostics_not_sql_error(self):
        self.sql("ALTER TABLE django_migrations RENAME COLUMN app TO synthetic_wrong")
        result=self.observe()
        self.assertIn("SCHEMA_INCOMPLETE",self.codes(result))
        self.assertIn("MIGRATION_0007_MISSING",self.codes(result))

    def test_missing_table_prevents_reader_and_retains_all_problems(self):
        self.sql("DROP TABLE ecomotor_targetlevelthreshold")
        with patch.object(audit,"validate_target_catalog_version",side_effect=AssertionError("reader called")):
            result=self.observe()
        self.assertIn("SCHEMA_INCOMPLETE",self.codes(result))
        self.assertEqual(self.codes(result).count("TRIGGER_MISSING"),3)
        self.assertIs(result.state,audit.CatalogAuditState.UNOBSERVED)

    def test_each_required_column_missing_prevents_orm_read(self):
        for model in (TargetCatalogVersion,TargetLevelThreshold,TargetEpoch):
            for field in model._meta.local_fields:
                table=model._meta.db_table
                with self.subTest(table=table,column=field.column):
                    self.sql(f'ALTER TABLE "{table}" RENAME COLUMN "{field.column}" TO synthetic_wrong')
                    with patch.object(audit,"validate_target_catalog_version",side_effect=AssertionError("reader called")):
                        result=self.observe()
                    self.assertIn("SCHEMA_INCOMPLETE",self.codes(result))
                    self.assertFalse(result.technically_conformant)
                    self.sql(f'ALTER TABLE "{table}" RENAME COLUMN synthetic_wrong TO "{field.column}"')

    def test_incompatible_column_type_nullability_pk_or_foreign_key_rejected(self):
        self.sql("DROP TABLE ecomotor_targetlevelthreshold")
        self.sql("CREATE TABLE ecomotor_targetlevelthreshold (id INTEGER, catalog_id INTEGER, level TEXT, minimum_xp BIGINT UNSIGNED)")
        with patch.object(audit,"validate_target_catalog_version",side_effect=AssertionError("reader called")):
            result=self.observe()
        issue=next(c for c in result.issues if c.name=="SCHEMA")
        for column in ("id","catalog_id","level","minimum_xp","catalog_fk"):
            self.assertIn(column,issue.subject)

    def test_catalog_incomplete_and_frozen_invalid_are_never_favorable(self):
        TargetEpoch.objects.using(self.alias).filter(catalog=self.version,ordinal=7).delete()
        for frozen in (False,True):
            if frozen:
                TargetCatalogVersion.objects.using(self.alias).filter(pk=self.version.pk).update(frozen_at=timezone.now())
            result=self.observe()
            self.assertEqual(self.codes(result),("CATALOG_INVALID",))
            self.assertFalse(result.technically_conformant)
            self.assertEqual(result.state is audit.CatalogAuditState.FROZEN,frozen)

    def test_invalid_observed_date_is_not_a_preparatory_or_favorable_catalog(self):
        self.sql("UPDATE ecomotor_targetcatalogversion SET frozen_at='synthetic-not-a-date' WHERE id=%s",[self.version.pk])
        result=self.observe()
        self.assertIs(result.state,audit.CatalogAuditState.FROZEN)
        self.assertIn("CATALOG_INVALID",self.codes(result))
        self.assertFalse(result.technically_conformant)

    def test_requested_identity_is_not_replaced_by_other_catalog(self):
        other=synthetic_catalog(using=self.alias,catalog_id="synthetic-other")
        result=self.observe(pk=other.pk)
        self.assertEqual((result.catalog_version_id,result.catalog_id),(other.pk,"synthetic-other"))
        missing=self.observe(pk=999999)
        self.assertEqual(self.codes(missing),("CATALOG_NOT_FOUND",))
        self.assertIsNone(missing.catalog_id)
        self.assertIs(missing.state,audit.CatalogAuditState.UNOBSERVED)

    def test_invalid_pk_alias_and_transactions_rejected_explicitly(self):
        for pk in (True,None,0,-1,1.0,"1",{},2**63):
            with self.subTest(pk=pk),self.assertRaises(audit.InvalidTargetCatalogAuditInputError):
                audit.audit_target_catalog(pk,using=self.alias)
        for alias in (None,True,"","unknown",{},1):
            with self.subTest(alias=alias),self.assertRaises(audit.InvalidTargetCatalogAuditInputError):
                audit.audit_target_catalog(self.version.pk,using=alias)
        with transaction.atomic(using=self.alias),CaptureQueriesContext(self.db) as queries:
            with self.assertRaises(audit.TargetCatalogAuditTransactionError): self.observe()
            self.assertEqual(len(queries),0)
        self.db.set_autocommit(False)
        try:
            with self.assertRaises(audit.TargetCatalogAuditTransactionError): self.observe()
        finally:
            self.db.rollback();self.db.set_autocommit(True)
        for options in ({"transaction_mode":"DEFERRED","timeout":5},{"transaction_mode":"IMMEDIATE","timeout":1}):
            with patch.dict(self.db.settings_dict,OPTIONS=options),self.assertRaises(audit.TargetCatalogAuditTransactionError): self.observe()
        with patch.object(self.db,"vendor","postgresql"),self.assertRaises(audit.TargetCatalogAuditTransactionError): self.observe()

    def test_sql_and_connection_errors_propagate_without_diagnostics(self):
        error=OperationalError("synthetic database error")
        def fail(execute,sql,params,many,context):
            if sql.upper().startswith("SELECT"): raise error
            return execute(sql,params,many,context)
        with self.db.execute_wrapper(fail),self.assertRaises(OperationalError) as caught: self.observe()
        self.assertIs(caught.exception,error)
        self.assertFalse(self.db.in_atomic_block)
        self.assertFalse(self.db.connection.in_transaction)
        with patch.object(self.db,"ensure_connection",side_effect=error),self.assertRaises(OperationalError): self.observe()
        self.assertTrue(self.observe().technically_conformant)

    def test_unexpected_programming_errors_are_not_hidden(self):
        with patch.object(audit,"validate_target_catalog_version",side_effect=TypeError("synthetic bug")):
            with self.assertRaises(TypeError): self.observe()

    def test_immutable_results_defensive_tuple_and_determinism(self):
        result=self.observe()
        self.assertEqual(result,self.observe())
        for obj,field in ((result,"catalog_id"),(result.checks[0],"subject")):
            with self.assertRaises(FrozenInstanceError): setattr(obj,field,"changed")
            self.assertFalse(hasattr(obj,"__dict__"))
        values=list(result.checks)
        copied=replace(result,checks=values)
        values.clear()
        self.assertEqual(copied,result)
        with self.assertRaises(ValueError): replace(result,checks=[["mutable"]])
        with self.assertRaises(ValueError): replace(result,checks="invalid")
        self.assertFalse(replace(result,checks=()).technically_conformant)

    def test_no_dml_ddl_freeze_preview_or_business_calls_and_alias_respected(self):
        create_xp_catalogs(self.alias)
        create_xp_profile(self.alias,username="synthetic-catalog-audit")
        before=self.rows(),self.schema()
        for frozen in (False,True):
            if frozen:
                freeze_target_catalog_version(self.version.pk,using=self.alias)
                before=self.rows(),self.schema()
            with patch("apps.ecomotor.target_catalog_freeze.freeze_target_catalog_version",side_effect=AssertionError),patch("apps.ecomotor.target_xp_preview.preview_target_xp",side_effect=AssertionError),patch("apps.ecomotor.xp_service.grant_historical_xp",side_effect=AssertionError):
                with CaptureQueriesContext(self.db) as queries,CaptureQueriesContext(connections["default"]) as other:
                    result=self.observe()
            self.assertTrue(result.technically_conformant)
            self.assertEqual(len(other),0)
            statements=[q["sql"].lstrip().upper() for q in queries]
            self.assertTrue(statements[0].startswith("BEGIN IMMEDIATE"))
            self.assertTrue(all(s.startswith(("BEGIN IMMEDIATE","SELECT","PRAGMA TABLE_INFO","PRAGMA FOREIGN_KEY_LIST","COMMIT")) for s in statements))
            self.assertEqual((self.rows(),self.schema()),before)


class AuditPre0007Tests(FileDatabase,TestCase):
    target=("ecomotor","0006_target_catalog_preparation")

    def test_real_0006_schema_diagnosed_without_querying_missing_field(self):
        self.sql("INSERT INTO ecomotor_targetcatalogversion (catalog_id,version) VALUES ('synthetic-old','r1')")
        with patch.object(audit,"validate_target_catalog_version",side_effect=AssertionError("reader called")):
            result=audit.audit_target_catalog(1,using=self.alias)
        codes=[c.issue_code for c in result.issues]
        self.assertIn("MIGRATION_0007_MISSING",codes)
        self.assertIn("SCHEMA_INCOMPLETE",codes)
        self.assertEqual(codes.count("TRIGGER_MISSING"),9)
        self.assertFalse(result.technically_conformant)


class CatalogAuditCommandTests(AuditDatabase,TestCase):
    def test_success_preparatory_frozen_and_no_output_inside_transaction(self):
        for frozen in (False,True):
            if frozen: freeze_target_catalog_version(self.version.pk,using=self.alias)
            output=StringIO()
            class CheckedOutput(StringIO):
                def write(inner,value):
                    self.assertFalse(self.db.in_atomic_block)
                    return output.write(value)
            self.command(stdout=CheckedOutput())
            text=output.getvalue()
            self.assertIn(NOTICE,text)
            self.assertIn("CONGELADA —" if frozen else "PREPARATORIA — no congelada",text)
            self.assertIn(self.version.catalog_id,text)
            self.assertEqual(text.count("OK: TRIGGER"),9)

    def test_failure_code_two_and_no_favorable_summary(self):
        self.drop_trigger(REFERENCE[0])
        output=StringIO()
        with self.assertRaises(CommandError) as caught:self.command(stdout=output)
        self.assertEqual(caught.exception.returncode,2)
        self.assertIn("TRIGGER_MISSING",output.getvalue())
        self.assertNotIn(NOTICE,output.getvalue())

    def test_command_operational_failure_code_three_and_no_success_output(self):
        for error in (OperationalError("synthetic SQL"),audit.TargetCatalogAuditTransactionError("synthetic")):
            output=StringIO()
            with patch(COMMAND_MODULE+".audit_target_catalog",side_effect=error),self.assertRaises(CommandError) as caught:
                self.command(stdout=output)
            self.assertEqual(caught.exception.returncode,3)
            self.assertEqual(output.getvalue(),"")
            self.assertNotIn("synthetic",str(caught.exception))

    def test_required_arguments_and_invalid_inputs(self):
        for args in ([],["--database",self.alias],["--catalog-version-id","1"],
                     ["--catalog-version-id","1.5","--database",self.alias],
                     ["--catalog-version-id","0","--database",self.alias],
                     ["--catalog-version-id","1","--database","unknown"]):
            with self.subTest(args=args),self.assertRaises(CommandError):
                call_command("audit_target_catalog",*args,stdout=StringIO())

    def test_run_from_argv_exit_codes_zero_two_three(self):
        Command=import_module(COMMAND_MODULE).Command
        argv=["manage.py","audit_target_catalog","--catalog-version-id",str(self.version.pk),"--database",self.alias]
        command=Command(stdout=StringIO(),stderr=StringIO())
        self.assertIsNone(command.run_from_argv(argv))  # Normal process completion: 0.
        self.drop_trigger(REFERENCE[0])
        command=Command(stdout=StringIO(),stderr=StringIO())
        with self.assertRaises(SystemExit) as caught:command.run_from_argv(argv)
        self.assertEqual(caught.exception.code,2)
        command=Command(stdout=StringIO(),stderr=StringIO())
        with patch(COMMAND_MODULE+".audit_target_catalog",side_effect=OperationalError("synthetic")):
            with self.assertRaises(SystemExit) as caught:command.run_from_argv(argv)
        self.assertEqual(caught.exception.code,3)

    def test_command_no_creation_or_changes(self):
        before=self.rows(),self.schema()
        with CaptureQueriesContext(self.db) as queries:self.command()
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT","UPDATE","DELETE","REPLACE","CREATE","DROP","ALTER")) for q in queries))
        self.assertEqual((self.rows(),self.schema()),before)


class CatalogAuditConcurrencyTests(AuditDatabase,TransactionTestCase):
    def overlap(self,first_operation,second_operation):
        locked,attempted=Event(),Event()
        def worker(first,operation):
            db=connections[self.alias];statements=[]
            def observe(execute,sql,params,many,context):
                statements.append(sql)
                if first and sql.upper().startswith("SELECT") and not locked.is_set():
                    locked.set()
                    if not attempted.wait(4):raise AssertionError("Second BEGIN missing")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"):attempted.set()
                return execute(sql,params,many,context)
            try:
                if not first and not locked.wait(4):raise AssertionError("First lock missing")
                with db.execute_wrapper(observe):result=operation()
                return result,get_ident(),id(db.connection),statements
            finally:db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(worker,True,first_operation);b=pool.submit(worker,False,second_operation)
            rows=[a.result(timeout=15),b.result(timeout=15)]
        self.assertNotEqual(rows[0][1],rows[1][1]);self.assertNotEqual(rows[0][2],rows[1][2])
        for _,_,_,sql in rows:
            self.assertLess(next(i for i,s in enumerate(sql) if s.upper().startswith("BEGIN IMMEDIATE")),next(i for i,s in enumerate(sql) if s.upper().startswith("SELECT")))
        return rows[0][0],rows[1][0]

    def compete(self,writer_first,change_protection=False):
        def writer():
            with transaction.atomic(using=self.alias):
                TargetCatalogVersion.objects.using(self.alias).get(pk=self.version.pk)
                if change_protection:self.drop_trigger(REFERENCE[0])
                else:
                    TargetCatalogVersion.objects.using(self.alias).filter(pk=self.version.pk).update(version="synthetic-after")
                    TargetEpoch.objects.using(self.alias).filter(catalog=self.version,ordinal=7).delete()
            return "changed"
        a,b=self.overlap(writer if writer_first else self.observe,self.observe if writer_first else writer)
        result=b if writer_first else a
        self.assertEqual(a if writer_first else b,"changed")
        self.assertEqual(result.technically_conformant,not writer_first)
        if writer_first:self.assertIn("TRIGGER_MISSING" if change_protection else "CATALOG_INVALID",self.codes(result))
        if not change_protection:self.assertEqual(result.version,"synthetic-after" if writer_first else self.version.version)
        self.assertFalse(self.observe().technically_conformant)

    def test_catalog_writer_before_audit(self):self.compete(True)
    def test_catalog_writer_after_audit(self):self.compete(False)
    def test_trigger_removal_before_audit(self):self.compete(True,True)
    def test_trigger_removal_after_audit(self):self.compete(False,True)

    def test_timeout_is_operational_then_new_transaction_can_audit(self):
        locked,release=Event(),Event()
        def hold():
            db=connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    locked.set()
                    if not release.wait(12):raise AssertionError("Release missing")
            finally:db.close()
        before=self.rows(),self.schema()
        with ThreadPoolExecutor(max_workers=1) as pool:
            holding=pool.submit(hold);self.assertTrue(locked.wait(4))
            try:
                start=monotonic()
                with self.assertRaises(OperationalError):self.observe()
                self.assertGreaterEqual(monotonic()-start,4.5)
                self.assertFalse(self.db.in_atomic_block);self.assertFalse(self.db.connection.in_transaction)
            finally:release.set()
            holding.result(timeout=4)
        self.assertEqual((self.rows(),self.schema()),before)
        self.assertTrue(self.observe().technically_conformant)
