"""Test-only Bank/default integration in a guarded disposable subprocess.

Uses the same pre-setup/default/audit-hook boundary proved in PR #103. Real
services, file-backed SQLite and native connections are never replaced by mocks.
Fault injection wraps real work only to demonstrate rollback or corrupt fixtures.
"""

import json
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import gettempdir
import unittest


def run(root, scenario):
    root = Path(root).absolute()
    if (root.parent.resolve() != Path(gettempdir()).resolve()
            or not root.name.startswith("ducky-bank-default-") or not root.is_dir()):
        raise ValueError("An owned test TemporaryDirectory is required")
    path = root / "instance" / "target_persistent_demo.sqlite3"
    if not path.parent.is_dir() or any(path.parent.iterdir()):
        raise ValueError("Only migrate may create the empty fixture")
    allowed = {path.as_uri() + "?mode=" + mode for mode in ("rw", "rwc", "ro")}
    opened = []

    def audit(event, args):
        if event == "sqlite3.connect":
            if str(args[0]) not in allowed:
                raise AssertionError("SQLite connection outside protected default fixture")
            opened.append(str(args[0]))

    sys.addaudithook(audit)
    from copy import deepcopy
    from contextlib import contextmanager
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import asdict, FrozenInstanceError
    from datetime import datetime, timezone
    from io import StringIO
    from threading import Barrier, Event
    from time import monotonic
    from unittest.mock import patch
    from uuid import uuid4
    from django.conf import settings
    from apps.ecomotor import target_persistent_demo_settings as official
    if settings.configured:
        raise AssertionError("default must be configured before setup")
    configuration = {k: v for k, v in vars(official).items() if k.isupper()}
    configuration["BASE_DIR"] = root
    configuration["DATABASES"] = deepcopy(official.DATABASES)
    configuration["DATABASES"]["default"]["NAME"] = path
    configuration["TARGET_PERSISTENT_DEMO_ALIAS"] = "default"
    settings.configure(**configuration)
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.core import signing
    from django.core.exceptions import ImproperlyConfigured
    from django.core.management import call_command
    from django.db import connections, transaction
    from django.test.utils import CaptureQueriesContext
    from apps.bank import services as bank
    from apps.bank.models import Wallet, Transaction
    from apps.ecomotor.reward_types import RewardDecision, RewardRuleSet, ProposedEffect, RewardIdentity, ValidatedRewardFact
    from apps.ecomotor.reward_identity import semantic_fingerprint
    from . import services as xp, reward_demo_services as rewards, reward_demo_rules as rules
    from . import playable_services as playable
    from .models import (DemoTargetProgress as Progress, DemoTargetRewardEvent as Reward,
                         DemoTargetXPEvent as XP, DemoTargetEvolutionEvent as Evolution,
                         DemoTargetOptionConfiguration as Configuration)
    from .isolation import demo_connection, MIGRATING

    db = connections["default"]
    User = get_user_model()
    secret = "d" * 64
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}

    def rows():
        with db.cursor() as cursor:
            result = {}
            for table in db.introspection.table_names(cursor):
                cursor.execute('SELECT * FROM "' + table + '" ORDER BY 1')
                result[table] = cursor.fetchall()
            return result

    def observer(sql, args=()):
        other = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            return other.execute(sql, args).fetchall()
        finally:
            other.close()

    def allocation(points):
        return tuple((code, points if i == 0 else 0)
                     for i, code in enumerate(("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")))

    class RewardsBankTests(unittest.TestCase):
        def setUp(self):
            self.progress = xp.create_demo_progress(session_token=secret)

        def token(self, activity="coin_challenge", progress=None, owner=secret):
            return rewards.issue_reward_fact(progress or self.progress, activity=activity, session_token=owner)

        def apply(self, token=None, activity="coin_challenge", progress=None, owner=secret):
            progress = progress or self.progress
            return rewards.apply_demo_reward(progress, activity=activity,
                fact_token=token or self.token(activity, progress, owner), session_token=owner)

        def direct(self, amount=100):
            return xp.grant_demo_target_xp(self.progress, amount=amount,
                operation_token=xp.issue_demo_operation(self.progress, session_token=secret), session_token=secret)

        def test_primary_real_credit_and_stationary_progress(self):
            self.direct(700)
            for option, points in (("persist-demo-tech-gamer", 45), ("persist-demo-epoch-3", 10)):
                playable.configure_demo_option(self.progress, option_code=option, increments=allocation(points),
                    operation_token=playable.issue_playable_operation(self.progress, action="configure", session_token=secret),
                    session_token=secret, **({"expected_revision": 1} if option.endswith("epoch-3") else {}))
            before = rows()
            result = self.apply()
            self.assertEqual((result.status, result.coin_amount, result.xp_amount, result.xp_event_id), ("APPLIED", 5, 0, None))
            self.assertEqual((result.progression.xp_before, result.progression.xp_after), (700, 700))
            self.assertEqual(result.evolution_ids, ())
            self.assertEqual((result.bank.amount, result.bank.balance_before, result.bank.balance_after), (5, 0, 5))
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            self.assertRegex(user.username, r"^rew-demo-[0-9a-f]{32}$")
            self.assertFalse(user.is_active or user.is_staff or user.is_superuser or user.has_usable_password())
            self.assertEqual((user.email, user.first_name, user.last_name), ("", "", ""))
            self.assertEqual(Wallet.objects.get(user=user).available_balance, 5)
            entry = Transaction.objects.get(pk=result.bank.transaction_id)
            self.assertEqual(entry.transaction_type, "REWARD")
            self.assertEqual(entry.request_fingerprint, result.bank.request_fingerprint)
            reward = Reward.objects.get(pk=result.event_id)
            self.assertEqual(reward.bank_transaction_id, entry.pk)
            self.assertEqual(reward.snapshot["schema"], "demo-reward-result-v2")
            self.assertEqual(reward.snapshot["bank"], asdict(result.bank))
            after = rows()
            for table in before:
                if table not in (User._meta.db_table, Wallet._meta.db_table, Transaction._meta.db_table,
                                 Progress._meta.db_table, Reward._meta.db_table):
                    self.assertEqual(before[table], after[table], table)
            with self.assertRaises(FrozenInstanceError): result.coin_amount = 10
            with self.assertRaises(FrozenInstanceError): result.bank.balance_after = 10
            self.assertFalse(hasattr(result.bank, "__dict__"))
            evidence["observations"].append("Real credit 5, linked inactive User/Wallet/REWARD/V2; XP700/six evolutions/Gamer/Romano unchanged")

        def test_lazy_provisioning_and_closed_facts(self):
            counts = (User.objects.count(), Wallet.objects.count())
            for activity in ("challenge", "visit", "coin_challenge"):
                token = self.token(activity)
                payload = signing.loads(token, salt=rewards.SALT)
                self.assertEqual(payload["fact_version"], "demo-fact-v2" if activity == "coin_challenge" else "demo-fact-v1")
            rewards.read_demo_rewards(self.progress, session_token=secret)
            self.apply(activity="visit")
            self.apply(activity="challenge")
            self.assertEqual((User.objects.count(), Wallet.objects.count()), counts)
            self.assertNotIn("coin_challenge", dict(rules.ACTIVITIES))
            instant = datetime(2026, 10, 23, tzinfo=timezone.utc)
            for activity in ("challenge", "visit"):
                original = ValidatedRewardFact(RewardIdentity(rules.ORIGIN, "a"*32, "demo-progress:1"),
                    activity, instant, {"completed": True} if activity == "challenge" else {"visited": True},
                    {"demo": "DEMO-REWARDS-XP-01", "fact_version": "demo-fact-v1"})
                self.assertEqual(semantic_fingerprint(original), semantic_fingerprint(rules.synthetic_fact(1, "a"*32, instant, activity)))
            results = rewards.read_demo_rewards(self.progress, session_token=secret)
            self.assertEqual([r.coin_amount for r in results], [0, 0])
            self.assertTrue(all(Reward.objects.get(pk=r.event_id).snapshot["bank"] is None for r in results))

        def test_replay_original_balance_rules_and_reopen(self):
            token = self.token()
            first = self.apply(token)
            self.apply()
            self.direct(100)
            before = rows()
            with patch.object(bank, "credit_coins", side_effect=AssertionError("replay cannot credit")), \
                 patch.object(rewards, "evaluate_reward", side_effect=AssertionError("replay cannot evaluate")), \
                 patch.object(rules, "RULE_SET", RewardRuleSet("future-empty", ())), CaptureQueriesContext(db) as queries:
                replay = self.apply(token)
            self.assertTrue(replay.replay)
            self.assertEqual(replay.bank, first.bank)
            self.assertEqual(replay.progression, first.progression)
            self.assertEqual(replay.fingerprint, first.fingerprint)
            self.assertEqual(replay.occurred_at, first.occurred_at)
            self.assertEqual(replay.bank.balance_after, 5)
            self.assertEqual(Wallet.objects.get(pk=first.bank.wallet_id).available_balance, 10)
            self.assertEqual(rows(), before)
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")) for q in queries))
            db.close()
            self.assertEqual(self.apply(token).bank, first.bank)
            evidence["observations"].append("Replay read-only without Bank/evaluation, original balance 5 versus current 10, XP anchor and reopen preserved")

        def test_sessions_tokens_and_parties(self):
            token = self.token()
            other = xp.create_demo_progress(session_token="e" * 64)
            before = rows()
            for call in (
                lambda: self.apply(token + "x"),
                lambda: self.apply(token, activity="challenge"),
                lambda: self.apply(token, owner="e"*64),
                lambda: self.apply(token, progress=other, owner="e"*64),
                lambda: self.apply(xp.issue_demo_operation(self.progress, session_token=secret)),
                lambda: self.apply(playable.issue_playable_operation(self.progress, action="configure", session_token=secret)),
            ):
                with self.assertRaises(xp.DemoAccessError): call()
            self.assertEqual(rows(), before)
            a = self.apply(token)
            b = self.apply(progress=other, owner="e"*64)
            self.assertNotEqual(a.bank.user_id, b.bank.user_id)
            self.assertNotEqual(a.bank.wallet_id, b.bank.wallet_id)
            for progress, owner in ((self.progress, "e"*64), (other, secret)):
                with self.assertRaises(xp.DemoAccessError): rewards.read_demo_rewards(progress, session_token=owner)

        def test_conflict_and_stable_identity_key(self):
            token = self.token()
            first = self.apply(token)
            payload = signing.loads(token, salt=rewards.SALT)
            payload["occurred_at"] = "2026-10-23T01:02:03.000000+00:00"
            incompatible = signing.dumps(payload, salt=rewards.SALT)
            before = rows()
            with self.assertRaises(xp.DemoConflictError): self.apply(incompatible)
            self.assertEqual(rows(), before)
            from hashlib import sha256
            encoded = json.dumps(["demo-reward-bank-key-v1", first.identity.origin_code,
                                  first.identity.fact_id, first.identity.recipient_id], separators=(",", ":"), ensure_ascii=True)
            self.assertEqual(first.bank.operation_key, "rb1:" + sha256(encoded.encode()).hexdigest())
            self.assertEqual(len(first.bank.operation_key), 68)

        def test_unsupported_proposals_abort_without_provisioning(self):
            token = self.token()
            before = rows()
            for effects in ((ProposedEffect("DUCKYCOINS", 6),), (ProposedEffect("XP", 700),),
                            (ProposedEffect("ITEM", 1),), (),
                            (ProposedEffect("DUCKYCOINS", 5), ProposedEffect("XP", 700))):
                with self.subTest(effects=effects), patch.object(rewards, "evaluate_reward",
                    return_value=RewardDecision("bad-test", "test" if effects else None, bool(effects), effects,
                                               () if effects else ("NO_MATCHING_RULE",))):
                    with self.assertRaises(rewards.DemoRewardConfigurationError): self.apply(token)
            self.assertEqual(rows(), before)

        def test_single_outer_commit_same_native_connection(self):
            token = self.token()
            statements, writes = [], []
            native = db.connection
            original = bank.credit_coins
            def credit(*args, **kwargs):
                ledger = original(*args, **kwargs)
                self.assertEqual(observer("SELECT available_balance FROM bank_wallet WHERE id=?", (ledger.transaction.wallet_id,)), [])
                self.assertEqual(observer("SELECT id FROM bank_transaction WHERE id=?", (ledger.transaction.pk,)), [])
                return ledger
            def trace(execute, sql, params, many, context):
                if sql.startswith(('UPDATE "bank_wallet"', 'INSERT INTO "bank_transaction"')):
                    self.assertIs(context["connection"], db)
                    self.assertIs(db.connection, native)
                    self.assertEqual(len(db.atomic_blocks), 2)
                    writes.append(sql)
                return execute(sql, params, many, context)
            native.set_trace_callback(statements.append)
            try:
                with patch.object(bank, "credit_coins", side_effect=credit), db.execute_wrapper(trace):
                    result = self.apply(token)
            finally:
                native.set_trace_callback(None)
            self.assertEqual(statements.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(statements.count("COMMIT"), 1)
            self.assertTrue(any(s.startswith("SAVEPOINT") for s in statements))
            self.assertTrue(any(s.startswith("RELEASE SAVEPOINT") for s in statements))
            self.assertEqual(len(writes), 2)
            self.assertEqual(observer("SELECT available_balance FROM bank_wallet WHERE id=?", (result.bank.wallet_id,)), [(5,)])
            evidence["observations"].append("One native default BEGIN IMMEDIATE, Bank savepoint, two Bank writes, one COMMIT; independent reader sees no uncommitted provision/credit")

        def test_rollback_after_real_credit(self):
            token = self.token()
            before = rows()
            original = bank.credit_coins
            def fail(*args, **kwargs):
                ledger = original(*args, **kwargs)
                self.assertTrue(ledger.created)
                raise RuntimeError("after real Bank credit")
            with patch.object(bank, "credit_coins", side_effect=fail):
                with self.assertRaisesRegex(RuntimeError, "after real Bank credit"): self.apply(token)
            self.assertEqual(rows(), before)
            self.assertEqual(self.apply(token).coin_amount, 5)

        def test_rollback_reward_save_and_final_causal_verification(self):
            token = self.token()
            before = rows()
            # The first check is immediately after Bank. The second check is
            # the real persisted RewardEvent/V2 read before the outer commit.
            original = rewards._bank_snapshot
            calls = []
            def fail_second(*args):
                value = original(*args)
                calls.append(value)
                if len(calls) == 2: raise xp.DemoIntegrityError("final causal verification")
                return value
            with patch.object(rewards, "_bank_snapshot", side_effect=fail_second):
                with self.assertRaisesRegex(xp.DemoIntegrityError, "final causal"): self.apply(token)
            self.assertEqual(len(calls), 2)
            self.assertEqual(rows(), before)
            with patch.object(Reward, "save", side_effect=RuntimeError("RewardEvent save")):
                with self.assertRaisesRegex(RuntimeError, "RewardEvent save"): self.apply(token)
            self.assertEqual(rows(), before)
            self.assertEqual(self.apply(token).coin_amount, 5)
            evidence["observations"].append("Real-credit, RewardEvent-save and final-causal failures roll back User/Wallet/Transaction/Reward together; explicit retry once")

        def test_bank_errors_outer_transaction_and_overflow(self):
            token = self.token()
            before = rows()
            with transaction.atomic():
                with self.assertRaises(xp.DemoTransactionError): self.apply(token)
            for error in (bank.InvalidAmount("invalid"), bank.WalletNotProvisioned("missing"), bank.IdempotencyConflict("conflict")):
                with patch.object(bank, "credit_coins", side_effect=error):
                    with self.assertRaises(type(error)): self.apply(token)
                self.assertEqual(rows(), before)
            first = self.apply(token)
            Wallet.objects.filter(pk=first.bank.wallet_id).update(available_balance=bank.MAX_BALANCE)
            next_token = self.token()
            before = rows()
            with self.assertRaises(bank.InvalidAmount): self.apply(next_token)
            self.assertEqual(rows(), before)

        def test_v2_corrupt_snapshots_rejected_strictly(self):
            first = self.apply()
            row = Reward.objects.get(pk=first.event_id)
            original = deepcopy(row.snapshot)
            mutations = (
                lambda s: s.update(coin_amount=True), lambda s: s.update(coin_amount=5.0),
                lambda s: s.update(extra="unknown"), lambda s: s.update(schema="unknown"),
                lambda s: s.update(status="NO_REWARD"), lambda s: s.update(bank=None),
                lambda s: s["bank"].update(balance_after=999),
                lambda s: s["bank"].update(user_id=True),
                lambda s: s["bank"].update(extra="unknown"),
                lambda s: s["bank"].pop("created_at"),
                lambda s: s.update(anchor_xp_event_id=True),
            )
            for mutate in mutations:
                value = deepcopy(original)
                mutate(value)
                Reward.objects.filter(pk=row.pk).update(snapshot=value)
                before = rows()
                with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
                self.assertEqual(rows(), before)
            Reward.objects.filter(pk=row.pk).update(snapshot=original)

        def test_bank_metadata_and_reference_corruption(self):
            first = self.apply()
            entry = Transaction.objects.get(pk=first.bank.transaction_id)
            for field, value in (("amount", 6), ("reference_id", "wrong"), ("operation_key", "wrong"),
                                 ("source_platform", "wrong"), ("request_fingerprint", "0"*64),
                                 ("issuing_entity", "wrong"), ("balance_after", 6)):
                original = getattr(entry, field)
                Transaction.objects.filter(pk=entry.pk).update(**{field: value})
                with self.subTest(field=field), self.assertRaises(xp.DemoIntegrityError):
                    rewards.read_demo_rewards(self.progress, session_token=secret)
                Transaction.objects.filter(pk=entry.pk).update(**{field: original})

        def test_crossed_wallet_user_and_missing_causes(self):
            first = self.apply()
            other = xp.create_demo_progress(session_token=secret)
            second = self.apply(progress=other)
            Transaction.objects.filter(pk=first.bank.transaction_id).update(wallet_id=second.bank.wallet_id)
            with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
            Transaction.objects.filter(pk=first.bank.transaction_id).update(wallet_id=first.bank.wallet_id)
            # Explicit isolated corruption bypasses only FK checking, never the
            # protected backend or file boundary. Restore before leaving test.
            entry = Transaction.objects.get(pk=first.bank.transaction_id)
            stored = {f.attname: getattr(entry, f.attname) for f in entry._meta.fields}
            with db.constraint_checks_disabled():
                with db.cursor() as cursor:
                    cursor.execute("DELETE FROM bank_transaction WHERE id=%s", [entry.pk])
                with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
                Transaction.objects.create(**stored)
                Transaction.objects.filter(pk=entry.pk).update(created_at=stored["created_at"])
            original_user = self.progress.synthetic_user_id
            self.progress.refresh_from_db()
            original_user = self.progress.synthetic_user_id
            other.refresh_from_db()
            # Remove other binding first so the local unique constraint does
            # not mask the cross-party causal validation being tested.
            Progress.objects.filter(pk=other.pk).update(synthetic_user=None)
            Progress.objects.filter(pk=self.progress.pk).update(synthetic_user_id=other.synthetic_user_id)
            with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
            Progress.objects.filter(pk=self.progress.pk).update(synthetic_user_id=original_user)
            Progress.objects.filter(pk=other.pk).update(synthetic_user_id=other.synthetic_user_id)
            for model, pk in ((Wallet, first.bank.wallet_id), (User, first.bank.user_id)):
                table = db.ops.quote_name(model._meta.db_table)
                with db.constraint_checks_disabled(), db.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {table} WHERE id=%s", [pk])
                    values = cursor.fetchone()
                    columns = ",".join(db.ops.quote_name(c[0]) for c in cursor.description)
                    cursor.execute(f"DELETE FROM {table} WHERE id=%s", [pk])
                    try:
                        before = rows()
                        with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
                        self.assertEqual(rows(), before)
                    finally:
                        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({','.join(['%s'] * len(values))})", values)
            rewards.read_demo_rewards(self.progress, session_token=secret)

        def test_orphan_bank_namespace_and_existing_link_not_repaired(self):
            first = self.apply()
            key = "rb1:" + "0" * 64
            entry = bank.credit_coins(User.objects.get(pk=first.bank.user_id), 5, source=rules.ORIGIN,
                operation_key=key, issuing_entity="EcomotorDemo", reference_type="demo_reward_fact_v1", reference_id=key).transaction
            before = rows()
            with patch.object(bank, "credit_coins", side_effect=AssertionError("cannot adopt")):
                with self.assertRaises(xp.DemoIntegrityError): self.apply()
            self.assertEqual(rows(), before)
            entry.delete()
            User.objects.filter(pk=first.bank.user_id).update(is_active=True)
            before = rows()
            with self.assertRaises(xp.DemoIntegrityError): rewards.read_demo_rewards(self.progress, session_token=secret)
            self.assertEqual(rows(), before)
            User.objects.filter(pk=first.bank.user_id).update(is_active=False)
            unlinked = xp.create_demo_progress(session_token=secret)
            token = self.token(progress=unlinked)
            payload = signing.loads(token, salt=rewards.SALT)
            identity = RewardIdentity(rules.ORIGIN, payload["fact_id"], f"demo-progress:{unlinked.pk}")
            key = rewards._bank_key(identity)
            orphan = bank.credit_coins(User.objects.get(pk=first.bank.user_id), 5,
                source=rules.ORIGIN, operation_key=key, issuing_entity="EcomotorDemo",
                reference_type="demo_reward_fact_v1", reference_id=key).transaction
            before = rows()
            with patch.object(bank, "credit_coins", side_effect=AssertionError("cannot adopt orphan")):
                with self.assertRaises(xp.DemoIntegrityError): self.apply(token, progress=unlinked)
            self.assertEqual(rows(), before)
            orphan.delete()

        def race(self, kind):
            same = self.token()
            token2 = same if kind == "same" else self.token()
            if kind == "conflict":
                payload = signing.loads(same, salt=rewards.SALT)
                payload["occurred_at"] = "2026-10-23T02:03:04.000000+00:00"
                token2 = signing.dumps(payload, salt=rewards.SALT)
            if kind == "direct":
                token2 = xp.issue_demo_operation(self.progress, session_token=secret)
            if kind == "playable":
                self.direct(700)
                token2 = playable.issue_playable_operation(self.progress, action="configure", session_token=secret)
            barrier = Barrier(2)
            def worker(index):
                try:
                    local = connections["default"]
                    local.ensure_connection()
                    native = local.connection
                    barrier.wait(timeout=10)
                    if index == 1 and kind == "direct":
                        value = xp.grant_demo_target_xp(self.progress, amount=100, operation_token=token2, session_token=secret)
                    elif index == 1 and kind == "playable":
                        value = playable.configure_demo_option(self.progress, option_code="persist-demo-tech-gamer",
                            increments=allocation(45), operation_token=token2, session_token=secret)
                    else:
                        value = self.apply(same if index == 0 else token2)
                    return value, native
                except xp.DemoConflictError as error:
                    return error, native
                finally:
                    connections["default"].close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(worker, (0, 1)))
            self.assertIsNot(outcomes[0][1], outcomes[1][1])
            progress = Progress.objects.get(pk=self.progress.pk)
            wallet = Wallet.objects.get(user_id=progress.synthetic_user_id)
            expected = 10 if kind == "different" else 5
            self.assertEqual(wallet.available_balance, expected)
            self.assertEqual(Reward.objects.filter(progress=progress).count(), 2 if kind == "different" else 1)
            if kind == "same": self.assertEqual(sum(result.replay for result, _ in outcomes), 1)
            if kind == "conflict": self.assertEqual(sum(isinstance(result, xp.DemoConflictError) for result, _ in outcomes), 1)
            if kind == "direct": self.assertEqual(progress.xp_total, 100)
            if kind == "playable": self.assertEqual(Configuration.objects.filter(progress=progress).count(), 1)
            rewards.read_demo_rewards(progress, session_token=secret)

        def test_same_fact_concurrency(self): self.race("same")
        def test_different_facts_concurrency(self): self.race("different")
        def test_direct_xp_concurrency(self): self.race("direct")
        def test_playable_concurrency(self): self.race("playable")
        def test_incompatible_fact_concurrency(self): self.race("conflict")

        def test_real_timeout_and_explicit_retry(self):
            token = self.token()
            before = rows()
            held, release = Event(), Event()
            def blocker():
                try:
                    local = connections["default"]
                    with transaction.atomic():
                        held.set()
                        if not release.wait(15): raise AssertionError("blocker timeout")
                finally:
                    connections["default"].close()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(blocker)
                try:
                    self.assertTrue(held.wait(10))
                    started = monotonic()
                    with self.assertRaises(xp.DemoBusyError): self.apply(token)
                    elapsed = monotonic() - started
                    self.assertGreaterEqual(elapsed, 4.5)
                finally:
                    release.set()
                    future.result(timeout=10)
            self.assertEqual(rows(), before)
            first = self.apply(token)
            self.assertTrue(self.apply(token).replay)
            self.assertEqual(Wallet.objects.get(pk=first.bank.wallet_id).available_balance, 5)
            evidence["observations"].append({"real_timeout_seconds": round(elapsed, 3), "retry_without_duplicate": True})

    groups = {
        "functional": ("test_primary_real_credit_and_stationary_progress", "test_lazy_provisioning_and_closed_facts",
            "test_replay_original_balance_rules_and_reopen", "test_sessions_tokens_and_parties",
            "test_conflict_and_stable_identity_key", "test_unsupported_proposals_abort_without_provisioning"),
        "atomicity": ("test_single_outer_commit_same_native_connection", "test_rollback_after_real_credit",
            "test_rollback_reward_save_and_final_causal_verification", "test_bank_errors_outer_transaction_and_overflow"),
        "integrity": ("test_v2_corrupt_snapshots_rejected_strictly", "test_bank_metadata_and_reference_corruption",
            "test_crossed_wallet_user_and_missing_causes", "test_orphan_bank_namespace_and_existing_link_not_repaired"),
        "concurrency": ("test_same_fact_concurrency", "test_different_facts_concurrency", "test_direct_xp_concurrency",
            "test_playable_concurrency", "test_incompatible_fact_concurrency", "test_real_timeout_and_explicit_retry"),
    }
    try:
        try:
            demo_connection()
        except ImproperlyConfigured:
            pass
        else:
            raise AssertionError("Missing SQLite opened before explicit migrate")
        if path.exists(): raise AssertionError("SQLite created before migrate")
        call_command("migrate", verbosity=0, stdout=StringIO())
        if MIGRATING.get(): raise AssertionError("Migration scope leaked")
        call_command("seed_persistent_target_demo", stdout=StringIO())
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(RewardsBankTests(name) for name in groups[scenario]))
        evidence.update(success=result.wasSuccessful(), tests=result.testsRun,
            failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    finally:
        connections.close_all()
    evidence.update(connections_closed=all(c.connection is None for c in connections.all()),
                    only_fixture_connections=bool(opened) and all(p in allowed for p in opened))
    print("BANK_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run(*sys.argv[1:]))
