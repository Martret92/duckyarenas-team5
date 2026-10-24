"""Disposable protected default: structural 0005 and a physical 0004 copy.

Only historical ORM bindings/serialization are adapted when generating old data.
No object Rewards coordinator, rule, snapshot V3 or lazy provisioning is added.
"""

import json
import os
from pathlib import Path
import sys
from tempfile import gettempdir
import unittest


def run(root, scenario):
    root = Path(root).absolute()
    owner = root.parent if root.name == "before" else root
    if (owner.parent.resolve() != Path(gettempdir()).resolve()
            or not owner.name.startswith("ducky-schema-0005-") or not root.is_dir()
            or owner.is_symlink() or getattr(owner, "is_junction", lambda: False)()):
        raise ValueError("An owned fresh TemporaryDirectory is required")
    if scenario not in ("before", "historical", "fresh"):
        raise ValueError("Unknown schema scenario")
    path = root / "instance" / "target_persistent_demo.sqlite3"
    if path.exists() != (scenario == "historical"):
        raise ValueError("Unexpected initial file state")
    if scenario != "historical" and (not path.parent.is_dir() or any(path.parent.iterdir())):
        raise ValueError("Only explicit migrate may create the fixture")
    allowed = {path.as_uri() + "?mode=" + mode for mode in ("rw", "rwc", "ro")}
    opened = []

    def audit(event, args):
        if event == "sqlite3.connect":
            if str(args[0]) not in allowed:
                raise AssertionError("SQLite connection outside the owned schema fixture")
            opened.append(str(args[0]))

    sys.addaudithook(audit)
    from copy import deepcopy
    from contextlib import ExitStack
    from dataclasses import asdict, replace
    from io import StringIO
    from itertools import product
    import re
    from unittest.mock import patch
    from uuid import uuid4
    from django.conf import settings
    from apps.ecomotor import target_persistent_demo_settings as official
    if settings.configured:
        raise AssertionError("Configure default before django.setup()")
    configuration = {k: v for k, v in vars(official).items() if k.isupper()}
    configuration["BASE_DIR"] = root
    configuration["DATABASES"] = deepcopy(official.DATABASES)
    configuration["DATABASES"]["default"]["NAME"] = path
    configuration["TARGET_PERSISTENT_DEMO_ALIAS"] = "default"
    settings.configure(**configuration)
    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from django.core.exceptions import ImproperlyConfigured
    from django.core.management import call_command
    from django.db import connections, transaction, IntegrityError
    from django.db.models.deletion import ProtectedError, PROTECT
    from django.db.migrations.executor import MigrationExecutor
    from django.test.utils import CaptureQueriesContext
    from django.utils.timezone import now
    from apps.bank.models import Wallet, Transaction
    from apps.duckies.models import Ducky, Item, ItemGrant, InventoryItem
    from apps.duckies.services import grant_item
    from apps.ecomotor.reward_types import RewardRuleSet, RewardRule, ProposedEffect
    from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES
    from . import models, services, playable_services as playable, reward_demo_services as rewards, reward_demo_rules as rules
    from .isolation import demo_connection, MIGRATING

    db = connections["default"]
    Reward = models.DemoTargetRewardEvent
    table = Reward._meta.db_table
    secret = "f" * 64
    latest = ("ecomotor_target_demo", "0005_rewards_duckies_schema")
    previous = ("ecomotor_target_demo", "0004_rewards_bank_schema")
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}

    def command(*args, **kwargs):
        result = call_command(*args, stdout=StringIO(), stderr=StringIO(), **kwargs)
        # Keep this historical app frontier; still install other apps normally.
        if args[:2] == ("migrate", "ecomotor_target_demo") and args[2] == "0005_rewards_duckies_schema":
            executor = MigrationExecutor(db)
            targets = [node for node in executor.loader.graph.leaf_nodes()
                       if node[0] != "ecomotor_target_demo"] + [("ecomotor_target_demo", "0005_rewards_duckies_schema")]
            if executor.migration_plan(targets):
                executor.migrate(targets)
                from django.core.management.sql import emit_post_migrate_signal
                emit_post_migrate_signal(0, False, "default",
                    apps=executor.loader.project_state(targets).apps, stdout=StringIO())
        return result

    def normalized(result):
        value = asdict(replace(result, replay=False))
        value.pop("changed", None)
        return json.loads(json.dumps(value, default=lambda x: x.isoformat(), sort_keys=True))

    def rows():
        result = {}
        with db.cursor() as cursor:
            for name in db.introspection.table_names(cursor):
                if not name.startswith("sqlite_"):
                    cursor.execute('SELECT * FROM "' + name + '" ORDER BY 1')
                    result[name] = {"columns": [c[0] for c in cursor.description],
                                    "rows": cursor.fetchall()}
        return json.loads(json.dumps(result, default=lambda x: x.isoformat()))

    def schema():
        with db.cursor() as cursor:
            cursor.execute("SELECT type,name,tbl_name,sql FROM sqlite_master "
                           "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
            return [list(row) for row in cursor.fetchall()]

    def constraints():
        with db.cursor() as cursor:
            return json.loads(json.dumps(db.introspection.get_constraints(cursor, table)))

    def assert_readonly(case, queries):
        case.assertFalse(any(q["sql"].lstrip().upper().startswith(
            ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")) for q in queries))

    def prepare_history():
        command("migrate", "ecomotor_target_demo", previous[1], interactive=False)
        executor = MigrationExecutor(db)
        targets = [node for node in executor.loader.graph.leaf_nodes()
                   if node[0] != "ecomotor_target_demo"] + [previous]
        executor.migrate(targets)
        old_apps = executor.loader.project_state(targets).apps
        from django.core.management.sql import emit_post_migrate_signal
        emit_post_migrate_signal(0, False, "default", apps=old_apps, stdout=StringIO())
        assert latest not in executor.loader.applied_migrations
        assert "item_grant_id" not in rows()[table]["columns"]
        command("seed_persistent_target_demo")
        old_reward = old_apps.get_model("ecomotor_target_demo", "DemoTargetRewardEvent")
        with ExitStack() as stack:
            # Only Reward gained a column. Its historical FK descriptors must
            # use the unchanged live classes for the real Bank/XP type checks.
            # These are test-local rendered fields, not production model edits.
            for name, model in (("progress", models.DemoTargetProgress),
                                ("xp_event", models.DemoTargetXPEvent),
                                ("bank_transaction", Transaction)):
                field = old_reward._meta.get_field(name)
                stack.enter_context(patch.object(field.remote_field, "model", model))
                stack.enter_context(patch.object(field, "related_model", model))
            stack.enter_context(patch.object(rewards, "Reward", old_reward))
            progress = services.create_demo_progress(session_token=secret)
            saved = {"progress": progress.pk, "calls": []}

            def remember(kind, args, result):
                saved["calls"].append({"kind": kind, "args": args, "result": normalized(result)})

            original_snapshot = rewards._snapshot
            def v1_snapshot(*args, **kwargs):
                return original_snapshot(*args, **{**kwargs, "schema": rewards.V1_SNAPSHOT_VERSION})
            with patch.object(rewards, "_snapshot", side_effect=v1_snapshot), patch.object(rules, "RULE_SET",
                    RewardRuleSet("demo-rewards-rules-v1", (RewardRule("demo-challenge-700-v1", "challenge",
                        {"completed": True}, (ProposedEffect("XP", 700),)),))):
                for activity in ("challenge", "visit"):
                    args = {"activity": activity, "fact_token": rewards.issue_reward_fact(
                        progress, activity=activity, session_token=secret)}
                    remember("reward", args, rewards.apply_demo_reward(progress, **args, session_token=secret))
            for activity in ("coin_challenge", "coin_challenge", "visit"):
                args = {"activity": activity, "fact_token": rewards.issue_reward_fact(
                    progress, activity=activity, session_token=secret)}
                remember("reward", args, rewards.apply_demo_reward(progress, **args, session_token=secret))
            args = {"amount": 100, "operation_token": services.issue_demo_operation(progress, session_token=secret)}
            remember("xp", args, services.grant_demo_target_xp(progress, **args, session_token=secret))
            for option, points in (("persist-demo-tech-gamer", 45), ("persist-demo-epoch-3", 10)):
                args = {"option_code": option, "increments": [(c, points if i == 0 else 0)
                    for i, c in enumerate(TARGET_STAT_CODES)], "operation_token": playable.issue_playable_operation(
                        progress, action="configure", session_token=secret)}
                if option.endswith("epoch-3"):
                    args["expected_revision"] = 1
                remember("configure", args, playable.configure_demo_option(progress, **args, session_token=secret))
            playable.switch_demo_option(progress, option_code="persist-demo-tech-gamer", expected_revision=2,
                operation_token=playable.issue_playable_operation(progress, action="switch", session_token=secret),
                session_token=secret)
            args = {"option_code": "persist-demo-tech-gamer", "expected_revision": 3,
                "configuration_revision": 1, "increments": [(c, 24 if i == 0 else 0)
                    for i, c in enumerate(TARGET_STAT_CODES)], "operation_token": playable.issue_playable_operation(
                        progress, action="redistribute", session_token=secret)}
            remember("redistribute", args, playable.redistribute_demo_option(progress, **args, session_token=secret))
            assert old_reward.objects.count() == 5
            assert models.DemoTargetEvolutionEvent.objects.count() == 6
            assert Wallet.objects.get().available_balance == 10
            assert {r.snapshot["schema"] for r in old_reward.objects.all()} == {
                "demo-reward-result-v1", "demo-reward-result-v2"}
        saved.update(rows=rows(), schema=schema(), constraints=constraints())
        assert "item_grant_id" not in saved["rows"][table]["columns"]
        assert [row[2] for row in saved["rows"]["django_migrations"]["rows"]
                if row[1] == "ecomotor_target_demo"] == ["0001_initial", "0002_playable_configurations",
                    "0003_synthetic_rewards", previous[1]]
        (root / "historical.json").write_text(json.dumps(saved), encoding="utf-8")
        evidence["observations"].append("Physical 0004: XP700/direct XP100, six evolutions, Gamer/Romano, V1 XP/visit and V2 coins/visit, Wallet10 and original tokens saved")

    class Schema0005Cases(unittest.TestCase):
        def repeat_migrate_and_check(self):
            before = rows()
            with CaptureQueriesContext(db) as queries:
                command("migrate", "ecomotor_target_demo", "0005_rewards_duckies_schema", interactive=False)
            assert_readonly(self, queries)
            self.assertEqual(rows(), before)
            executor = MigrationExecutor(db)
            self.assertEqual(executor.migration_plan([node for node in executor.loader.graph.leaf_nodes()
                if node[0] != "ecomotor_target_demo"] + [("ecomotor_target_demo", "0005_rewards_duckies_schema")]), [])
            self.assertIn(latest, executor.loader.applied_migrations)
            migration = executor.loader.disk_migrations[latest]
            self.assertEqual(migration.dependencies, [previous,
                ("duckies", "0002_rename_selected_historical_item_ducky_selected_outfit_and_more")])
            self.assertEqual([type(op).__name__ for op in migration.operations],
                             ["RemoveConstraint", "AddField", "AddConstraint"])
            command("check", databases=["default"])
            self.assertNotIn(("ecomotor_target_demo", "0006_rewards_combined_schema"),
                             executor.loader.applied_migrations)
            command("makemigrations", check=True, dry_run=True)
            self.assertEqual(rows(), before)
            self.assertFalse(db.in_atomic_block or db.connection.in_transaction)

        def test_fresh_installation_and_repeat(self):
            command("migrate", "ecomotor_target_demo", "0005_rewards_duckies_schema", interactive=False)
            for model in (get_user_model(), Wallet, Transaction, Ducky, Item, ItemGrant,
                          InventoryItem, models.DemoTargetProgress, Reward):
                self.assertEqual(model.objects.count(), 0, model.__name__)
            field = Reward._meta.get_field("item_grant")
            self.assertTrue(field.one_to_one and field.null and field.blank)
            self.assertIs(field.remote_field.on_delete, PROTECT)
            self.assertIs(field.remote_field.model, ItemGrant)
            self.assertFalse(field.has_default())
            found = constraints()
            self.assertTrue(any(c["unique"] and c["columns"] == ["item_grant_id"] for c in found.values()))
            self.assertTrue(any(c["foreign_key"] == [ItemGrant._meta.db_table, "id"]
                and c["columns"] == ["item_grant_id"] for c in found.values()))
            self.assertTrue(found["demo_reward_outcome_valid"]["check"])
            self.repeat_migrate_and_check()
            evidence["observations"].append("Fresh 0005/default: nullable OneToOne/PROTECT, FK/unique/CHECK and no automatic provisioning; repeat migrate read-only; check and autodetector clean")

        def causes(self):
            command("seed_persistent_target_demo")
            progress = services.create_demo_progress(session_token=secret)
            user = get_user_model()(username="schema-only-" + uuid4().hex, is_active=False)
            user.set_unusable_password()
            user.save()
            progress.synthetic_user = user
            progress.save(update_fields=["synthetic_user"])
            wallet = Wallet.objects.create(user=user, available_balance=5)
            bank = Transaction.objects.create(wallet=wallet, transaction_type="REWARD", amount=5,
                balance_after=5, operation_key=uuid4().hex, source_platform="schema-only",
                issuing_entity="schema-only", request_fingerprint="a" * 64)
            ducky = Ducky.objects.create(user=user, sex=Ducky.SEX[0][0], selected_outfit=None)
            item = Item.objects.create(code="schema-hint-" + uuid4().hex, name="Fixture HINT",
                                       category=Item.HINT, consumable=True, is_active=True)
            grant = grant_item(user, item, 1, "schema-only-" + uuid4().hex,
                               item_level=None, reference_type="schema-only", reference_id="fixture")
            xp = services.grant_demo_target_xp(progress, amount=100,
                operation_token=services.issue_demo_operation(progress, session_token=secret), session_token=secret)
            return progress, xp.event_id, bank, grant

        def reward(self, progress, **changes):
            values = dict(progress=progress, origin_code="schema-only", fact_id=uuid4().hex,
                recipient_id=f"demo-progress:{progress.pk}", activity_type="schema-only", occurred_at=now(),
                fingerprint_version="schema-only", fingerprint="a" * 64, rule_set_version="schema-only",
                status="NO_REWARD", reason_codes=[], xp_amount=0, snapshot={"fixture": "structural-only"})
            values.update(changes)
            return Reward.objects.create(**values)

        def test_four_valid_outcomes_and_item_relations(self):
            progress, xp, bank, grant = self.causes()
            self.assertIsNone(self.reward(progress).item_grant_id)
            self.assertIsNone(self.reward(progress, status="APPLIED", xp_amount=100, xp_event_id=xp).item_grant_id)
            self.assertIsNone(self.reward(progress, status="APPLIED", coin_amount=5, bank_transaction=bank).item_grant_id)
            item_reward = self.reward(progress, status="APPLIED", item_grant=grant)
            self.assertEqual(item_reward.item_grant_id, grant.pk)
            with self.assertRaisesRegex(IntegrityError, "UNIQUE.*item_grant"), transaction.atomic():
                self.reward(progress, status="APPLIED", item_grant=grant)
            with self.assertRaises(ProtectedError):
                grant.delete()
            unlinked = self.reward(progress)
            with self.assertRaisesRegex(IntegrityError, "FOREIGN KEY"), transaction.atomic():
                Reward.objects.filter(pk=unlinked.pk).update(status="APPLIED", item_grant_id=2**63-1)
            self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
            self.assertTrue(db.get_autocommit())
            self.assertIsNone(Reward.objects.get(pk=unlinked.pk).item_grant_id)
            evidence["observations"].append("Four structural outcomes persisted; ItemGrant unique, invalid FK rejected at commit, PROTECT and connection recovery verified")

        def test_exhaustive_outcome_check_via_updates(self):
            progress, xp, bank, grant = self.causes()
            row = self.reward(progress)
            accepted = 0
            for status, xp_positive, coin_positive, xp_cause, bank_cause, item_cause in product(
                    ("APPLIED", "NO_REWARD"), (False, True), (False, True), (False, True), (False, True), (False, True)):
                state = (status, xp_positive, coin_positive, xp_cause, bank_cause, item_cause)
                valid = state in (("APPLIED", True, False, True, False, False),
                    ("APPLIED", False, True, False, True, False),
                    ("APPLIED", False, False, False, False, True),
                    ("NO_REWARD", False, False, False, False, False))
                changes = dict(status=status, xp_amount=100 if xp_positive else 0,
                    coin_amount=5 if coin_positive else 0, xp_event_id=xp if xp_cause else None,
                    bank_transaction_id=bank.pk if bank_cause else None,
                    item_grant_id=grant.pk if item_cause else None)
                with self.subTest(state=state):
                    # Only this row uses these causes; UNIQUE/FK cannot mask CHECK.
                    if valid:
                        with transaction.atomic():
                            self.assertEqual(Reward.objects.filter(pk=row.pk).update(**changes), 1)
                        accepted += 1
                    else:
                        with self.assertRaisesRegex(IntegrityError, "demo_reward_outcome_valid"), transaction.atomic():
                            Reward.objects.filter(pk=row.pk).update(**changes)
                    self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                    self.assertTrue(db.get_autocommit())
            self.assertEqual(accepted, 4)
            evidence["observations"].append({"update_combinations": 64, "accepted": 4,
                                              "rejected_by_named_check": 60})

        def test_previous_identity_format_ranges_and_uniqueness(self):
            progress, xp, bank, grant = self.causes()
            row = self.reward(progress)
            for changes, name in (
                ({"fact_id": ""}, "demo_reward_hash_format"),
                ({"fact_id": "G" * 32}, "demo_reward_hash_format"),
                ({"fingerprint": "a" * 63}, "demo_reward_hash_format"),
                ({"origin_code": ""}, "demo_reward_text_present"),
                ({"recipient_id": ""}, "demo_reward_text_present"),
                ({"activity_type": ""}, "demo_reward_text_present"),
                ({"fingerprint_version": ""}, "demo_reward_text_present"),
                ({"rule_set_version": ""}, "demo_reward_text_present"),
                ({"matched_rule_id": ""}, "demo_reward_text_present"),
                ({"status": "UNKNOWN"}, "demo_reward_outcome_valid")):
                with self.subTest(changes=changes), self.assertRaisesRegex(IntegrityError, name), transaction.atomic():
                    Reward.objects.filter(pk=row.pk).update(**changes)
            with self.assertRaises(IntegrityError), transaction.atomic():
                self.reward(progress, fact_id=row.fact_id)
            for changes in ({"status": "APPLIED", "xp_amount": -1, "xp_event_id": xp},
                            {"status": "APPLIED", "coin_amount": -1, "bank_transaction": bank}):
                with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                    Reward.objects.filter(pk=row.pk).update(**changes)
            for field, cause in (("xp_amount", {"xp_event_id": xp}),
                                 ("coin_amount", {"bank_transaction": bank})):
                with self.subTest(field=field):
                    with self.assertRaises((OverflowError, IntegrityError)), transaction.atomic():
                        Reward.objects.filter(pk=row.pk).update(status="APPLIED", **{field: 2**63}, **cause)
                    Reward.objects.filter(pk=row.pk).update(status="APPLIED", **{field: 2**63-1}, **cause)
                    self.assertEqual(getattr(Reward.objects.get(pk=row.pk), field), 2**63-1)
                    Reward.objects.filter(pk=row.pk).update(status="NO_REWARD", xp_amount=0, coin_amount=0,
                        xp_event=None, bank_transaction=None, item_grant=None)
            for changes in ({"status": "APPLIED", "xp_amount": 100, "xp_event_id": xp},
                            {"status": "APPLIED", "coin_amount": 5, "bank_transaction": bank}):
                self.reward(progress, **changes)
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.reward(progress, **changes)
            self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
            evidence["observations"].append("Previous identity/text/hash/range, XP/Bank cause uniqueness and SQLite integer limits preserved")

        def test_physical_historical_copy(self):
            old = json.loads((root / "historical.json").read_text(encoding="utf-8"))
            self.assertEqual(rows(), old["rows"])
            self.assertNotIn("item_grant_id", old["rows"][table]["columns"])
            before_executor = MigrationExecutor(db)
            self.assertIn(previous, before_executor.loader.applied_migrations)
            self.assertNotIn(latest, before_executor.loader.applied_migrations)
            command("migrate", "ecomotor_target_demo", "0005_rewards_duckies_schema", interactive=False)
            after = rows()
            self.assertEqual(set(after), set(old["rows"]))
            for name, prior in old["rows"].items():
                columns = after[name]["columns"]
                indexes = [columns.index(c) for c in prior["columns"]]
                common = [[row[i] for i in indexes] for row in after[name]["rows"]]
                if name == "django_migrations":
                    additions = [row for row in common if row[1:3] == list(latest)]
                    self.assertEqual(len(additions), 1)
                    common = [row for row in common if row[1:3] != list(latest)]
                self.assertEqual(common, prior["rows"], name)
            self.assertEqual([r for r in schema() if r[2] != table],
                             [r for r in old["schema"] if r[2] != table])
            prior_indexes = [r for r in old["schema"] if r[0] == "index" and r[2] == table]
            for entry in prior_indexes:
                self.assertIn(entry, schema())
            found = constraints()
            old_table_sql = next(r[3] for r in old["schema"] if r[:3] == ["table", table, table])
            for name in re.findall(r'CONSTRAINT "([^"]+)"', old_table_sql):
                self.assertIn(name, found)
            current_table_sql = next(r[3] for r in schema() if r[:3] == ["table", table, table])
            check_pattern = r'CONSTRAINT "([^"]+)" CHECK (\(.+?\))(?=, CONSTRAINT|\)$)'
            old_checks = dict(re.findall(check_pattern, old_table_sql, re.S))
            new_checks = dict(re.findall(check_pattern, current_table_sql, re.S))
            self.assertIn("demo_reward_outcome_valid", old_checks)
            self.assertEqual(set(old_checks), set(new_checks))
            for name, expression in old_checks.items():
                if name != "demo_reward_outcome_valid":
                    self.assertEqual(new_checks[name], expression, name)
            # Autoindex names can shift on SQLite table reconstruction. Compare
            # their semantic columns/unique/foreign-key attributes, not numbers.
            for prior in old["constraints"].values():
                if prior["check"]:
                    continue
                self.assertTrue(any(all(value.get(k) == prior.get(k) for k in
                    ("columns", "unique", "primary_key", "foreign_key", "index", "orders", "type"))
                    for value in found.values()), prior)
            self.assertEqual(set(Reward.objects.values_list("item_grant_id", flat=True)), {None})
            with db.cursor() as cursor:
                cursor.execute("PRAGMA foreign_key_check")
                self.assertEqual(cursor.fetchall(), [])
            progress = models.DemoTargetProgress.objects.get(pk=old["progress"])
            functions = {"reward": rewards.apply_demo_reward, "xp": services.grant_demo_target_xp,
                "configure": playable.configure_demo_option, "redistribute": playable.redistribute_demo_option}
            before_replay = rows()
            with CaptureQueriesContext(db) as queries:
                for call in old["calls"]:
                    result = functions[call["kind"]](progress, **call["args"], session_token=secret)
                    self.assertTrue(result.replay)
                    self.assertEqual(normalized(result), call["result"])
                self.assertEqual(len(rewards.read_demo_rewards(progress, session_token=secret)), 5)
                overview = rewards.read_demo_bank(progress, session_token=secret)
                self.assertEqual(overview.balance, 10)
            assert_readonly(self, queries)
            self.assertEqual(rows(), before_replay)
            self.assertEqual(Ducky.objects.count(), 0)
            self.assertEqual(Item.objects.count(), 0)
            self.assertEqual(ItemGrant.objects.count(), 0)
            db.close()
            self.assertEqual(rows(), before_replay)
            self.repeat_migrate_and_check()
            evidence["observations"].append({"physical_0004_copy": True,
                "historical_calls_replayed": len(old["calls"]), "raw_v1_v2_json_unchanged": True,
                "all_common_columns_identical": True, "unrelated_schema_and_catalog_triggers_identical": True,
                "old_indexes_fk_constraints_preserved": True, "wallet_balance": 10,
                "no_object_provisioning": True, "replay_readonly": True, "reopen_preserved": True})

    try:
        if scenario != "historical":
            try:
                demo_connection()
            except ImproperlyConfigured:
                pass
            else:
                raise AssertionError("Ordinary open accepted an absent file")
            assert not path.exists()
        if scenario == "before":
            prepare_history()
            evidence.update(success=True, tests=1, failures=0, errors=0, skipped=0)
        else:
            names = ("test_physical_historical_copy",) if scenario == "historical" else (
                "test_fresh_installation_and_repeat", "test_four_valid_outcomes_and_item_relations",
                "test_exhaustive_outcome_check_via_updates", "test_previous_identity_format_ranges_and_uniqueness")
            result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(Schema0005Cases(name) for name in names))
            evidence.update(success=result.wasSuccessful(), tests=result.testsRun,
                failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    finally:
        connections.close_all()
    evidence.update(connections_closed=all(c.connection is None for c in connections.all()),
                    only_fixture_connections=bool(opened) and all(p in allowed for p in opened),
                    migration_scope_closed=not MIGRATING.get())
    print("SCHEMA_0005_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
    return 0 if evidence["success"] else 1


if __name__ == "__main__":
    raise SystemExit(run(*sys.argv[1:]))
