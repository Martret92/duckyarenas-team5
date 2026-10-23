"""Test-only protected default processes for real 0003 -> 0004 compatibility.

The before process uses Django's rendered historical ORM models, binding only
model references in the unchanged V1 services. All business logic and SQL are
real. The parent closes that process and copies its physical SQLite before the
after process opens it with today's models. No personal database is opened.
"""

import json
import os
from pathlib import Path
import sys
from tempfile import gettempdir


def run(root, scenario):
    root = Path(root).absolute()
    owner = root.parent if root.name == "before" else root
    if (owner.parent.resolve() != Path(gettempdir()).resolve()
            or not owner.name.startswith("ducky-bank-default-") or not root.is_dir()):
        raise ValueError("An owned disposable test directory is required")
    path = root / "instance" / "target_persistent_demo.sqlite3"
    if scenario not in ("fresh", "before", "historical"):
        raise ValueError("Unknown schema test scenario")
    if path.exists() != (scenario == "historical"):
        raise ValueError("Unexpected fixture state")
    allowed = {path.as_uri() + "?mode=" + mode for mode in ("rw", "rwc", "ro")}
    opened = []

    def audit(event, args):
        if event == "sqlite3.connect":
            if str(args[0]) not in allowed:
                raise AssertionError("SQLite connection outside the disposable fixture")
            opened.append(str(args[0]))

    sys.addaudithook(audit)
    from copy import deepcopy
    from contextlib import ExitStack
    from dataclasses import asdict, replace
    from io import StringIO
    from unittest.mock import patch
    from uuid import uuid4
    import unittest
    from django.conf import settings
    from apps.ecomotor import target_persistent_demo_settings as official
    if settings.configured:
        raise AssertionError("Configure the protected default before setup")
    configuration = {k: v for k, v in vars(official).items() if k.isupper()}
    configuration["BASE_DIR"] = root
    configuration["DATABASES"] = deepcopy(official.DATABASES)
    configuration["DATABASES"]["default"]["NAME"] = path
    configuration["TARGET_PERSISTENT_DEMO_ALIAS"] = "default"
    settings.configure(**configuration)
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db import connections, transaction, IntegrityError
    from django.db.models.deletion import ProtectedError
    from django.db.migrations.executor import MigrationExecutor
    from django.test.utils import CaptureQueriesContext
    from . import services, playable_services as playable, reward_demo_services as rewards
    from . import models
    from apps.bank.models import Wallet, Transaction
    from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES

    db = connections["default"]
    secret = "c" * 64
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}

    def command(*args, **kwargs):
        return call_command(*args, stdout=StringIO(), stderr=StringIO(), **kwargs)

    def normalized(result):
        value = asdict(replace(result, replay=False))
        # changed, like replay, describes this invocation, not its snapshot.
        value.pop("changed", None)
        return json.loads(json.dumps(value,
                                     default=lambda x: x.isoformat(), sort_keys=True))

    def rows():
        result = {}
        with db.cursor() as cursor:
            for table in db.introspection.table_names(cursor):
                if table.startswith("sqlite_"):
                    continue
                cursor.execute('SELECT * FROM "' + table + '" ORDER BY 1')
                result[table] = {"columns": [c[0] for c in cursor.description],
                                 "rows": [list(row) for row in cursor.fetchall()]}
        return json.loads(json.dumps(result, default=lambda value: value.isoformat()))

    def schema():
        with db.cursor() as cursor:
            cursor.execute("SELECT type,name,tbl_name,sql FROM sqlite_master "
                           "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
            return [list(row) for row in cursor.fetchall()]

    def prepare_history():
        command("migrate", "ecomotor_target_demo", "0003_synthetic_rewards", interactive=False)
        executor = MigrationExecutor(db)
        targets = [node for node in executor.loader.graph.leaf_nodes()
                   if node[0] != "ecomotor_target_demo"] + [
                       ("ecomotor_target_demo", "0003_synthetic_rewards")]
        executor.migrate(targets)
        old_apps = executor.loader.project_state(targets).apps
        # Complete the same post_migrate phase as an ordinary historical
        # installation, including content types/permissions of all other apps.
        from django.core.management.sql import emit_post_migrate_signal
        emit_post_migrate_signal(0, False, "default", apps=old_apps, stdout=StringIO())
        command("seed_persistent_target_demo")
        get = lambda name: old_apps.get_model("ecomotor_target_demo", name)
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(services,
                DemoTargetProgress=get("DemoTargetProgress"),
                DemoTargetXPEvent=get("DemoTargetXPEvent"),
                DemoTargetEvolutionEvent=get("DemoTargetEvolutionEvent"),
                TargetCatalogVersion=old_apps.get_model("ecomotor", "TargetCatalogVersion"),
                TargetEpoch=old_apps.get_model("ecomotor", "TargetEpoch")))
            stack.enter_context(patch.multiple(rewards, Reward=get("DemoTargetRewardEvent"),
                XPEvent=get("DemoTargetXPEvent"), Evolution=get("DemoTargetEvolutionEvent")))
            stack.enter_context(patch.multiple(playable, DemoTargetProgress=get("DemoTargetProgress"),
                Configuration=get("DemoTargetOptionConfiguration"),
                State=get("DemoTargetPlayableState"), Event=get("DemoTargetPlayableEvent")))
            progress = services.create_demo_progress(session_token=secret)
            saved = {"progress": progress.pk, "calls": []}

            def remember(kind, args, result):
                saved["calls"].append({"kind": kind, "args": args, "result": normalized(result)})

            for activity in ("challenge", "visit"):
                token = rewards.issue_reward_fact(progress, activity=activity, session_token=secret)
                args = {"activity": activity, "fact_token": token}
                remember("reward", args, rewards.apply_demo_reward(progress, **args, session_token=secret))
            token = services.issue_demo_operation(progress, session_token=secret)
            args = {"amount": 100, "operation_token": token}
            remember("xp", args, services.grant_demo_target_xp(progress, **args, session_token=secret))
            for option, points in (("persist-demo-tech-gamer", 45), ("persist-demo-epoch-3", 10)):
                token = playable.issue_playable_operation(progress, action="configure", session_token=secret)
                args = {"option_code": option, "increments": [(c, points if i == 0 else 0)
                        for i, c in enumerate(TARGET_STAT_CODES)], "operation_token": token}
                if option.endswith("epoch-3"):
                    args["expected_revision"] = 1
                remember("configure", args, playable.configure_demo_option(progress, **args, session_token=secret))
            args = {"option_code": "persist-demo-tech-gamer", "expected_revision": 2,
                    "operation_token": playable.issue_playable_operation(
                        progress, action="switch", session_token=secret)}
            playable.switch_demo_option(progress, **args, session_token=secret)
            args = {"option_code": "persist-demo-tech-gamer", "expected_revision": 3,
                    "configuration_revision": 1,
                    "increments": [(c, 24 if i == 0 else 0) for i, c in enumerate(TARGET_STAT_CODES)],
                    "operation_token": playable.issue_playable_operation(
                        progress, action="redistribute", session_token=secret)}
            remember("redistribute", args, playable.redistribute_demo_option(progress, **args, session_token=secret))
            assert get("DemoTargetEvolutionEvent").objects.count() == 6
            assert get("DemoTargetRewardEvent").objects.count() == 2
        saved["rows"], saved["schema"] = rows(), schema()
        assert "synthetic_user_id" not in saved["rows"][models.DemoTargetProgress._meta.db_table]["columns"]
        assert not any(row[1:3] == ["ecomotor_target_demo", "0004_rewards_bank_schema"]
                       for row in saved["rows"]["django_migrations"]["rows"])
        (root / "historical.json").write_text(json.dumps(saved), encoding="utf-8")
        evidence["observations"].append("Real 0003 rows, raw V1 JSON and signed replay tokens saved; no 0004 applied")

    class SchemaTests(unittest.TestCase):
        def test_historical_copy(self):
            old = json.loads((root / "historical.json").read_text(encoding="utf-8"))
            self.assertEqual(rows(), old["rows"])
            command("migrate", interactive=False)
            after = rows()
            for table, previous in old["rows"].items():
                columns = after[table]["columns"]
                indexes = [columns.index(c) for c in previous["columns"]]
                actual = [[row[i] for i in indexes] for row in after[table]["rows"]]
                if table == "django_migrations":
                    actual = [row for row in actual if row[2] != "0004_rewards_bank_schema"]
                self.assertEqual(actual, previous["rows"], table)
            changed = {models.DemoTargetProgress._meta.db_table, models.DemoTargetRewardEvent._meta.db_table}
            self.assertEqual([r for r in schema() if r[2] not in changed],
                             [r for r in old["schema"] if r[2] not in changed])
            with db.cursor() as cursor:
                for table in changed:
                    constraints = db.introspection.get_constraints(cursor, table)
                    old_sql = next(r[3] for r in old["schema"] if r[:3] == ["table", table, table])
                    import re
                    for name in re.findall(r'CONSTRAINT "([^"]+)"', old_sql):
                        self.assertIn(name, constraints)
            progress = models.DemoTargetProgress.objects.get(pk=old["progress"])
            self.assertIsNone(progress.synthetic_user_id)
            self.assertEqual(list(models.DemoTargetRewardEvent.objects.values_list(
                "coin_amount", "bank_transaction_id")), [(0, None), (0, None)])
            before_replay = rows()
            functions = {"xp": services.grant_demo_target_xp, "reward": rewards.apply_demo_reward,
                         "configure": playable.configure_demo_option,
                         "redistribute": playable.redistribute_demo_option}
            with CaptureQueriesContext(db) as queries:
                for call in old["calls"]:
                    result = functions[call["kind"]](progress, **call["args"], session_token=secret)
                    self.assertTrue(result.replay)
                    self.assertEqual(normalized(result), call["result"])
                self.assertEqual(len(rewards.read_demo_rewards(progress, session_token=secret)), 2)
            self.assertEqual(rows(), before_replay)
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")) for q in queries))
            self.assertEqual(get_user_model().objects.count(), 0)
            self.assertEqual(Wallet.objects.count(), 0)
            self.assertEqual(Transaction.objects.count(), 0)
            db.close()
            self.assertEqual(rows(), before_replay)
            self.repeat_migrate()
            evidence["observations"].append("Physical 0003 copy: all rows/raw JSON/identities and unrelated schema identical; actual V1 replays read-only after 0004 and reopen")

        def repeat_migrate(self):
            with CaptureQueriesContext(db) as queries:
                command("migrate", interactive=False)
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")) for q in queries))
            executor = MigrationExecutor(db)
            self.assertEqual(executor.migration_plan(executor.loader.graph.leaf_nodes()), [])
            command("makemigrations", check=True, dry_run=True)
            command("check")

        def test_fresh_schema_constraints(self):
            command("migrate", interactive=False)
            command("seed_persistent_target_demo")
            self.assertEqual(get_user_model().objects.count(), 0)
            self.assertEqual(Wallet.objects.count(), 0)
            progress = services.create_demo_progress(session_token=secret)
            other = services.create_demo_progress(session_token=secret)
            self.assertIsNone(progress.synthetic_user_id)
            User = get_user_model()
            user = User(username="schema-only", is_active=False)
            user.set_unusable_password()
            user.save()
            progress.synthetic_user = user
            progress.save(update_fields=["synthetic_user"])
            with self.assertRaises(IntegrityError), transaction.atomic():
                models.DemoTargetProgress.objects.filter(pk=other.pk).update(synthetic_user=user)
            with self.assertRaises(ProtectedError):
                user.delete()
            # Structural test rows only: no credit_coins call or monetary activity.
            wallet = Wallet.objects.create(user=user)
            bank = Transaction.objects.create(wallet=wallet, transaction_type="REWARD", amount=5,
                balance_after=5, operation_key="schema-only", source_platform="schema-only",
                issuing_entity="schema-only", request_fingerprint="a" * 64)
            token = services.issue_demo_operation(progress, session_token=secret)
            grant = services.grant_demo_target_xp(progress, amount=100, operation_token=token, session_token=secret)
            from django.utils.timezone import now

            def reward(**extra):
                values = dict(progress=progress, origin_code="schema-only", fact_id=uuid4().hex,
                    recipient_id=f"demo-progress:{progress.pk}", activity_type="schema-only",
                    occurred_at=now(), fingerprint_version="schema-only", fingerprint="a" * 64,
                    rule_set_version="schema-only", status="NO_REWARD", reason_codes=[],
                    xp_amount=0, snapshot={"fixture": "constraint-only"})
                values.update(extra)
                return models.DemoTargetRewardEvent.objects.create(**values)

            no_reward = reward()
            self.assertEqual((no_reward.coin_amount, no_reward.bank_transaction_id), (0, None))
            xp = reward(status="APPLIED", xp_amount=100, xp_event_id=grant.event_id)
            coins = reward(status="APPLIED", coin_amount=5, bank_transaction=bank)
            self.assertEqual((xp.coin_amount, coins.xp_amount), (0, 0))
            for values in (
                dict(status="APPLIED"), dict(status="APPLIED", coin_amount=5),
                dict(status="APPLIED", bank_transaction=bank),
                dict(status="APPLIED", xp_amount=1),
                dict(status="APPLIED", xp_amount=1, coin_amount=5),
                dict(coin_amount=5), dict(bank_transaction=bank), dict(xp_amount=1),
                dict(status="UNKNOWN"), dict(coin_amount=-1),
            ):
                with self.subTest(values=values):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        reward(**values)
            with self.assertRaises(IntegrityError), transaction.atomic():
                reward(status="APPLIED", coin_amount=5, bank_transaction=bank)
            # Updates of existing valid rows isolate the outcome CHECK from
            # uniqueness/FK constraints; both effects and crossed causes fail.
            for row, changes in (
                (xp, dict(coin_amount=1)), (xp, dict(bank_transaction=bank)),
                (coins, dict(xp_amount=1)), (coins, dict(coin_amount=0)),
                (coins, dict(bank_transaction=None)),
                (no_reward, dict(status="APPLIED")),
            ):
                with self.subTest(changes=changes):
                    with self.assertRaisesRegex(IntegrityError, "demo_reward_outcome_valid"), transaction.atomic():
                        models.DemoTargetRewardEvent.objects.filter(pk=row.pk).update(**changes)
            with self.assertRaises(IntegrityError), transaction.atomic():
                models.DemoTargetProgress.objects.filter(pk=other.pk).update(synthetic_user_id=2**63-1)
            with self.assertRaises(ProtectedError):
                bank.delete()
            with self.assertRaises((OverflowError, IntegrityError)), transaction.atomic():
                reward(status="APPLIED", coin_amount=2**63, bank_transaction=bank)
            coins.coin_amount = 2**63 - 1
            coins.save(update_fields=["coin_amount"])
            self.assertEqual(models.DemoTargetRewardEvent.objects.get(pk=coins.pk).coin_amount, 2**63 - 1)
            executor = MigrationExecutor(db)
            migration = executor.loader.disk_migrations[("ecomotor_target_demo", "0004_rewards_bank_schema")]
            self.assertIn(("bank", "0001_initial"), migration.dependencies)
            self.assertIn(("ecomotor_target_demo", "0003_synthetic_rewards"), migration.dependencies)
            self.assertEqual({type(op).__name__ for op in migration.operations},
                             {"AddField", "RemoveConstraint", "AddConstraint"})
            self.repeat_migrate()
            evidence["observations"].append("Fresh SQLite: nullable defaults, three outcome arms, invalid states, unique/PROTECT references, SQLite range and repeat migrate verified; no automatic provisioning")

    try:
        if scenario == "before":
            prepare_history()
            evidence.update(success=True, tests=1, failures=0, errors=0, skipped=0)
        else:
            name = "test_historical_copy" if scenario == "historical" else "test_fresh_schema_constraints"
            result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([SchemaTests(name)]))
            evidence.update(success=result.wasSuccessful(), tests=result.testsRun,
                            failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    finally:
        connections.close_all()
    evidence.update(connections_closed=all(c.connection is None for c in connections.all()),
                    only_fixture_connections=bool(opened) and all(p in allowed for p in opened))
    print("BANK_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True))
    return 0 if evidence["success"] else 1


if __name__ == "__main__":
    raise SystemExit(run(*sys.argv[1:]))
