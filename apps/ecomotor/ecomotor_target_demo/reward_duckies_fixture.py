"""Test-only child: real Duckies API inside the existing Rewards boundary.

2A scenarios retain their original meaning. Separate 2C scenarios exercise the
real coordinator/V3 and real consumption. Only this fixture prepares its Item.
The parent removes the directory after all child connections close.
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
    from dataclasses import asdict, replace, FrozenInstanceError
    from datetime import timedelta
    from threading import Barrier, Event
    from time import monotonic
    from uuid import uuid4
    from unittest.mock import patch
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
    from django.db import connections, IntegrityError, transaction
    from django.core import signing
    from django.test.utils import CaptureQueriesContext
    from django.test import Client
    from html.parser import HTMLParser
    from urllib.parse import urlencode
    from apps.bank.models import Wallet, Transaction
    from apps.duckies.models import Ducky, Item, ItemLevel, ItemGrant, InventoryItem, EquipmentSlot, ItemUsage
    from apps.duckies.services import grant_item
    from apps.duckies import services as duckies
    from apps.ecomotor.reward_types import RewardDecision, ProposedEffect, RewardIdentity, RewardRuleSet
    from apps.ecomotor.reward_identity import semantic_fingerprint
    from apps.users.models import UserProfileEcomotor
    from . import services, reward_demo_services as rewards, reward_demo_rules as rules, playable_services as playable
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

    class RewardsItemServiceTests(unittest.TestCase):
        """2C coordinator cases, independent of the retained 2A API cases."""

        def setUp(self):
            self.progress = services.create_demo_progress(session_token=secret)
            slot, _ = EquipmentSlot.objects.get_or_create(code="fixture-hint-slot", defaults={"name": "Fixture HINT"})
            self.item, _ = Item.objects.update_or_create(code=rules.ITEM_MAPPING.item_code, defaults={
                "name": "Synthetic HINT", "category": Item.HINT, "consumable": True,
                "is_active": True, "slot": slot})

        def token(self, activity="item_challenge", progress=None):
            return rewards.issue_reward_fact(progress or self.progress, activity=activity, session_token=secret)

        def apply(self, token, activity="item_challenge", progress=None):
            return rewards.apply_demo_reward(progress or self.progress, activity=activity,
                fact_token=token, session_token=secret)

        def rows(self):
            with db.cursor() as cursor:
                tables = db.introspection.table_names(cursor)
                return {table: cursor.execute('SELECT * FROM "' + table + '" ORDER BY rowid').fetchall()
                        for table in tables if table != "sqlite_sequence"}

        def replay(self, token, original):
            before = self.rows()

            def no_inventory(execute, sql, params, many, context):
                if "duckies_inventoryitem" in sql.lower():
                    raise AssertionError("Historical replay queried current inventory")
                return execute(sql, params, many, context)

            with db.execute_wrapper(no_inventory), CaptureQueriesContext(db) as queries, \
                    patch.object(duckies, "grant_item", side_effect=AssertionError("Replay delivered again")), \
                    patch.object(rewards, "evaluate_reward", side_effect=AssertionError("Replay reevaluated rules")):
                result = self.apply(token)
            self.assertTrue(result.replay)
            self.assertEqual(asdict(replace(result, replay=False)), asdict(original))
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP")) for q in queries))
            self.assertEqual(self.rows(), before)
            return result

        def test_real_item_and_exact_key(self):
            from hashlib import sha256
            token = self.token()
            before = {m: m.objects.count() for m in (Transaction, DemoTargetXPEvent, DemoTargetEvolutionEvent, UserProfileEcomotor)}
            result = self.apply(token)
            entry = ItemGrant.objects.get(pk=result.item.item_grant_id)
            row = DemoTargetRewardEvent.objects.get(pk=result.event_id)
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            self.assertRegex(user.username, r"^rew-demo-[0-9a-f]{32}$")
            self.assertFalse(user.is_active or user.is_staff or user.is_superuser or user.has_usable_password())
            self.assertEqual(Wallet.objects.get(user=user).available_balance, 0)
            self.assertEqual(InventoryItem.objects.get(ducky__user=user, item=self.item).quantity, 1)
            self.assertEqual((row.item_grant_id, row.xp_event_id, row.bank_transaction_id,
                row.xp_amount, row.coin_amount, row.snapshot["schema"]),
                (entry.pk, None, None, 0, 0, "demo-reward-result-v3"))
            self.assertEqual((entry.quantity, entry.item_level_id, entry.reference_type), (1, None, "demo_reward_item_v1"))
            for identity in (result.identity, RewardIdentity("é", "ñ", "鸭")):
                encoded = json.dumps(["demo-reward-item-key-v1", identity.origin_code, identity.fact_id,
                    identity.recipient_id], ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                self.assertEqual(rewards._item_key(identity), "ri1:" + sha256(encoded.encode("utf-8")).hexdigest())
                self.assertEqual(len(rewards._item_key(identity)), 68)
            self.assertEqual(entry.operation_key, rewards._item_key(result.identity))
            self.assertEqual(entry.reference_id, entry.operation_key)
            self.assertEqual({m: m.objects.count() for m in before}, before)
            self.assertEqual((self.progress.xp_total, self.progress.current_level), (0, 1))
            with self.assertRaises(FrozenInstanceError):
                result.item.quantity = 2
            self.replay(token, result)
            evidence["observations"].append({"coordinator_item_grant": True, "exact_ri1_encoding": True,
                "inventory_increment": 1, "xp_and_bank_unchanged": True})

        def test_lazy_and_bank_compatibility(self):
            item_token = self.token()
            rewards.read_demo_rewards(self.progress, session_token=secret)
            self.progress.refresh_from_db()
            self.assertIsNone(self.progress.synthetic_user_id)
            for activity in ("visit", "challenge"):
                result = self.apply(self.token(activity), activity)
                self.assertIsNone(result.item)
                self.assertEqual(DemoTargetRewardEvent.objects.get(pk=result.event_id).snapshot["schema"], rewards.SNAPSHOT_VERSION)
            self.progress.refresh_from_db()
            self.assertIsNone(self.progress.synthetic_user_id)
            bank = self.apply(self.token("coin_challenge"), "coin_challenge")
            self.assertFalse(Ducky.objects.filter(user_id=bank.bank.user_id).exists())
            original = self.apply(item_token)
            self.assertEqual(original.item.user_id, bank.bank.user_id)
            later = self.apply(self.token("coin_challenge"), "coin_challenge")
            self.assertEqual(later.bank.balance_after, 10)
            self.assertEqual(rewards.read_demo_bank(self.progress, session_token=secret).balance, 10)
            self.assertEqual(original.progression.xp_after, 700)
            self.assertEqual(DemoTargetEvolutionEvent.objects.filter(progress=self.progress).count(), 6)
            self.replay(item_token, original)
            from .forms import REWARD_HTTP_ACTIVITIES
            self.assertIn("item_challenge", dict(REWARD_HTTP_ACTIVITIES))

        def test_real_consumption_then_readonly_replay(self):
            token = self.token()
            original = self.apply(token)
            user = User.objects.get(pk=original.item.user_id)
            duckies.equip_item(user, self.item)
            duckies.consume_item(user, self.item, 1, "fixture-consumption-" + uuid4().hex,
                server_accepted=True, game_reference="synthetic-fixture-game")
            self.assertFalse(InventoryItem.objects.filter(ducky_id=original.item.ducky_id, item=self.item).exists())
            self.assertTrue(ItemUsage.objects.filter(ducky_id=original.item.ducky_id, item=self.item).exists())
            self.assertTrue(ItemGrant.objects.filter(pk=original.item.item_grant_id).exists())
            Item.objects.filter(pk=self.item.pk).update(is_active=False, category=Item.COSMETIC,
                consumable=False, description="Changed after historical delivery")
            self.replay(token, original)
            evidence["observations"].append({"real_equip_and_consume": True,
                "inventory_exhausted": True, "replay_without_inventory_query_or_dml": True})

        def test_reopen_and_future_rules_do_not_reinterpret(self):
            token = self.token()
            original = self.apply(token)
            self.apply(self.token())
            self.apply(self.token("challenge"), "challenge")
            db.close()
            demo_connection()
            with patch.object(rules, "ITEM_RULE_SET", RewardRuleSet("future", ())), \
                    patch.object(rules, "ITEM_MAPPING", replace(rules.ITEM_MAPPING, mapping_version="future")):
                self.replay(token, original)

        def test_existing_playable_configuration_is_unchanged(self):
            self.apply(self.token("challenge"), "challenge")
            from .models import DemoTargetOptionConfiguration, DemoTargetPlayableState, DemoTargetPlayableEvent
            revision = None
            for option in ("persist-demo-tech-gamer", "persist-demo-epoch-3"):
                configured = playable.configure_demo_option(self.progress, option_code=option,
                    increments=tuple((code, 0) for code in ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")),
                    operation_token=playable.issue_playable_operation(self.progress, action="configure", session_token=secret),
                    session_token=secret, expected_revision=revision)
                revision = configured.after.revision
            models = (DemoTargetOptionConfiguration, DemoTargetPlayableState, DemoTargetPlayableEvent,
                DemoTargetXPEvent, DemoTargetEvolutionEvent)
            before = {m: list(m.objects.filter(progress=self.progress).values()) for m in models}
            self.apply(self.token())
            self.assertEqual({m: list(m.objects.filter(progress=self.progress).values()) for m in models}, before)

        def test_invalid_item_configuration(self):
            token = self.token()
            for fields in ({"code": "wrong-code"}, {"is_active": False}, {"category": Item.ATTACK}, {"consumable": False}):
                with self.subTest(fields=fields):
                    Item.objects.filter(pk=self.item.pk).update(**fields)
                    before = self.rows()
                    with self.assertRaises(rewards.DemoRewardConfigurationError):
                        self.apply(token)
                    self.assertEqual(self.rows(), before)
                    Item.objects.filter(pk=self.item.pk).update(code=rules.ITEM_MAPPING.item_code,
                        category=Item.HINT, is_active=True, consumable=True)
            level = ItemLevel.objects.create(item=self.item, level=1)
            with self.assertRaises(rewards.DemoRewardConfigurationError):
                self.apply(token)
            level.delete()
            self.progress.refresh_from_db()
            self.assertIsNone(self.progress.synthetic_user_id)

        def test_mapping_and_exclusive_proposal(self):
            token = self.token()
            for changes in ({"mapping_version": "bad"}, {"quantity": 2}, {"quantity": True}, {"item_level": 1}):
                with self.subTest(changes=changes), patch.object(rules, "ITEM_MAPPING", replace(rules.ITEM_MAPPING, **changes)):
                    before = self.rows()
                    with self.assertRaises(rewards.DemoRewardConfigurationError):
                        self.apply(token)
                    self.assertEqual(self.rows(), before)
            for effects in ((), (ProposedEffect("ITEM", 2),), (ProposedEffect("XP", 700),),
                    (ProposedEffect("DUCKYCOINS", 5),), (ProposedEffect("ITEM", 1), ProposedEffect("XP", 1))):
                decision = RewardDecision("demo-rewards-rules-v3", "demo-item-challenge-hint-v3", True,
                    effects, () if effects else ("MATCHED_NO_EFFECT",))
                with self.subTest(effects=effects), patch.object(rewards, "evaluate_reward", return_value=decision):
                    before = self.rows()
                    with self.assertRaises(rewards.DemoRewardConfigurationError):
                        self.apply(token)
                    self.assertEqual(self.rows(), before)

        def test_overflow_and_inconsistent_inventory(self):
            original = self.apply(self.token())
            inventory = InventoryItem.objects.get(ducky_id=original.item.ducky_id, item=self.item)
            maximum = db.ops.integer_field_range("PositiveIntegerField")[1]
            InventoryItem.objects.filter(pk=inventory.pk).update(quantity=maximum)
            before = self.rows()
            with self.assertRaises(services.DemoIntegrityError):
                self.apply(self.token())
            self.assertEqual(self.rows(), before)
            InventoryItem.objects.filter(pk=inventory.pk).update(quantity=maximum - 1)
            self.apply(self.token())
            self.assertEqual(InventoryItem.objects.get(pk=inventory.pk).quantity, maximum)
            InventoryItem.objects.filter(pk=inventory.pk).update(quantity=1)
            level = ItemLevel.objects.create(item=self.item, level=1)
            InventoryItem.objects.filter(pk=inventory.pk).update(item_level=level)
            before = self.rows()
            with self.assertRaises((services.DemoIntegrityError, rewards.DemoRewardConfigurationError)):
                self.apply(self.token())
            self.assertEqual(self.rows(), before)
            InventoryItem.objects.filter(pk=inventory.pk).update(item_level=None)
            level.delete()

        def test_signed_identity_and_session_validation(self):
            token = self.token()
            payload = signing.loads(token, salt=rewards.SALT)
            for change in ({"fact_version": "demo-fact-v2"}, {"mapping_version": "future"},
                    {"item_code": "other"}, {"occurred_at": "not-an-instant"}, {"quantity": 1}):
                altered = signing.dumps({**payload, **change}, salt=rewards.SALT)
                with self.subTest(change=change), self.assertRaises((services.DemoInputError, services.DemoAccessError)):
                    self.apply(altered)
            with self.assertRaises(services.DemoAccessError):
                rewards.apply_demo_reward(self.progress, activity="item_challenge", fact_token=token, session_token="f" * 64)
            other = services.create_demo_progress(session_token=secret)
            with self.assertRaises(services.DemoAccessError):
                self.apply(token, progress=other)
            with self.assertRaises(services.DemoAccessError):
                self.apply(token, "coin_challenge")
            for invalid in (token + "x", "forged", services.issue_demo_operation(self.progress, session_token=secret)):
                with self.subTest(invalid=invalid), self.assertRaises(services.DemoAccessError):
                    self.apply(invalid)
            original = self.apply(token)
            payload["occurred_at"] = (original.occurred_at + timedelta(seconds=1)).isoformat(timespec="microseconds")
            changed = signing.dumps(payload, salt=rewards.SALT)
            before = self.rows()
            with self.assertRaises(services.DemoConflictError):
                self.apply(changed)
            self.assertEqual(self.rows(), before)

        def test_strict_snapshot_corruption(self):
            original = self.apply(self.token())
            row = DemoTargetRewardEvent.objects.get(pk=original.event_id)
            pristine = deepcopy(row.snapshot)
            variants = []
            for key, value in (("quantity", True), ("item_id", True), ("user_id", 1.0),
                    ("mapping_version", "future"), ("reference_id", "wrong"), ("category", "ATTACK"),
                    ("item_level_id", 1), ("consumable", 1), ("created_at", "bad")):
                changed = deepcopy(pristine)
                changed["item"][key] = value
                variants.append(changed)
            changed = deepcopy(pristine)
            del changed["item"]["quantity"]
            variants.append(changed)
            changed = deepcopy(pristine)
            changed["item"]["extra"] = 1
            variants.append(changed)
            for key, value in (("coin_amount", 5), ("schema", "unknown"), ("xp_amount", 1), ("extra", True)):
                variants.append({**deepcopy(pristine), key: value})
            for changed in variants:
                with self.subTest(snapshot=changed):
                    DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=changed)
                    before = self.rows()
                    with self.assertRaises(services.DemoIntegrityError):
                        rewards.read_demo_rewards(self.progress, session_token=secret)
                    self.assertEqual(self.rows(), before)
            DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=pristine)
            # Missing physical cause is not inferred from the JSON or inventory.
            with db.constraint_checks_disabled():
                DemoTargetRewardEvent.objects.filter(pk=row.pk).update(item_grant_id=2**62)
                with self.assertRaises(services.DemoIntegrityError):
                    rewards.read_demo_rewards(self.progress, session_token=secret)
                DemoTargetRewardEvent.objects.filter(pk=row.pk).update(item_grant_id=original.item.item_grant_id)

        def test_real_cause_corruption_and_foreign_key(self):
            original = self.apply(self.token())
            grant = ItemGrant.objects.get(pk=original.item.item_grant_id)
            other_user, _, other_ducky = provision()
            other_item = Item.objects.create(code="fixture-foreign-" + uuid4().hex, name="Foreign", category=Item.HINT, consumable=True)
            variant = ItemLevel.objects.create(item=self.item, level=1)
            for changes in ({"quantity": 2}, {"operation_key": "ri1:wrong"}, {"reference_id": "wrong"},
                    {"reference_type": "wrong"}, {"ducky_id": other_ducky.pk}, {"item_id": other_item.pk},
                    {"item_level_id": variant.pk}, {"created_at": grant.created_at + timedelta(seconds=1)}):
                previous = {key: getattr(grant, key) for key in changes}
                with self.subTest(changes=changes):
                    ItemGrant.objects.filter(pk=grant.pk).update(**changes)
                    before = self.rows()
                    with self.assertRaises(services.DemoIntegrityError):
                        rewards.read_demo_rewards(self.progress, session_token=secret)
                    self.assertEqual(self.rows(), before)
                    ItemGrant.objects.filter(pk=grant.pk).update(**previous)
            variant.delete()
            user = User.objects.get(pk=original.item.user_id)
            User.objects.filter(pk=user.pk).update(is_active=True)
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            User.objects.filter(pk=user.pk).update(is_active=False)
            ducky = Ducky.objects.get(pk=original.item.ducky_id)
            Ducky.objects.filter(pk=ducky.pk).update(sex="bad")
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            Ducky.objects.filter(pk=ducky.pk).update(sex=ducky.sex)
            spare = User(username="fixture-spare-" + uuid4().hex, is_active=False)
            spare.set_unusable_password()
            spare.save()
            Ducky.objects.filter(pk=ducky.pk).update(user=spare)
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            Ducky.objects.filter(pk=ducky.pk).update(user=user)
            Wallet.objects.filter(user=user).delete()
            before = self.rows()
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            self.assertEqual(self.rows(), before)
            Wallet.objects.create(user=user)
            with self.assertRaises(IntegrityError), transaction.atomic():
                DemoTargetRewardEvent.objects.filter(pk=original.event_id).update(coin_amount=5)
            self.assertFalse(db.in_atomic_block)

        def test_orphan_and_crossed_namespace(self):
            token = self.token()
            fact = rewards._fact(token, self.progress, services._owner(secret), "item_challenge")
            user, _, ducky = provision()
            orphan = grant_item(user, self.item, 1, rewards._item_key(fact.identity),
                reference_type="demo_reward_item_v1", reference_id=rewards._item_key(fact.identity))
            before = self.rows()
            with self.assertRaises(services.DemoIntegrityError):
                self.apply(token)
            self.assertEqual(self.rows(), before)
            ItemGrant.objects.filter(pk=orphan.pk).update(operation_key="foreign-non-rewards")
            original = self.apply(token)
            duplicate = grant_item(user, self.item, 1, original.item.operation_key,
                reference_type="demo_reward_item_v1", reference_id=original.item.operation_key)
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            ItemGrant.objects.filter(pk=duplicate.pk).update(operation_key="foreign-other")
            self.replay(token, original)
            owner = User.objects.get(pk=original.item.user_id)
            orphan = grant_item(owner, self.item, 1, "ri1:" + "f" * 64,
                reference_type="demo_reward_item_v1", reference_id="ri1:" + "f" * 64)
            before = self.rows()
            with self.assertRaises(services.DemoIntegrityError):
                rewards.read_demo_rewards(self.progress, session_token=secret)
            self.assertEqual(self.rows(), before)
            orphan.delete()

        def test_shared_connection_single_commit(self):
            token = self.token()
            native = db.connection
            statements, writes = [], []

            def inspect(execute, sql, params, many, context):
                if sql.startswith(('INSERT INTO "duckies_itemgrant"', 'INSERT INTO "duckies_inventoryitem"', 'UPDATE "duckies_inventoryitem"')):
                    self.assertIs(context["connection"], db)
                    self.assertIs(db.connection, native)
                    self.assertEqual(len(db.atomic_blocks), 2)
                    self.assertTrue(native.in_transaction)
                    writes.append(sql)
                    result = execute(sql, params, many, context)
                    self.assertEqual(observe("SELECT COUNT(*) FROM duckies_itemgrant WHERE operation_key LIKE 'ri1:%'"), [(0,)])
                    return result
                return execute(sql, params, many, context)

            native.set_trace_callback(statements.append)
            try:
                with db.execute_wrapper(inspect):
                    result = self.apply(token)
            finally:
                native.set_trace_callback(None)
            self.assertEqual(statements.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(statements.count("COMMIT"), 1)
            self.assertTrue(any(sql.startswith("SAVEPOINT") for sql in statements))
            self.assertTrue(any(sql.startswith("RELEASE SAVEPOINT") for sql in statements))
            self.assertEqual(len(writes), 2)
            self.assertEqual(observe("SELECT COUNT(*) FROM duckies_itemgrant WHERE id=?", (result.item.item_grant_id,)), [(1,)])
            evidence["observations"].append({"shared_native_connection": True, "single_begin_immediate": True,
                "single_commit": True, "inner_savepoint": True, "uncommitted_grant_invisible": True,
                "transaction_sql": [sql for sql in statements if sql.startswith(
                    ("BEGIN", "SAVEPOINT", "RELEASE", "COMMIT", "ROLLBACK"))]})

        def test_complete_rollback_matrix(self):
            token = self.token()
            from django.db.models.query import QuerySet
            original_create = QuerySet.create

            def fail_reward(query, **kwargs):
                if query.model is DemoTargetRewardEvent:
                    raise RuntimeError("injected reward persistence failure")
                return original_create(query, **kwargs)

            def fail_after(function):
                def wrapped(*args, **kwargs):
                    function(*args, **kwargs)
                    raise RuntimeError("injected after real work")
                return wrapped

            for target, name, replacement in (
                    (rewards, "_ducky", fail_after(rewards._ducky)),
                    (duckies, "grant_item", fail_after(duckies.grant_item)),
                    (QuerySet, "create", fail_reward),
                    (rewards, "_recorded_item", fail_after(rewards._recorded_item))):
                before = self.rows()
                with self.subTest(stage=name), patch.object(target, name, replacement), self.assertRaisesRegex(RuntimeError, "injected"):
                    self.apply(token)
                self.assertEqual(self.rows(), before)
                self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
            real_grant = duckies.grant_item

            def corrupt_real_cause(*args, **kwargs):
                grant = real_grant(*args, **kwargs)
                ItemGrant.objects.filter(pk=grant.pk).update(reference_id="incompatible-cause")
                return grant

            before = self.rows()
            with patch.object(duckies, "grant_item", corrupt_real_cause), self.assertRaises(services.DemoIntegrityError):
                self.apply(token)
            self.assertEqual(self.rows(), before)
            evidence["observations"].append({"rollback_stages": 5, "no_partial_provisioning_or_causes": True})

        def concurrent(self, mode):
            tokens = [self.token(), self.token()]
            if mode != "distinct":
                tokens[1] = tokens[0]
            if mode == "conflict":
                payload = signing.loads(tokens[1], salt=rewards.SALT)
                instant = rewards._instant(payload["occurred_at"]) + timedelta(seconds=1)
                tokens[1] = signing.dumps({**payload, "occurred_at": instant.isoformat(timespec="microseconds")}, salt=rewards.SALT)
            barrier = Barrier(2)

            def worker(index):
                connection = connections["default"]
                try:
                    connection.ensure_connection()
                    native = connection.connection
                    barrier.wait(timeout=10)
                    try:
                        result = self.apply(tokens[index])
                        return "ok", result.replay, id(native)
                    except services.DemoConflictError:
                        return "conflict", False, id(native)
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(worker, index) for index in range(2)]
                results = [future.result(timeout=20) for future in futures]
            self.assertNotEqual(results[0][2], results[1][2])
            self.assertEqual(sorted(r[0] for r in results), ["conflict", "ok"] if mode == "conflict" else ["ok", "ok"])
            count = 2 if mode == "distinct" else 1
            self.assertEqual(DemoTargetRewardEvent.objects.filter(progress=self.progress).count(), count)
            self.progress.refresh_from_db()
            self.assertEqual(ItemGrant.objects.filter(ducky__user_id=self.progress.synthetic_user_id).count(), count)
            self.assertEqual(InventoryItem.objects.get(ducky__user_id=self.progress.synthetic_user_id, item=self.item).quantity, count)
            if mode == "same":
                self.assertEqual(sum(r[1] for r in results), 1)
            evidence["observations"].append({"mode": mode, "independent_native_connections": True,
                "outcomes": [r[0] for r in results], "rewards": count})

        def test_concurrent_same(self):
            self.concurrent("same")

        def test_concurrent_conflict(self):
            self.concurrent("conflict")

        def test_concurrent_distinct(self):
            self.concurrent("distinct")

        def test_concurrent_item_with_bank_and_direct_xp(self):
            for mode in ("bank", "xp", "playable"):
                progress = services.create_demo_progress(session_token=secret)
                if mode == "playable":
                    self.apply(self.token("challenge", progress), "challenge", progress)
                item_token = self.token(progress=progress)
                if mode == "bank":
                    second_token = self.token("coin_challenge", progress)
                elif mode == "playable":
                    second_token = playable.issue_playable_operation(progress, action="configure", session_token=secret)
                else:
                    second_token = services.issue_demo_operation(progress, session_token=secret)
                barrier = Barrier(2)

                def worker(index):
                    connection = connections["default"]
                    try:
                        connection.ensure_connection()
                        native = connection.connection
                        barrier.wait(timeout=10)
                        if index == 0:
                            self.apply(item_token, progress=progress)
                        elif mode == "bank":
                            self.apply(second_token, "coin_challenge", progress)
                        elif mode == "playable":
                            playable.configure_demo_option(progress, option_code="persist-demo-tech-gamer",
                                increments=tuple((code, 0) for code in ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")),
                                operation_token=second_token, session_token=secret)
                        else:
                            services.grant_demo_target_xp(progress, amount=700,
                                operation_token=second_token, session_token=secret)
                        return id(native)
                    finally:
                        connection.close()

                with self.subTest(mode=mode), ThreadPoolExecutor(max_workers=2) as pool:
                    futures = [pool.submit(worker, index) for index in range(2)]
                    natives = [f.result(timeout=20) for f in futures]
                self.assertNotEqual(*natives)
                progress.refresh_from_db()
                self.assertEqual(progress.xp_total, 0 if mode == "bank" else 700)
                self.assertEqual(Wallet.objects.get(user_id=progress.synthetic_user_id).available_balance,
                    5 if mode == "bank" else 0)
                self.assertEqual(InventoryItem.objects.get(ducky__user_id=progress.synthetic_user_id, item=self.item).quantity, 1)
                rewards.read_demo_rewards(progress, session_token=secret)
                if mode == "playable":
                    state, _ = playable.read_demo_playable(progress, session_token=secret)
                    self.assertEqual(state.active_option, "persist-demo-tech-gamer")
                evidence["observations"].append({"mixed_with": mode,
                    "independent_native_connections": True, "causal_history_valid": True})

        def test_timeout_explicit_retry(self):
            token = self.token()
            held, release = Event(), Event()

            def blocker():
                connection = connections["default"]
                try:
                    with services._xp_transaction(self.progress, session_token=secret):
                        held.set()
                        if not release.wait(timeout=15):
                            raise AssertionError("Blocker was not released")
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(blocker)
                self.assertTrue(held.wait(timeout=10))
                started = monotonic()
                try:
                    with self.assertRaises(services.DemoBusyError):
                        self.apply(token)
                    elapsed = monotonic() - started
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                finally:
                    release.set()
                future.result(timeout=10)
            self.assertFalse(DemoTargetRewardEvent.objects.filter(progress=self.progress).exists())
            self.progress.refresh_from_db()
            self.assertIsNone(self.progress.synthetic_user_id)
            original = self.apply(token)
            self.replay(token, original)
            evidence["observations"].append({"real_timeout_seconds": elapsed, "explicit_retry_only": True,
                "no_partial_effects": True})

    class RewardsItemHTTPTests(unittest.TestCase):
        """2D only: actual Client, sessions, CSRF and the unmodified coordinator."""
        url = "/demo/objetivo-persistente/"

        def setUp(self):
            slot, _ = EquipmentSlot.objects.get_or_create(code="http-hint-slot", defaults={"name": "Synthetic HINT slot"})
            self.item, _ = Item.objects.update_or_create(code=rules.ITEM_MAPPING.item_code, defaults={
                "name": "Synthetic HINT", "category": Item.HINT, "consumable": True, "is_active": True, "slot": slot})

        def start(self):
            client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
            self.assertEqual(client.get(self.url).status_code, 200)
            self.assertEqual(self.post(client, {"action": "start"}).status_code, 302)
            self.assertEqual(client.get(self.url).status_code, 200)
            return client

        def post(self, client, data, **kwargs):
            return client.post(self.url, data,
                HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value, **kwargs)

        def fact(self, client, activity="item_challenge"):
            return {"action": "reward", "activity": activity, "fact_token": client.session["reward_tokens"][activity]}

        def progress(self, client):
            return services.DemoTargetProgress.objects.get(pk=client.session["demo_progress"])

        def business(self):
            with db.cursor() as cursor:
                return {table: cursor.execute('SELECT * FROM "' + table + '" ORDER BY rowid').fetchall()
                    for table in db.introspection.table_names(cursor) if table not in ("django_session", "sqlite_sequence")}

        def readonly(self, client):
            before = self.business()
            with CaptureQueriesContext(db) as queries:
                result = rewards.read_demo_inventory(self.progress(client), session_token=client.session["demo_secret"])
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP")) for q in queries))
            self.assertEqual(self.business(), before)
            self.assertFalse(hasattr(result, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                result.quantity = 99
            return result

        def reward(self, client):
            return DemoTargetRewardEvent.objects.get(progress=self.progress(client), activity_type="item_challenge")

        def test_http_real_grant_and_distinct_present_inventory(self):
            client = self.start()
            data = self.fact(client)
            page = client.get(self.url).content.decode()
            self.assertIn('value="item_challenge"', page)
            self.assertIn(data["fact_token"], page)
            before = {model: model.objects.count() for model in (Transaction, DemoTargetXPEvent, DemoTargetEvolutionEvent)}
            response = self.post(client, data)
            self.assertEqual((response.status_code, response["Location"]), (302, self.url))
            row = self.reward(client)
            self.assertEqual((row.status, row.xp_amount, row.coin_amount, row.snapshot["schema"]),
                ("APPLIED", 0, 0, "demo-reward-result-v3"))
            self.assertIsNotNone(row.item_grant_id)
            self.assertEqual(InventoryItem.objects.get(ducky__user=self.progress(client).synthetic_user, item=self.item).quantity, 1)
            page = client.get(self.url).content.decode()
            for text in ("APPLIED: HINT sintético entregado y registrado.", "Cantidad histórica entregada: 1",
                    f"ItemGrant #{row.item_grant_id}", 'id="hint-quantity">1</strong>', "demo-item-challenge-hint-v3"):
                self.assertIn(text, page)
            self.assertNotIn("APPLIED: +0 XP", page)
            self.assertEqual({m: m.objects.count() for m in before}, before)
            self.assertEqual(Wallet.objects.get(user=self.progress(client).synthetic_user).available_balance, 0)
            evidence["observations"].append({"http_prg": 302, "real_item_grant": True,
                "historical_quantity": 1, "present_quantity": 1, "no_xp_or_bank_credit": True})

        def test_get_and_tokens_never_provision(self):
            client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
            before = self.business()
            self.assertEqual(client.get(self.url).status_code, 200)
            self.assertEqual(self.business(), before)
            client = self.start()
            before = self.business()
            self.assertEqual(client.get(self.url).status_code, 200)
            self.assertEqual(client.get(self.url).status_code, 200)
            self.assertEqual(self.business(), before)
            self.assertIsNone(self.progress(client).synthetic_user_id)

        def test_replay_original_last_and_row_forms(self):
            client = self.start()
            original = self.fact(client)
            self.assertEqual(self.post(client, original).status_code, 302)
            row = self.reward(client)
            snapshot = deepcopy(row.snapshot)
            self.assertEqual(client.get(self.url).status_code, 200)

            class Forms(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.forms, self.current, self.ids = [], None, []
                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if tag == "form":
                        self.current, self.ids = {}, []
                    if tag == "input" and self.current is not None and "name" in attrs:
                        self.current[attrs["name"]] = attrs.get("value", "")
                        self.ids.append(attrs.get("id", ""))
                def handle_endtag(self, tag):
                    if tag == "form" and self.current is not None:
                        self.forms.append((self.current, tuple(self.ids)))
                        self.current = None

            parser = Forms()
            parser.feed(client.get(self.url).content.decode())
            replays = [values for values, ids in parser.forms if any(
                identity in ids for identity in ("reward_replay_fact_token", f"reward_history_{row.pk}_fact_token"))]
            self.assertEqual(len(replays), 2)
            for payload in (original, *replays):
                before = self.business()
                self.assertEqual(self.post(client, payload).status_code, 302)
                self.assertEqual(self.business(), before)
                page = client.get(self.url).content.decode()
                self.assertIn("Replay Rewards histórico: sin nuevas concesiones", page)
                self.assertNotIn("APPLIED: HINT sintético entregado", page)
            row.refresh_from_db()
            self.assertEqual(row.snapshot, snapshot)
            self.assertEqual(ItemGrant.objects.filter(pk=row.item_grant_id).count(), 1)

        def test_consumed_inventory_zero_and_http_replay(self):
            client = self.start()
            data = self.fact(client)
            self.assertEqual(self.post(client, data).status_code, 302)
            row = self.reward(client)
            user = self.progress(client).synthetic_user
            duckies.equip_item(user, self.item)
            duckies.consume_item(user, self.item, 1, "http-consume-" + uuid4().hex,
                server_accepted=True, game_reference="http-fixture-game")
            self.assertFalse(InventoryItem.objects.filter(ducky__user=user, item=self.item).exists())
            Item.objects.filter(pk=self.item.pk).update(is_active=False)
            before = self.business()
            page = client.get(self.url).content.decode()
            self.assertIn('id="hint-quantity">0</strong>', page)
            self.assertIn("Cantidad histórica entregada: 1", page)
            self.assertIn("Repetir último hecho Rewards", page)
            self.assertIn(f"Repetir hecho #{row.pk}", page)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertEqual(self.business(), before)
            self.assertTrue(ItemGrant.objects.filter(pk=row.item_grant_id).exists())
            evidence["observations"].append({"real_http_grant_equip_consume": True,
                "inventory_exhausted": True, "http_replay_without_delivery": True})

        def test_inventory_readonly_all_states(self):
            client = self.start()
            state = self.readonly(client)
            self.assertEqual(asdict(state), dict(item_prepared=True, user_provisioned=False, ducky_provisioned=False, quantity=None))
            Item.objects.filter(pk=self.item.pk).update(code="unprepared-" + uuid4().hex)
            self.assertFalse(self.readonly(client).item_prepared)
            Item.objects.filter(pk=self.item.pk).update(code=rules.ITEM_MAPPING.item_code)
            self.assertEqual(self.post(client, self.fact(client, "coin_challenge")).status_code, 302)
            self.assertEqual(client.get(self.url).status_code, 200)
            state = self.readonly(client)
            self.assertTrue(state.user_provisioned)
            self.assertFalse(state.ducky_provisioned)
            user = self.progress(client).synthetic_user
            Ducky.objects.create(user=user, sex=Ducky.SEX[0][0], selected_outfit=None)
            Item.objects.filter(pk=self.item.pk).update(code="unprepared-with-ducky-" + uuid4().hex)
            state = self.readonly(client)
            self.assertEqual(asdict(state), dict(item_prepared=False, user_provisioned=True,
                ducky_provisioned=True, quantity=None))
            Item.objects.filter(pk=self.item.pk).update(code=rules.ITEM_MAPPING.item_code)
            self.assertEqual(self.readonly(client).quantity, 0)
            self.assertEqual(self.post(client, self.fact(client)).status_code, 302)
            self.assertEqual(self.readonly(client).quantity, 1)
            with self.assertRaises(services.DemoAccessError):
                rewards.read_demo_inventory(self.progress(client), session_token="f" * 64)
            row = self.reward(client)
            corrupt = deepcopy(row.snapshot)
            corrupt["item"]["quantity"] = True
            DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=corrupt)
            before = self.business()
            with self.assertRaises(services.DemoIntegrityError):
                self.readonly(client)
            self.assertEqual(self.business(), before)
            evidence["observations"].append({"readonly_states": 5, "no_dml": True,
                "historical_corruption_not_empty_inventory": True})

        def test_sessions_reset_and_private_history(self):
            a, b = self.start(), self.start()
            first = self.fact(a)
            self.assertEqual(self.post(a, first).status_code, 302)
            ra = self.reward(a)
            self.assertEqual(self.post(b, first).status_code, 403)
            self.assertEqual(self.post(b, self.fact(b)).status_code, 302)
            rb = self.reward(b)
            self.assertNotIn(f"ItemGrant #{ra.item_grant_id}", b.get(self.url).content.decode())
            self.assertNotIn(f"ItemGrant #{rb.item_grant_id}", a.get(self.url).content.decode())
            own_pk = a.session["demo_progress"]
            session = a.session
            session["demo_progress"] = b.session["demo_progress"]
            session.save()
            before = self.business()
            self.assertEqual(a.get(self.url).status_code, 403)
            self.assertEqual(self.business(), before)
            session = a.session
            session["demo_progress"] = own_pk
            session.save()
            self.assertEqual(self.post(a, {"action": "start"}).status_code, 302)
            self.assertEqual(a.get(self.url).status_code, 200)
            self.assertNotIn("ItemGrant #", a.get(self.url).content.decode())
            self.assertEqual(self.post(a, first).status_code, 403)
            self.assertTrue(DemoTargetRewardEvent.objects.filter(pk=ra.pk).exists())
            self.assertNotIn(str(ra.pk), a.session.get("reward_confirmed_tokens", {}))
            self.assertNotIn("reward_last", a.session)

        def test_csrf_and_methods(self):
            client = self.start()
            data = self.fact(client)
            before = self.business()
            self.assertEqual(client.post(self.url, data).status_code, 403)
            self.assertEqual(client.post(self.url, data, HTTP_X_CSRFTOKEN="x" * 64).status_code, 403)
            self.assertEqual(self.business(), before)
            self.assertEqual(self.post(client, data).status_code, 302)
            for method in ("put", "patch", "delete", "head", "options", "trace"):
                self.assertEqual(getattr(client, method)(self.url,
                    HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value).status_code, 405)

        def test_strict_fields_tokens_get_and_escape(self):
            client = self.start()
            data = self.fact(client)
            before = self.business()
            for key in ("item_id", "user_id", "ducky_id", "quantity", "item_level_id", "wallet_id",
                    "balance", "transaction_id", "progress", "fact_id"):
                with self.subTest(extra=key):
                    self.assertEqual(self.post(client, {**data, key: "1"}).status_code, 400)
                    self.assertEqual(client.get(self.url, {key: "1"}).status_code, 400)
            for key in data:
                self.assertEqual(self.post(client, {k: v for k, v in data.items() if k != key}).status_code, 400)
                self.assertEqual(self.post(client, urlencode([*data.items(), (key, data[key])]),
                    content_type="application/x-www-form-urlencoded").status_code, 400)
            for token in ("forged", data["fact_token"] + "x", client.session["reward_tokens"]["challenge"],
                    client.session["demo_operation"]):
                self.assertEqual(self.post(client, {**data, "fact_token": token}).status_code, 403)
            response = self.post(client, {**data, "activity": "<script>private</script>"})
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("<script>private</script>", response.content.decode())
            self.assertIn("&lt;script&gt;private&lt;/script&gt;", response.content.decode())
            self.assertEqual(self.business(), before)

        def test_conflict_and_no_stale_success(self):
            client = self.start()
            data = self.fact(client)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertEqual(client.get(self.url).status_code, 200)
            payload = signing.loads(data["fact_token"], salt=rewards.SALT)
            payload["occurred_at"] = (rewards._instant(payload["occurred_at"]) + timedelta(seconds=1)).isoformat(timespec="microseconds")
            changed = {**data, "fact_token": signing.dumps(payload, salt=rewards.SALT)}
            before = self.business()
            response = self.post(client, changed)
            self.assertEqual(response.status_code, 409)
            self.assertNotIn("APPLIED:", response.content.decode())
            self.assertEqual(self.business(), before)
            self.assertNotIn("APPLIED: HINT", client.get(self.url).content.decode())

        def test_item_unavailable_and_invalid_configuration(self):
            client = self.start()
            data = self.fact(client)
            for fields in ({"code": "absent-" + uuid4().hex}, {"is_active": False}, {"category": Item.COSMETIC}):
                with self.subTest(fields=fields):
                    Item.objects.filter(pk=self.item.pk).update(**fields)
                    before = self.business()
                    response = self.post(client, data)
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(self.business(), before)
                    self.assertNotIn("APPLIED:", response.content.decode())
                    self.assertNotIn(str(path), response.content.decode())
                    Item.objects.filter(pk=self.item.pk).update(code=rules.ITEM_MAPPING.item_code, is_active=True, category=Item.HINT)
            self.assertIsNone(self.progress(client).synthetic_user_id)

        def test_history_identity_and_cause_errors(self):
            client = self.start()
            self.assertEqual(self.post(client, self.fact(client)).status_code, 302)
            row = self.reward(client)
            grant = ItemGrant.objects.get(pk=row.item_grant_id)
            for changes in ({"reference_id": "private-incompatible"}, {"quantity": 2}, {"operation_key": "ri1:private-incompatible"}):
                previous = {key: getattr(grant, key) for key in changes}
                ItemGrant.objects.filter(pk=grant.pk).update(**changes)
                before = self.business()
                response = client.get(self.url)
                self.assertEqual(response.status_code, 409)
                self.assertEqual(self.business(), before)
                self.assertNotIn("private-incompatible", response.content.decode())
                self.assertNotIn("APPLIED:", response.content.decode())
                ItemGrant.objects.filter(pk=grant.pk).update(**previous)
            user = self.progress(client).synthetic_user
            User.objects.filter(pk=user.pk).update(is_active=True)
            self.assertEqual(client.get(self.url).status_code, 409)
            User.objects.filter(pk=user.pk).update(is_active=False)
            ducky = Ducky.objects.get(user=user)
            Ducky.objects.filter(pk=ducky.pk).update(sex="bad")
            self.assertEqual(client.get(self.url).status_code, 409)
            Ducky.objects.filter(pk=ducky.pk).update(sex=ducky.sex)
            snapshot = deepcopy(row.snapshot)
            snapshot["item"]["quantity"] = 99
            DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=snapshot)
            self.assertEqual(client.get(self.url).status_code, 409)

        def test_inventory_sql_error_is_sanitized(self):
            from django.db import OperationalError
            client = self.start()
            self.assertEqual(self.post(client, self.fact(client)).status_code, 302)
            before = self.business()

            def fail_inventory(execute, sql, params, many, context):
                if "duckies_inventoryitem" in sql.lower():
                    raise OperationalError("private-sql-location")
                return execute(sql, params, many, context)

            with db.execute_wrapper(fail_inventory):
                response = client.get(self.url)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(self.business(), before)
            self.assertNotIn("private-sql-location", response.content.decode())
            self.assertNotIn("APPLIED:", response.content.decode())

        def test_real_http_timeout_and_explicit_retry(self):
            client = self.start()
            data = self.fact(client)
            before = self.business()
            held, release = Event(), Event()

            def blocker():
                try:
                    with services._xp_transaction(self.progress(client), session_token=client.session["demo_secret"]):
                        held.set()
                        if not release.wait(15):
                            raise AssertionError("HTTP fixture lock was not released")
                finally:
                    connections["default"].close()

            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(blocker)
                self.assertTrue(held.wait(10))
                started = monotonic()
                try:
                    response = self.post(client, data)
                    elapsed = monotonic() - started
                    self.assertEqual(response.status_code, 503)
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertNotIn("APPLIED:", response.content.decode())
                finally:
                    release.set()
                    future.result(timeout=10)
            self.assertEqual(self.business(), before)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertEqual(InventoryItem.objects.get(ducky__user=self.progress(client).synthetic_user, item=self.item).quantity, 1)
            evidence["observations"].append({"http_timeout": 503, "seconds": elapsed,
                "explicit_retry_without_duplicate": True})

        def test_xp_bank_visit_and_playable_compatibility(self):
            client = self.start()
            original = {a: self.fact(client, a) for a in ("challenge", "coin_challenge", "visit")}
            for payload in original.values():
                self.assertEqual(self.post(client, payload).status_code, 302)
            self.assertEqual(client.get(self.url).status_code, 200)
            progress = self.progress(client)
            self.assertEqual((progress.xp_total, progress.current_level), (700, 8))
            self.assertEqual(DemoTargetEvolutionEvent.objects.filter(progress=progress).count(), 6)
            self.assertEqual(Wallet.objects.get(user=progress.synthetic_user).available_balance, 5)
            revision = None
            for option in ("persist-demo-tech-gamer", "persist-demo-epoch-3"):
                result = playable.configure_demo_option(progress, option_code=option,
                    increments=tuple((code, 0) for code in ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")),
                    operation_token=playable.issue_playable_operation(progress, action="configure", session_token=client.session["demo_secret"]),
                    session_token=client.session["demo_secret"], expected_revision=revision)
                revision = result.after.revision
            before = self.business()
            for payload in original.values():
                self.assertEqual(self.post(client, payload).status_code, 302)
            self.assertEqual(self.business(), before)
            self.assertEqual(self.post(client, self.fact(client)).status_code, 302)
            db.close()
            page = client.get(self.url).content.decode()
            for text in ("+700 XP", "+5 DuckyCoins", "NO_REWARD", "ItemGrant #", "Gamer", "Romano"):
                self.assertIn(text, page)
            self.assertEqual({r.snapshot["schema"] for r in DemoTargetRewardEvent.objects.filter(progress=progress)},
                {"demo-reward-result-v2", "demo-reward-result-v3"})

    groups = {
        "atomicity": ("test_shared_default_savepoint_commit", "test_rollback_existing_inventory",
                      "test_rollback_new_provisioning", "test_inner_failure_rolls_back_savepoint"),
        "idempotency": ("test_duckies_idempotency_and_conflict",),
        "concurrency": ("test_concurrent_compatible", "test_concurrent_incompatible",
                        "test_concurrent_distinct", "test_timeout_and_explicit_recovery"),
        "failure": ("test_injected_child_failure",),
        "service-functional": ("test_real_item_and_exact_key", "test_lazy_and_bank_compatibility",
            "test_real_consumption_then_readonly_replay", "test_reopen_and_future_rules_do_not_reinterpret",
            "test_existing_playable_configuration_is_unchanged"),
        "service-validation": ("test_invalid_item_configuration", "test_mapping_and_exclusive_proposal",
            "test_overflow_and_inconsistent_inventory", "test_signed_identity_and_session_validation"),
        "service-integrity": ("test_strict_snapshot_corruption", "test_real_cause_corruption_and_foreign_key",
            "test_orphan_and_crossed_namespace"),
        "service-atomicity": ("test_shared_connection_single_commit", "test_complete_rollback_matrix"),
        "service-concurrency": ("test_concurrent_same", "test_concurrent_conflict", "test_concurrent_distinct",
            "test_concurrent_item_with_bank_and_direct_xp", "test_timeout_explicit_retry"),
        "http-functional": ("test_http_real_grant_and_distinct_present_inventory", "test_get_and_tokens_never_provision"),
        "http-replay": ("test_replay_original_last_and_row_forms",),
        "http-consumption": ("test_consumed_inventory_zero_and_http_replay", "test_inventory_readonly_all_states"),
        "http-sessions": ("test_sessions_reset_and_private_history",),
        "http-security": ("test_csrf_and_methods", "test_strict_fields_tokens_get_and_escape", "test_conflict_and_no_stale_success"),
        "http-errors": ("test_item_unavailable_and_invalid_configuration", "test_history_identity_and_cause_errors", "test_inventory_sql_error_is_sanitized", "test_real_http_timeout_and_explicit_retry"),
        "http-compatibility": ("test_xp_bank_visit_and_playable_compatibility",),
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
        case = (RewardsItemHTTPTests if scenario.startswith("http-") else
                RewardsItemServiceTests if scenario.startswith("service-") else RewardsDuckiesTests)
        suite = unittest.TestSuite(case(name) for name in groups[scenario])
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        evidence.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                        skipped=len(result.skipped), success=result.wasSuccessful())
        if scenario == "service-functional" and result.wasSuccessful():
            call_command("check", databases=["default"], stdout=StringIO())
            call_command("makemigrations", check=True, dry_run=True, verbosity=0, stdout=StringIO())
            evidence["checks_and_no_model_changes"] = True
    finally:
        connections.close_all()
    evidence["connections_closed"] = all(c.connection is None for c in connections.all())
    evidence["only_fixture_connections"] = bool(opened) and all(name in allowed for name in opened)
    print("DUCKIES_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2]))
