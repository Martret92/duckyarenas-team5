"""Synthetic-only previews, read-only commands and real file-backed concurrency."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from decimal import Decimal
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

from . import target_catalog_freeze, target_xp_preview as preview
from .models import EvolutionEvent, EvolutionStage, TargetCatalogVersion, TargetEpoch, TargetLevelThreshold, XPEvent
from .target_xp_plan import plan_target_xp_grant
from .test_target_catalog_freeze import FileDatabase
from .test_target_catalog_persistence import synthetic_catalog
from .test_xp_service import create_xp_catalogs, create_xp_profile

WARNING = "SIMULACIÓN INTERNA — No se ha concedido XP real. El catálogo no queda autorizado ni activado por esta operación."
COMMAND = "apps.ecomotor.management.commands.preview_target_xp"


class PreviewDatabase(FileDatabase):
    def setUp(self):
        super().setUp()
        # The historical 0007 target alone only requires auth.0001. Fixtures
        # using today's User model need the complete current graph in this file.
        executor = MigrationExecutor(self.db)
        executor.migrate(executor.loader.graph.leaf_nodes())
        self.version = synthetic_catalog(using=self.alias, levels=9)

    def simulate(self, before=0, amount=91, pk=None):
        return preview.preview_target_xp(self.version.pk if pk is None else pk,
                                         using=self.alias, xp_before=before, amount=amount)

    def command(self, before="0", amount="91", **kwargs):
        output = StringIO()
        call_command("preview_target_xp", "--catalog-version-id", str(self.version.pk),
                     "--database", self.alias, "--xp-before", before, "--amount", amount,
                     stdout=output, **kwargs)
        return output.getvalue()


class PreviewServiceTests(PreviewDatabase, TestCase):
    def test_persisted_catalog_exact_level_eight_and_all_crossings(self):
        result = self.simulate()
        p = result.plan.progression
        self.assertEqual(result.catalog_version_id, self.version.pk)
        self.assertEqual(result.plan.amount, 91)
        self.assertEqual((p.xp_before,p.xp_after),(0,91))
        self.assertEqual((p.level_before,p.level_after),(1,8))
        self.assertEqual((p.epoch_before_code,p.epoch_after_code),("synthetic-epoch-1","synthetic-epoch-7"))
        self.assertEqual(p.crossed_levels,tuple(range(2,9)))
        self.assertEqual(p.crossed_epoch_codes,tuple(f"synthetic-epoch-{n}" for n in range(2,8)))
        self.assertEqual((p.choice_unlocked_before,p.choice_unlocked_after,p.choice_newly_unlocked),(False,True,True))
        self.assertEqual(p.catalog_version,"synthetic-r1")

    def test_exact_thresholds_and_no_crossing(self):
        for before,amount,level in ((0,1,1),(12,1,2),(13,1,2),(90,1,8)):
            with self.subTest(before=before,amount=amount):
                p = self.simulate(before,amount).plan.progression
                self.assertEqual(p.level_after,level)
                if before in (0,13):
                    self.assertEqual(p.crossed_levels,())
                    self.assertEqual(p.crossed_epoch_codes,())

    def test_already_unlocked_level_nine_and_large_xp_without_extra_epoch(self):
        for before,amount in ((91,13),(104,10**50)):
            with self.subTest(before=before):
                p = self.simulate(before,amount).plan.progression
                self.assertEqual(p.level_after,9)
                self.assertEqual(p.epoch_after_code,"synthetic-epoch-7")
                self.assertEqual(p.crossed_epoch_codes,())
                self.assertTrue(p.choice_unlocked_before and p.choice_unlocked_after)
                self.assertFalse(p.choice_newly_unlocked)
                self.assertEqual(p.xp_after,before+amount)

    def test_same_textual_version_in_different_catalogs_retains_technical_pk(self):
        other = synthetic_catalog(using=self.alias, catalog_id="synthetic-another",levels=9)
        first,second = self.simulate(),self.simulate(pk=other.pk)
        self.assertEqual(first.plan,second.plan)
        self.assertNotEqual(first.catalog_version_id,second.catalog_version_id)

    def test_result_and_nested_plan_are_immutable_deterministic_and_tuples(self):
        result = self.simulate()
        self.assertEqual(result,self.simulate())
        for obj,field in ((result,"catalog_version_id"),(result.plan,"amount"),(result.plan.progression,"xp_after")):
            with self.assertRaises(FrozenInstanceError): setattr(obj,field,0)
            self.assertFalse(hasattr(obj,"__dict__"))
        self.assertIs(type(result.plan.progression.crossed_levels),tuple)
        self.assertIs(type(result.plan.progression.crossed_epoch_codes),tuple)
        with self.assertRaises(preview.InvalidTargetCatalogError): preview.TargetXPPreview(True,result.plan)
        with self.assertRaises(TypeError): preview.TargetXPPreview(result.catalog_version_id,{"amount":91})

    def test_invalid_pk_alias_and_missing_row(self):
        for pk in (None,True,0,-1,1.0,"1",{},2**63):
            with self.subTest(pk=pk), self.assertRaises(preview.InvalidTargetCatalogError):
                preview.preview_target_xp(pk,using=self.alias,xp_before=0,amount=1)
        for alias in (None,True,"","missing",{},1):
            with self.subTest(alias=alias), self.assertRaises(preview.InvalidTargetCatalogError):
                preview.preview_target_xp(self.version.pk,using=alias,xp_before=0,amount=1)
        with self.assertRaises(TargetCatalogVersion.DoesNotExist): self.simulate(pk=999999)

    def test_invalid_xp_and_amount_rejected_before_queries(self):
        for value in (-1,True,False,1.0,Decimal("1"),"1",None,[]):
            with self.subTest(xp=value), CaptureQueriesContext(self.db) as queries:
                with self.assertRaises(preview.InvalidTargetXPError): self.simulate(before=value)
                self.assertEqual(len(queries),0)
        for value in (0,-1,True,False,1.0,Decimal("1"),"1",None,[]):
            with self.subTest(amount=value), CaptureQueriesContext(self.db) as queries:
                with self.assertRaises(preview.InvalidTargetXPAmountError): self.simulate(amount=value)
                self.assertEqual(len(queries),0)

    def test_incomplete_or_incoherent_catalog_rejected_without_repair(self):
        TargetEpoch.objects.using(self.alias).filter(catalog=self.version,ordinal=7).delete()
        before = self.rows()
        with self.assertRaises(preview.InvalidTargetCatalogError): self.simulate()
        self.assertEqual(self.rows(),before)
        other = synthetic_catalog(using=self.alias,version="synthetic-incoherent")
        TargetLevelThreshold.objects.using(self.alias).filter(catalog=other,level=2).update(minimum_xp=14)
        with self.assertRaises(preview.InvalidTargetCatalogError): self.simulate(pk=other.pk)

    def test_outer_atomic_manual_autocommit_and_incompatible_connections_rejected(self):
        with transaction.atomic(using=self.alias), CaptureQueriesContext(self.db) as queries:
            with self.assertRaises(preview.TargetXPPreviewTransactionError): self.simulate()
            self.assertEqual(len(queries),0)
        self.db.set_autocommit(False)
        try:
            with self.assertRaises(preview.TargetXPPreviewTransactionError): self.simulate()
        finally:
            self.db.rollback()
            self.db.set_autocommit(True)
        for options in ({"transaction_mode":"DEFERRED","timeout":5},{"transaction_mode":"IMMEDIATE","timeout":1}):
            with patch.dict(self.db.settings_dict,OPTIONS=options):
                with self.assertRaises(preview.TargetXPPreviewTransactionError): self.simulate()
        for name,value in (("transaction_mode","DEFERRED"),("vendor","postgresql")):
            with patch.object(self.db,name,value):
                with self.assertRaises(preview.TargetXPPreviewTransactionError): self.simulate()

    def test_sql_errors_propagate_and_transaction_is_clean(self):
        error = OperationalError("synthetic SQL failure")
        def fail(execute,sql,params,many,context):
            if sql.upper().startswith("SELECT"): raise error
            return execute(sql,params,many,context)
        before = self.rows()
        with self.db.execute_wrapper(fail), self.assertRaises(OperationalError) as caught:
            self.simulate()
        self.assertIs(caught.exception,error)
        self.assertFalse(self.db.in_atomic_block)
        self.assertFalse(self.db.connection.in_transaction)
        self.assertEqual(self.rows(),before)
        self.simulate()

    def test_uses_public_a11_reader_and_a21_planner_within_transaction(self):
        reader = preview.validate_target_catalog_version
        def observed_reader(pk,*,using):
            self.assertTrue(connections[using].in_atomic_block)
            return reader(pk,using=using)
        def observed_plan(before,amount,snapshot):
            self.assertTrue(self.db.in_atomic_block)
            self.assertEqual(snapshot.catalog_version,"synthetic-r1")
            return plan_target_xp_grant(before,amount,snapshot)
        with patch.object(preview,"validate_target_catalog_version",side_effect=observed_reader) as a11:
            with patch.object(preview,"plan_target_xp_grant",side_effect=observed_plan) as a21:
                result = self.simulate()
        a11.assert_called_once_with(self.version.pk,using=self.alias)
        a21.assert_called_once()
        self.assertEqual(result.plan.amount,91)

    def test_preparatory_and_frozen_catalogs_no_writes_or_calls_to_business_services(self):
        create_xp_catalogs(self.alias)
        profile = create_xp_profile(self.alias,username="synthetic-preview-user")
        event = XPEvent.objects.using(self.alias).create(profile=profile,operation_key="synthetic-preview-existing",amount=1,xp_before=0,xp_after=1)
        stage = EvolutionStage.objects.using(self.alias).order_by("pk").first()
        EvolutionEvent.objects.using(self.alias).create(profile=profile,xp_event=event,stage=stage)
        for frozen in (False,True):
            if frozen: target_catalog_freeze.freeze_target_catalog_version(self.version.pk,using=self.alias)
            before = self.rows()
            with patch("apps.ecomotor.xp_service.grant_historical_xp",side_effect=AssertionError("S3 called")), patch.object(target_catalog_freeze,"freeze_target_catalog_version",side_effect=AssertionError("freeze called")):
                with CaptureQueriesContext(self.db) as queries, CaptureQueriesContext(connections["default"]) as default_queries:
                    result = self.simulate()
            self.assertEqual(len(default_queries),0)
            sql = [q["sql"].upper() for q in queries]
            self.assertTrue(sql[0].startswith("BEGIN IMMEDIATE"))
            self.assertEqual(sum(s.startswith("SELECT") for s in sql),3)
            self.assertFalse(any(s.startswith(("INSERT","UPDATE","DELETE","REPLACE")) for s in sql))
            self.assertEqual(self.rows(),before)
            self.assertEqual(result.plan.amount,91)
            self.version.refresh_from_db(using=self.alias)
            self.assertEqual(self.version.frozen_at is not None,frozen)


class PreviewCommandTests(PreviewDatabase, TestCase):
    def test_output_has_all_fields_and_exact_warning(self):
        output = self.command()
        self.assertIn(WARNING,output)
        for text in (f"Catálogo PK: {self.version.pk}","Versión: synthetic-r1","XP: 0 → 91",
                     "Nivel: 1 → 8","Época: synthetic-epoch-1 → synthetic-epoch-7",
                     "Niveles cruzados: 2, 3, 4, 5, 6, 7, 8","synthetic-epoch-7",
                     "Elección desbloqueada antes: False","Elección desbloqueada después: True",
                     "Elección recién desbloqueada: True"):
            self.assertIn(text,output)

    def test_no_crossings_command_output_and_no_console_inside_transaction(self):
        output = StringIO()
        class ObservedOutput(StringIO):
            def write(inner,text):
                self.assertFalse(self.db.in_atomic_block)
                return output.write(text)
        call_command("preview_target_xp","--catalog-version-id",str(self.version.pk),"--database",self.alias,
                     "--xp-before","0","--amount","1",stdout=ObservedOutput())
        self.assertIn("Niveles cruzados: (ninguno)",output.getvalue())
        self.assertIn("Épocas cruzadas: (ninguna)",output.getvalue())

    def test_four_arguments_are_required_and_invalid_cli_integers_are_command_errors(self):
        args=["--catalog-version-id",str(self.version.pk),"--database",self.alias,"--xp-before","0","--amount","1"]
        for index in range(0,len(args),2):
            with self.subTest(missing=args[index]), self.assertRaises(CommandError):
                call_command("preview_target_xp",*(args[:index]+args[index+2:]),stdout=StringIO())
        for index in (1,5,7):
            invalid=args.copy();invalid[index]="1.5"
            with self.subTest(index=index), self.assertRaises(CommandError):
                call_command("preview_target_xp",*invalid,stdout=StringIO())

    def test_domain_and_database_errors_are_controlled_without_success_output(self):
        errors=(preview.InvalidTargetCatalogError("synthetic"),preview.InvalidTargetXPError("synthetic"),
                preview.InvalidTargetXPAmountError("synthetic"),TargetCatalogVersion.DoesNotExist(),
                preview.TargetXPPreviewTransactionError("synthetic"),OperationalError("synthetic SQL"))
        for error in errors:
            output=StringIO()
            with self.subTest(error=type(error)), patch(COMMAND+".preview_target_xp",side_effect=error):
                with self.assertRaises(CommandError) as caught:
                    call_command("preview_target_xp","--catalog-version-id",str(self.version.pk),"--database",self.alias,
                                 "--xp-before","0","--amount","1",stdout=output)
            self.assertEqual(output.getvalue(),"")
            self.assertNotIn("synthetic SQL",str(caught.exception))
            self.assertEqual(caught.exception.returncode,3 if isinstance(error,OperationalError) else 2)

    def test_real_invalid_cli_inputs_rejected(self):
        for name,value in (("--database","missing"),("--catalog-version-id","999999"),
                           ("--catalog-version-id","0"),("--xp-before","-1"),("--amount","0")):
            args=["--catalog-version-id",str(self.version.pk),"--database",self.alias,"--xp-before","0","--amount","1"]
            args[args.index(name)+1]=value
            with self.subTest(name=name), self.assertRaises(CommandError):
                call_command("preview_target_xp",*args,stdout=StringIO())

    def test_command_no_writes_no_seed_and_only_expected_service_called(self):
        before=self.rows()
        with patch(COMMAND+".preview_target_xp",wraps=preview.preview_target_xp) as service:
            with CaptureQueriesContext(self.db) as queries:
                self.command()
        service.assert_called_once_with(self.version.pk,using=self.alias,xp_before=0,amount=91)
        self.assertFalse(any(q["sql"].upper().startswith(("INSERT","UPDATE","DELETE","REPLACE")) for q in queries))
        self.assertEqual(self.rows(),before)


class PreviewConcurrencyTests(PreviewDatabase, TransactionTestCase):
    def overlap(self,first_operation,second_operation):
        locked,attempted=Event(),Event()
        def worker(first,operation):
            db=connections[self.alias]
            statements=[]
            def observe(execute,sql,params,many,context):
                statements.append(sql)
                if first and sql.upper().startswith("SELECT") and not locked.is_set():
                    locked.set()
                    if not attempted.wait(4): raise AssertionError("Writer did not attempt BEGIN")
                if not first and sql.upper().startswith("BEGIN IMMEDIATE"): attempted.set()
                return execute(sql,params,many,context)
            try:
                if not first and not locked.wait(4): raise AssertionError("First transaction not locked")
                with db.execute_wrapper(observe): result=operation()
                return result,get_ident(),id(db.connection),statements
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(worker,True,first_operation)
            second=pool.submit(worker,False,second_operation)
            rows=[first.result(timeout=15),second.result(timeout=15)]
        self.assertNotEqual(rows[0][1],rows[1][1])
        self.assertNotEqual(rows[0][2],rows[1][2])
        for _,_,_,sql in rows:
            self.assertLess(next(i for i,s in enumerate(sql) if s.upper().startswith("BEGIN IMMEDIATE")),next(i for i,s in enumerate(sql) if s.upper().startswith("SELECT")))
        return rows[0][0],rows[1][0]

    def compete(self,kind,writer_first):
        def writer():
            with transaction.atomic(using=self.alias):
                TargetCatalogVersion.objects.using(self.alias).get(pk=self.version.pk)
                if kind=="level":
                    TargetLevelThreshold.objects.using(self.alias).filter(catalog=self.version,level=8).update(minimum_xp=95)
                elif kind=="epoch":
                    TargetEpoch.objects.using(self.alias).filter(catalog=self.version,ordinal=7).update(code="synthetic-epoch-new")
                else:
                    TargetLevelThreshold.objects.using(self.alias).filter(catalog=self.version,level=2).update(minimum_xp=14)
                    TargetEpoch.objects.using(self.alias).filter(catalog=self.version,ordinal=2).update(minimum_xp=14)
            return "changed"
        amount=13 if kind=="pair" else 91
        reader=lambda:self.simulate(amount=amount)
        a,b=self.overlap(writer if writer_first else reader,reader if writer_first else writer)
        result=b if writer_first else a
        self.assertEqual(a if writer_first else b,"changed")
        p=result.plan.progression
        if kind=="level":
            self.assertEqual(p.level_after,7 if writer_first else 8)
            self.assertEqual(p.choice_newly_unlocked,not writer_first)
        elif kind=="epoch":
            self.assertEqual(p.epoch_after_code,"synthetic-epoch-new" if writer_first else "synthetic-epoch-7")
        else:
            self.assertEqual((p.level_after,p.epoch_after_code),
                             (1,"synthetic-epoch-1") if writer_first else (2,"synthetic-epoch-2"))
        self.version.refresh_from_db(using=self.alias)
        self.assertIsNone(self.version.frozen_at)
        # A later observation sees the committed change, without changing the
        # earlier immutable result into a mixture of old and new thresholds.
        current=self.simulate(amount=amount).plan.progression
        if kind=="pair": self.assertEqual((current.level_after,current.epoch_after_code),(1,"synthetic-epoch-1"))
        if kind=="level": self.assertEqual(current.level_after,7)
        if kind=="epoch": self.assertEqual(current.epoch_after_code,"synthetic-epoch-new")

    def test_level_writer_before_snapshot(self): self.compete("level",True)
    def test_level_writer_after_snapshot(self): self.compete("level",False)
    def test_epoch_writer_before_snapshot(self): self.compete("epoch",True)
    def test_epoch_writer_after_snapshot(self): self.compete("epoch",False)
    def test_atomic_threshold_pair_before_snapshot_never_mixed(self): self.compete("pair",True)
    def test_atomic_threshold_pair_after_snapshot_never_mixed(self): self.compete("pair",False)

    def test_real_timeout_propagates_no_partial_result_and_next_preview_succeeds(self):
        locked,release=Event(),Event()
        def hold():
            db=connections[self.alias]
            try:
                with transaction.atomic(using=self.alias):
                    locked.set()
                    if not release.wait(12): raise AssertionError("Release missing")
            finally: db.close()
        before=self.rows()
        with ThreadPoolExecutor(max_workers=1) as pool:
            holder=pool.submit(hold)
            self.assertTrue(locked.wait(4))
            try:
                start=monotonic()
                with self.assertRaises(OperationalError): self.simulate()
                self.assertGreaterEqual(monotonic()-start,4.5)
                self.assertFalse(self.db.in_atomic_block)
                self.assertFalse(self.db.connection.in_transaction)
            finally: release.set()
            holder.result(timeout=4)
        self.assertEqual(self.rows(),before)
        self.simulate()
