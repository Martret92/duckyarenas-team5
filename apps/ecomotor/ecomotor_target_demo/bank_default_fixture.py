"""Test-only child process. Never imported by a production service or test discovery.

The caller owns a fresh TemporaryDirectory; Django is configured before setup.
Only the protected backend and the real migration command may create its SQLite.
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
        raise ValueError("A fresh test TemporaryDirectory is required.")
    path = root / "instance" / "target_persistent_demo.sqlite3"
    if not path.parent.is_dir() or any(path.parent.iterdir()):
        raise ValueError("The fixture destination must be empty before migrate.")

    # Fail closed on any attempted SQLite connection outside this fixture,
    # including memory or a personal file. No replacement of sqlite3.connect.
    allowed = {path.as_uri() + "?mode=" + mode for mode in ("rw", "rwc", "ro")}
    opened = []

    def audit(event, arguments):
        if event == "sqlite3.connect":
            destination = str(arguments[0])
            if destination not in allowed:
                raise AssertionError("SQLite connection outside the disposable fixture")
            opened.append(destination)

    sys.addaudithook(audit)

    from copy import deepcopy
    from django.conf import settings
    from apps.ecomotor import target_persistent_demo_settings as official

    if settings.configured:
        raise AssertionError("Child must configure default before Django setup")
    configuration = {k: v for k, v in vars(official).items() if k.isupper()}
    configuration["BASE_DIR"] = root
    configuration["DATABASES"] = deepcopy(official.DATABASES)
    configuration["DATABASES"]["default"]["NAME"] = path
    configuration["TARGET_PERSISTENT_DEMO_ALIAS"] = "default"
    settings.configure(**configuration)

    import django
    django.setup()

    from concurrent.futures import ThreadPoolExecutor
    from contextlib import contextmanager
    from io import StringIO
    from threading import Barrier, Event
    from time import monotonic
    from uuid import uuid4
    from django.contrib.auth import get_user_model
    from django.core.exceptions import ImproperlyConfigured
    from django.core.management import call_command
    from django.db import connections
    from apps.bank.models import Wallet, Transaction, TransactionType
    from apps.bank.services import credit_coins, IdempotencyConflict
    from . import services
    from .isolation import demo_connection, MIGRATING

    db = connections["default"]
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}
    secret = "a" * 64
    User = get_user_model()

    def observe(sql, parameters=()):
        other = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            if other is db.connection:
                raise AssertionError("Observer must have an independent native connection")
            return other.execute(sql, parameters).fetchall()
        finally:
            other.close()

    def provision():
        user = User(username="bank-fixture-" + uuid4().hex, is_active=False)
        user.set_unusable_password()
        user.save(using="default")
        wallet = Wallet.objects.using("default").create(user=user)
        return user, wallet

    def credit(user, key, amount=17, **kwargs):
        return credit_coins(user, amount, source="bank-default-fixture",
                            issuing_entity="Fixture", operation_key=key, **kwargs)

    @contextmanager
    def trace():
        native = db.connection
        statements, writes = [], []

        def inspect(execute, sql, params, many, context):
            if sql.startswith(('INSERT INTO "bank_transaction"', 'UPDATE "bank_wallet"')):
                if (context["connection"] is not db or db.connection is not native
                        or not db.in_atomic_block or db.get_autocommit()
                        or len(db.atomic_blocks) != 2 or not native.in_transaction):
                    raise AssertionError("Bank write did not use the owned default/savepoint")
                writes.append((db.alias, id(native)))
            return execute(sql, params, many, context)

        native.set_trace_callback(statements.append)
        try:
            with db.execute_wrapper(inspect):
                yield statements, writes
        finally:
            native.set_trace_callback(None)

    class BankDefaultTests(unittest.TestCase):
        def setUp(self):
            self.progress = services.create_demo_progress(session_token=secret)

        def boundary(self):
            # The exact existing Rewards/XP transaction owner, not an imitation.
            return services._xp_transaction(self.progress, session_token=secret)

        def test_shared_connection_and_single_commit(self):
            user, wallet = provision()
            native = db.connection
            before = tuple(observe('SELECT COUNT(*) FROM "' + table + '"')[0][0]
                           for table in ("ecomotor_target_demo_demotargetxpevent",
                                         "ecomotor_target_demo_demotargetevolutionevent",
                                         "ecomotor_target_demo_demotargetrewardevent"))
            with trace() as (sql, writes):
                with self.boundary() as context:
                    current, alias = services._check_xp_transaction(context)
                    self.assertEqual(alias, "default")
                    self.assertIs(context.connection, native)
                    self.assertEqual(current.pk, self.progress.pk)
                    self.assertEqual(db.transaction_mode, "IMMEDIATE")
                    self.assertEqual(db.settings_dict["OPTIONS"], {"transaction_mode": "IMMEDIATE", "timeout": 5})
                    self.assertTrue(path.samefile(db.connection.execute("PRAGMA database_list").fetchone()[2]))
                    result = credit(user, uuid4().hex)
                    self.assertTrue(result.created)
                    self.assertEqual((result.transaction._state.db, result.transaction.wallet_id,
                                      result.transaction.transaction_type, result.transaction.amount,
                                      result.transaction.balance_after),
                                     ("default", wallet.pk, TransactionType.REWARD, 17, 17))
                    services._check_xp_transaction(context)  # Bank savepoint has ended.
                    self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(0,)])
                    self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(0,)])
            self.assertEqual(sql.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(sql.count("COMMIT"), 1)
            self.assertFalse(any(s.startswith("ROLLBACK") for s in sql))
            savepoint = next(i for i, s in enumerate(sql) if s.startswith("SAVEPOINT"))
            release = next(i for i, s in enumerate(sql) if s.startswith("RELEASE SAVEPOINT"))
            self.assertLess(savepoint, release)
            self.assertLess(release, sql.index("COMMIT"))
            self.assertEqual(writes, [("default", id(native))] * 2)
            self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(17,)])
            after = tuple(observe('SELECT COUNT(*) FROM "' + table + '"')[0][0]
                          for table in ("ecomotor_target_demo_demotargetxpevent",
                                        "ecomotor_target_demo_demotargetevolutionevent",
                                        "ecomotor_target_demo_demotargetrewardevent"))
            self.assertEqual(after, before)
            evidence["observations"].append({"single_begin_immediate": True, "single_commit": True,
                "bank_savepoint": True, "same_native_connection": True,
                "uncommitted_credit_invisible": True, "balance": 17})

        def test_rollback_credit_on_existing_wallet(self):
            user, wallet = provision()
            with trace() as (sql, writes):
                with self.assertRaisesRegex(RuntimeError, "after successful Bank credit"):
                    with self.boundary():
                        self.assertTrue(credit(user, uuid4().hex).created)
                        raise RuntimeError("after successful Bank credit")
            self.assertEqual(sql.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(sql.count("ROLLBACK"), 1)
            self.assertNotIn("COMMIT", sql)
            self.assertEqual(len(writes), 2)
            self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(0,)])
            self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(0,)])
            self.assertFalse(db.in_atomic_block)
            evidence["observations"].append({"existing_wallet_credit_rolled_back": True})

        def test_rollback_provisioning_and_credit(self):
            with self.assertRaisesRegex(RuntimeError, "rollback new synthetic account"):
                with self.boundary():
                    user, wallet = provision()
                    self.assertTrue(credit(user, uuid4().hex).created)
                    raise RuntimeError("rollback new synthetic account")
            self.assertEqual(observe("SELECT COUNT(*) FROM auth_user WHERE username=?", (user.username,)), [(0,)])
            self.assertEqual(observe("SELECT COUNT(*) FROM bank_wallet WHERE id=?", (wallet.pk,)), [(0,)])
            self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(0,)])
            evidence["observations"].append({"user_wallet_transaction_rolled_back": True})

        def test_bank_idempotency_and_conflicts(self):
            user, wallet = provision()
            key = uuid4().hex
            with self.boundary():
                first = credit(user, key, reference_type="fixture", reference_id="original")
            with self.boundary():
                replay = credit(user, key, reference_type="fixture", reference_id="original")
            self.assertTrue(first.created)
            self.assertTrue(replay.already_applied)
            self.assertEqual(first.transaction.pk, replay.transaction.pk)
            for amount, reference in ((18, "original"), (17, "changed")):
                with self.subTest(amount=amount, reference=reference), self.assertRaises(IdempotencyConflict):
                    with self.boundary():
                        credit(user, key, amount, reference_type="fixture", reference_id=reference)
            self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(17,)])
            self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(1,)])
            evidence["observations"].append({"compatible_bank_replay": True, "amount_and_reference_conflicts": True})

        def test_simultaneous_credits(self):
            for same_key in (True, False):
                with self.subTest(same_key=same_key):
                    user, wallet = provision()
                    keys = [uuid4().hex, uuid4().hex]
                    if same_key:
                        keys[1] = keys[0]
                    barrier = Barrier(2)

                    def worker(index):
                        connection = connections["default"]
                        try:
                            connection.ensure_connection()
                            native = connection.connection
                            barrier.wait(timeout=10)
                            with self.boundary():
                                result = credit(user, keys[index])
                            return result.created, id(native)
                        finally:
                            connection.close()

                    with ThreadPoolExecutor(max_workers=2) as pool:
                        futures = [pool.submit(worker, i) for i in range(2)]
                        results = [future.result(timeout=20) for future in futures]
                    self.assertNotEqual(results[0][1], results[1][1])
                    expected = 1 if same_key else 2
                    self.assertEqual(sum(r[0] for r in results), expected)
                    self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(expected,)])
                    self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(17 * expected,)])
                    evidence["observations"].append({"same_key": same_key, "independent_native_connections": True,
                                                       "serialized_credits": expected})

        def test_real_timeout_and_explicit_retry(self):
            user, wallet = provision()
            key = uuid4().hex
            held, release = Event(), Event()

            def blocker():
                connection = connections["default"]
                try:
                    with self.boundary():
                        native_id = id(connection.connection)
                        held.set()
                        if not release.wait(20):
                            raise AssertionError("Blocker synchronization timeout")
                    return native_id
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(blocker)
                try:
                    self.assertTrue(held.wait(10))
                    started = monotonic()
                    with self.assertRaises(services.DemoBusyError):
                        with self.boundary():
                            credit(user, key)
                    elapsed = monotonic() - started
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertEqual(observe("SELECT COUNT(*) FROM bank_transaction WHERE wallet_id=?", (wallet.pk,)), [(0,)])
                finally:
                    release.set()
                blocker_id = future.result(timeout=10)
            self.assertNotEqual(blocker_id, id(db.connection))
            self.assertFalse(db.in_atomic_block)
            with self.boundary():
                self.assertTrue(credit(user, key).created)
            with self.boundary():
                self.assertTrue(credit(user, key).already_applied)
            self.assertEqual(observe("SELECT available_balance FROM bank_wallet WHERE id=?", (wallet.pk,)), [(17,)])
            evidence["observations"].append({"real_timeout_seconds": round(elapsed, 3), "explicit_retry_once": True})

        def test_injected_child_failure(self):
            self.assertTrue(demo_connection().connection is not None)
            self.fail("injected child failure after protected connection opened")

    groups = {
        "atomicity": ("test_shared_connection_and_single_commit", "test_rollback_credit_on_existing_wallet",
                      "test_rollback_provisioning_and_credit"),
        "idempotency": ("test_bank_idempotency_and_conflicts",),
        "concurrency": ("test_simultaneous_credits", "test_real_timeout_and_explicit_retry"),
        "failure": ("test_injected_child_failure",),
    }
    try:
        # Opening before the explicit migration must fail without creating a file.
        try:
            demo_connection()
        except ImproperlyConfigured:
            pass
        else:
            raise AssertionError("Ordinary opening created the absent SQLite")
        if path.exists():
            raise AssertionError("SQLite was created before migrate")
        call_command("migrate", database="default", verbosity=0, stdout=StringIO())
        if MIGRATING.get():
            raise AssertionError("Migration creation scope leaked")
        call_command("seed_persistent_target_demo", stdout=StringIO())
        db = demo_connection()
        if db.settings_dict["ENGINE"] != official.DATABASES["default"]["ENGINE"]:
            raise AssertionError("Protected engine changed")
        suite = unittest.TestSuite(BankDefaultTests(name) for name in groups[scenario])
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        evidence.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                        skipped=len(result.skipped), success=result.wasSuccessful())
    finally:
        connections.close_all()
    evidence["connections_closed"] = all(c.connection is None for c in connections.all())
    evidence["only_fixture_connections"] = bool(opened) and all(name in allowed for name in opened)
    print("BANK_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2]))
