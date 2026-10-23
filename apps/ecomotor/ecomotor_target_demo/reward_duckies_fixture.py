"""Test-only child: real Duckies API inside the existing Rewards boundary.

No object reward coordinator, schema, rules or snapshots are implemented here.
The parent owns and removes the directory after all child connections close.
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
            or not root.name.startswith("ducky-rewards-duckies-") or not root.is_dir()
            or root.is_symlink() or getattr(root, "is_junction", lambda: False)()):
        raise ValueError("An owned fresh test TemporaryDirectory is required")
    path = root / "instance" / "target_persistent_demo.sqlite3"
    if not path.parent.is_dir() or any(path.parent.iterdir()):
        raise ValueError("Only explicit migrate may create the absent fixture")
    allowed = {path.as_uri() + "?mode=" + mode for mode in ("rw", "rwc", "ro")}
    opened = []

    def audit(event, arguments):
        if event == "sqlite3.connect":
            destination = str(arguments[0])
            if destination not in allowed:
                raise AssertionError("SQLite connection outside the owned Duckies fixture")
            opened.append(destination)

    sys.addaudithook(audit)
    from copy import deepcopy
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import contextmanager
    from io import StringIO
    from threading import Barrier, Event
    from time import monotonic
    from uuid import uuid4
    from django.conf import settings
    from apps.ecomotor import target_persistent_demo_settings as official

    if settings.configured:
        raise AssertionError("Configure protected default before django.setup()")
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
    from django.db import connections, IntegrityError
    from apps.bank.models import Wallet, Transaction
    from apps.duckies.models import Ducky, Item, ItemLevel, ItemGrant, InventoryItem
    from apps.duckies.services import grant_item
    from apps.users.models import UserProfileEcomotor
    from . import services
    from .isolation import demo_connection, MIGRATING
    from .models import DemoTargetXPEvent, DemoTargetEvolutionEvent, DemoTargetRewardEvent

    db = connections["default"]
    User = get_user_model()
    secret = "e" * 64
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}

    def observe(sql, parameters=()):
        other = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
        try:
            if other is db.connection:
                raise AssertionError("Observer must own an independent native connection")
            return other.execute(sql, parameters).fetchall()
        finally:
            other.close()

    def provision():
        user = User(username="duckies-fixture-" + uuid4().hex, is_active=False)
        user.set_unusable_password()
        user.save(using="default")
        wallet = Wallet.objects.create(user=user)
        ducky = Ducky.objects.create(user=user, sex=Ducky.SEX[0][0], selected_outfit=None)
        return user, wallet, ducky

    def deliver(user, item, key, reference="original"):
        return grant_item(user, item, 1, key, item_level=None,
                          reference_type="demo_duckies_fixture", reference_id=reference)

    @contextmanager
    def trace():
        native = db.connection
        statements, writes = [], []

        def inspect(execute, sql, params, many, context):
            if sql.startswith(('INSERT INTO "duckies_', 'UPDATE "duckies_')):
                if (context["connection"] is not db or db.connection is not native
                        or not db.in_atomic_block or db.get_autocommit()
                        or len(db.atomic_blocks) != 2 or not native.in_transaction):
                    raise AssertionError("Duckies write outside shared default/savepoint")
                writes.append((db.alias, id(native)))
            return execute(sql, params, many, context)

        native.set_trace_callback(statements.append)
        try:
            with db.execute_wrapper(inspect):
                yield statements, writes
        finally:
            native.set_trace_callback(None)

    class RewardsDuckiesTests(unittest.TestCase):
        def setUp(self):
            self.progress = services.create_demo_progress(session_token=secret)
            self.user, self.wallet, self.ducky = provision()
            self.progress.synthetic_user = self.user
            self.progress.save(update_fields=["synthetic_user"])
            self.item = Item.objects.create(code="fixture-hint-" + uuid4().hex,
                name="Synthetic fixture HINT", category=Item.HINT, consumable=True, is_active=True)

        def boundary(self):
            return services._xp_transaction(self.progress, session_token=secret)

        def quantity(self):
            return sum(row[0] for row in observe(
                "SELECT quantity FROM duckies_inventoryitem WHERE ducky_id=?", (self.ducky.pk,)))

        def unchanged_business(self):
            self.progress.refresh_from_db()
            self.wallet.refresh_from_db()
            self.assertEqual((self.progress.xp_total, self.progress.current_level,
                              self.wallet.available_balance), (0, 1, 0))
            for model in (Transaction, UserProfileEcomotor, DemoTargetXPEvent,
                          DemoTargetEvolutionEvent, DemoTargetRewardEvent, ItemLevel):
                self.assertEqual(model.objects.count(), 0, model.__name__)
            self.assertFalse(self.user.is_active or self.user.is_staff or self.user.is_superuser
                             or self.user.has_usable_password())
            self.assertIsNone(self.ducky.selected_outfit_id)

        def test_shared_default_savepoint_commit(self):
            native = db.connection
            key = "ri1:fixture:" + uuid4().hex
            with trace() as (sql, writes):
                with self.boundary() as context:
                    current, alias = services._check_xp_transaction(context)
                    self.assertEqual((alias, current.pk), ("default", self.progress.pk))
                    self.assertIs(context.connection, native)
                    self.assertEqual(db.settings_dict["ENGINE"], official.DATABASES["default"]["ENGINE"])
                    self.assertEqual(db.settings_dict["OPTIONS"], {"transaction_mode": "IMMEDIATE", "timeout": 5})
                    self.assertEqual(db.transaction_mode, "IMMEDIATE")
                    self.assertEqual(native.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
                    self.assertTrue(path.samefile(native.execute("PRAGMA database_list").fetchone()[2]))
                    grant = deliver(self.user, self.item, key)
                    self.assertIsInstance(grant, ItemGrant)
                    self.assertEqual((grant._state.db, grant.ducky_id, grant.ducky.user_id,
                        grant.item_id, grant.item_level_id, grant.quantity, grant.operation_key,
                        grant.reference_type, grant.reference_id),
                        ("default", self.ducky.pk, self.user.pk, self.item.pk, None, 1, key,
                         "demo_duckies_fixture", "original"))
                    self.assertEqual(ItemGrant.objects.get(pk=grant.pk).pk, grant.pk)
                    inventory = InventoryItem.objects.get(ducky=self.ducky)
                    self.assertEqual((inventory._state.db, inventory.ducky_id, inventory.item_id,
                                      inventory.item_level_id, inventory.quantity),
                                     ("default", self.ducky.pk, self.item.pk, None, 1))
                    services._check_xp_transaction(context)
                    self.assertEqual(observe("SELECT COUNT(*) FROM duckies_itemgrant WHERE id=?", (grant.pk,)), [(0,)])
                    self.assertEqual(self.quantity(), 0)
            self.assertEqual(sql.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(sql.count("COMMIT"), 1)
            self.assertFalse(any(s.startswith("ROLLBACK") for s in sql))
            opening = next(i for i, s in enumerate(sql) if s.startswith("SAVEPOINT"))
            closing = next(i for i, s in enumerate(sql) if s.startswith("RELEASE SAVEPOINT"))
            self.assertLess(opening, closing)
            self.assertLess(closing, sql.index("COMMIT"))
            self.assertEqual(writes, [("default", id(native))] * 2)
            self.assertEqual(observe("SELECT COUNT(*) FROM duckies_itemgrant WHERE id=?", (grant.pk,)), [(1,)])
            self.assertEqual(self.quantity(), 1)
            self.unchanged_business()
            evidence["observations"].append({"shared_native_connection": True,
                "single_begin_immediate": True, "duckies_savepoint": True, "single_commit": True,
                "uncommitted_delivery_invisible": True, "inventory_quantity": 1,
                "transaction_sql": [s for s in sql if s.startswith(("BEGIN", "SAVEPOINT", "RELEASE", "COMMIT", "ROLLBACK"))]})

        def test_rollback_existing_inventory(self):
            with self.boundary():
                original = deliver(self.user, self.item, uuid4().hex)
            with trace() as (sql, writes):
                with self.assertRaisesRegex(RuntimeError, "after real Duckies delivery"):
                    with self.boundary() as context:
                        grant = deliver(self.user, self.item, uuid4().hex)
                        self.assertEqual(InventoryItem.objects.get(ducky=self.ducky).quantity, 2)
                        services._check_xp_transaction(context)
                        raise RuntimeError("after real Duckies delivery")
            self.assertEqual(sql.count("ROLLBACK"), 1)
            self.assertNotIn("COMMIT", sql)
            self.assertEqual(len(writes), 2)
            self.assertEqual(self.quantity(), 1)
            self.assertEqual(list(ItemGrant.objects.filter(ducky=self.ducky).values_list("pk", flat=True)), [original.pk])
            self.assertFalse(ItemGrant.objects.filter(pk=grant.pk).exists())
            self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
            evidence["observations"].append({"existing_inventory_and_grant_rolled_back": True})

        def test_rollback_new_provisioning(self):
            self.progress = services.create_demo_progress(session_token=secret)
            self.assertIsNone(self.progress.synthetic_user_id)
            with self.assertRaisesRegex(RuntimeError, "rollback synthetic provisioning"):
                with self.boundary():
                    user, wallet, ducky = provision()
                    self.progress.synthetic_user = user
                    self.progress.save(update_fields=["synthetic_user"])
                    grant = deliver(user, self.item, uuid4().hex)
                    self.assertTrue(ItemGrant.objects.filter(pk=grant.pk).exists())
                    raise RuntimeError("rollback synthetic provisioning")
            for model, pk in ((User, user.pk), (Wallet, wallet.pk), (Ducky, ducky.pk), (ItemGrant, grant.pk)):
                self.assertFalse(model.objects.filter(pk=pk).exists())
            self.assertEqual(observe("SELECT COUNT(*) FROM duckies_inventoryitem WHERE ducky_id=?", (ducky.pk,)), [(0,)])
            self.progress.refresh_from_db()
            self.assertIsNone(self.progress.synthetic_user_id)
            evidence["observations"].append({"user_wallet_ducky_inventory_grant_rolled_back": True})

        def test_inner_failure_rolls_back_savepoint(self):
            # A real UNIQUE violation at ItemGrant INSERT, after inventory UPDATE.
            # The wrapper injects a failing parameter, never replaces the API/SQL.
            with self.boundary():
                original = deliver(self.user, self.item, "existing-key")

            def violate(execute, sql, params, many, context):
                if sql.startswith('INSERT INTO "duckies_itemgrant"'):
                    names = sql.split("(", 1)[1].split(")", 1)[0].replace('"', '').split(", ")
                    params = list(params)
                    params[names.index("operation_key")] = "existing-key"
                return execute(sql, params, many, context)

            with trace() as (sql, writes):
                with self.boundary() as context:
                    with db.execute_wrapper(violate), self.assertRaises(IntegrityError):
                        deliver(self.user, self.item, "new-key")
                    services._check_xp_transaction(context)
                    self.assertEqual(InventoryItem.objects.get(ducky=self.ducky).quantity, 1)
                    self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).get().pk, original.pk)
            self.assertTrue(any(s.startswith("ROLLBACK TO SAVEPOINT") for s in sql))
            self.assertTrue(any(s.startswith("RELEASE SAVEPOINT") for s in sql))
            self.assertEqual(sql.count("COMMIT"), 1)
            self.assertEqual(self.quantity(), 1)
            evidence["observations"].append({"real_inner_integrity_error": True, "savepoint_rollback": True,
                                              "outer_context_usable_after_inner_error": True})

        def test_duckies_idempotency_and_conflict(self):
            key = uuid4().hex
            with self.boundary():
                first = deliver(self.user, self.item, key)
            with trace() as (sql, writes):
                with self.boundary():
                    replay = deliver(self.user, self.item, key)
            self.assertEqual(first.pk, replay.pk)
            self.assertEqual(writes, [])
            self.assertEqual(self.quantity(), 1)
            for changes in ({"quantity": 2}, {"reference_id": "changed"}, {"reference_type": "changed"}):
                with self.subTest(changes=changes), trace() as (sql, writes):
                    with self.assertRaisesRegex(ValueError, "Conflicto"):
                        with self.boundary():
                            arguments = dict(quantity=1, operation_key=key, item_level=None,
                                             reference_type="demo_duckies_fixture", reference_id="original")
                            arguments.update(changes)
                            grant_item(self.user, self.item, **arguments)
                    self.assertEqual(writes, [])
            self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), 1)
            self.assertEqual(self.quantity(), 1)
            evidence["observations"].append({"duckies_replay_same_grant": True,
                "conflicts_without_writes": True, "not_rewards_coordinator_replay": True})

        def concurrent(self, *, incompatible=False, distinct=False):
            barrier = Barrier(2)
            key = uuid4().hex

            def worker(index):
                connection = connections["default"]
                try:
                    connection.ensure_connection()
                    native = connection.connection
                    barrier.wait(timeout=10)
                    try:
                        with self.boundary() as context:
                            services._check_xp_transaction(context)
                            grant = deliver(self.user, self.item, key + (str(index) if distinct else ""),
                                            "changed" if incompatible and index else "original")
                            services._check_xp_transaction(context)
                        return "ok", grant.pk, id(native)
                    except ValueError as error:
                        if "Conflicto de idempotencia" not in str(error):
                            raise
                        return "conflict", None, id(native)
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(worker, index) for index in range(2)]
                results = [future.result(timeout=20) for future in futures]
            self.assertNotEqual(results[0][2], results[1][2])
            self.assertEqual(sorted(r[0] for r in results), ["conflict", "ok"] if incompatible else ["ok", "ok"])
            expected = 2 if distinct else 1
            self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), expected)
            self.assertEqual(self.quantity(), expected)
            if not incompatible and not distinct:
                self.assertEqual(results[0][1], results[1][1])
            self.unchanged_business()
            evidence["observations"].append({"independent_native_connections": True,
                "incompatible": incompatible, "distinct": distinct, "outcomes": [r[0] for r in results],
                "committed_grants": expected, "inventory_quantity": expected})

        def test_concurrent_compatible(self):
            self.concurrent()

        def test_concurrent_incompatible(self):
            self.concurrent(incompatible=True)

        def test_concurrent_distinct(self):
            self.concurrent(distinct=True)

        def test_timeout_and_explicit_recovery(self):
            held, release = Event(), Event()
            key = uuid4().hex

            def blocker():
                connection = connections["default"]
                try:
                    with self.boundary() as context:
                        services._check_xp_transaction(context)
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
                            deliver(self.user, self.item, key)
                    elapsed = monotonic() - started
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertLess(elapsed, 12)
                    self.assertEqual(self.quantity(), 0)
                    self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())
                    self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                    self.assertTrue(db.get_autocommit())
                finally:
                    release.set()
                blocker_id = future.result(timeout=10)
            self.assertNotEqual(blocker_id, id(db.connection))
            with self.boundary():
                first = deliver(self.user, self.item, key)
            with self.boundary():
                self.assertEqual(deliver(self.user, self.item, key).pk, first.pk)
            self.assertEqual(self.quantity(), 1)
            self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), 1)
            evidence["observations"].append({"real_timeout_seconds": round(elapsed, 3),
                "no_partial_delivery": True, "explicit_retry_then_duckies_replay": True})

        def test_injected_child_failure(self):
            self.assertIsNotNone(demo_connection().connection)
            self.fail("injected Duckies child failure after protected connection opened")

    groups = {
        "atomicity": ("test_shared_default_savepoint_commit", "test_rollback_existing_inventory",
                      "test_rollback_new_provisioning", "test_inner_failure_rolls_back_savepoint"),
        "idempotency": ("test_duckies_idempotency_and_conflict",),
        "concurrency": ("test_concurrent_compatible", "test_concurrent_incompatible",
                        "test_concurrent_distinct", "test_timeout_and_explicit_recovery"),
        "failure": ("test_injected_child_failure",),
    }
    try:
        try:
            demo_connection()
        except ImproperlyConfigured:
            pass
        else:
            raise AssertionError("Ordinary opening accepted an absent database")
        if path.exists():
            raise AssertionError("SQLite exists before explicit migration")
        call_command("migrate", database="default", verbosity=0, stdout=StringIO())
        if MIGRATING.get():
            raise AssertionError("Migration creation context leaked")
        call_command("seed_persistent_target_demo", stdout=StringIO())
        db = demo_connection()
        suite = unittest.TestSuite(RewardsDuckiesTests(name) for name in groups[scenario])
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        evidence.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                        skipped=len(result.skipped), success=result.wasSuccessful())
    finally:
        connections.close_all()
    evidence["connections_closed"] = all(c.connection is None for c in connections.all())
    evidence["only_fixture_connections"] = bool(opened) and all(name in allowed for name in opened)
    print("DUCKIES_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2]))
