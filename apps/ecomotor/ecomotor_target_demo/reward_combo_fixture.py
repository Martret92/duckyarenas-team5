"""Test-only protected default: real combined Rewards V4, no HTTP or personal DB.

Only this owned subprocess prepares the synthetic HINT. All owner APIs and
SQLite commits/rollback/concurrency are real; patches inject faults or observe.
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
            or not root.name.startswith("ducky-rewards-combo-") or not root.is_dir()
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
                raise AssertionError("SQLite connection outside the owned combo fixture")
            opened.append(destination)

    sys.addaudithook(audit)
    from copy import deepcopy
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import ExitStack
    from io import StringIO
    from dataclasses import asdict, replace, FrozenInstanceError
    from hashlib import sha256
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
    from apps.bank.models import Wallet, Transaction
    from apps.bank import services as bank
    from apps.duckies.models import Ducky, Item, ItemLevel, ItemGrant, InventoryItem, EquipmentSlot
    from apps.duckies import services as duckies
    from apps.ecomotor.reward_types import (RewardDecision, ProposedEffect, RewardIdentity,
        RewardRuleSet, RewardRule, InvalidRewardRuleSetError, AmbiguousRewardRulesError)
    from apps.ecomotor.reward_identity import semantic_fingerprint
    from apps.users.models import UserProfileEcomotor
    from . import services, reward_demo_services as rewards, reward_demo_rules as rules, playable_services as playable
    from .isolation import demo_connection, MIGRATING
    from .models import (DemoTargetXPEvent, DemoTargetEvolutionEvent, DemoTargetRewardEvent,
                         DemoTargetOptionConfiguration)

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

    def rows():
        with db.cursor() as cursor:
            return {table: cursor.execute('SELECT * FROM "' + table + '" ORDER BY rowid').fetchall()
                    for table in db.introspection.table_names(cursor)}

    class ComboTests(unittest.TestCase):
        def setUp(self):
            self.progress = services.create_demo_progress(session_token=secret)
            slot, _ = EquipmentSlot.objects.get_or_create(code="combo-hint-slot", defaults={"name": "Synthetic"})
            self.item, _ = Item.objects.get_or_create(code="demo-reward-hint-v1", defaults={
                "name": "Synthetic HINT", "category": Item.HINT, "consumable": True, "is_active": True, "slot": slot})

        def token(self, activity="combo_challenge", progress=None):
            return rewards.issue_reward_fact(progress or self.progress, activity=activity, session_token=secret)

        def apply(self, token, activity="combo_challenge", progress=None, owner=secret):
            return rewards.apply_demo_reward(progress or self.progress, activity=activity,
                fact_token=token, session_token=owner)

        def direct(self, amount):
            return services.grant_demo_target_xp(self.progress, amount=amount,
                operation_token=services.issue_demo_operation(self.progress, session_token=secret), session_token=secret)

        def replay(self, token, original):
            before = rows()
            # Each audited capture owns an empty buffer; long corruption matrices
            # must not silently truncate the writer-free evidence at 9000 queries.
            db.queries_log.clear()
            def no_inventory(execute, sql, params, many, context):
                self.assertNotIn("duckies_inventoryitem", sql.lower())
                return execute(sql, params, many, context)
            with ExitStack() as stack:
                for module, name in ((rewards, "evaluate_reward"), (bank, "credit_coins"),
                    (duckies, "grant_item"), (services, "_grant_xp_in_transaction"),
                    (User.objects, "create")):
                    stack.enter_context(patch.object(module, name, side_effect=AssertionError("Replay writer/evaluation")))
                stack.enter_context(db.execute_wrapper(no_inventory))
                queries = stack.enter_context(CaptureQueriesContext(db))
                result = self.apply(token)
                history = rewards.read_demo_rewards(self.progress, session_token=secret)
            self.assertTrue(result.replay)
            self.assertEqual(asdict(replace(result, replay=False)), asdict(original))
            self.assertIn(original, history)
            self.assertFalse(any(q["sql"].lstrip().upper().startswith(
                ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")) for q in queries))
            self.assertEqual(rows(), before)
            return result

        def test_primary_and_exact_three_keys(self):
            token = self.token()
            before = rows()
            result = self.apply(token)
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            self.assertFalse(user.is_active or user.is_staff or user.is_superuser or user.has_usable_password())
            self.assertFalse(UserProfileEcomotor.objects.filter(user=user).exists())
            self.assertEqual((self.progress.xp_total, self.progress.current_level, self.progress.current_epoch.ordinal), (700, 8, 7))
            self.assertEqual((result.xp_amount, result.coin_amount, result.item.quantity), (700, 5, 1))
            row = DemoTargetRewardEvent.objects.get(pk=result.event_id)
            self.assertEqual(DemoTargetRewardEvent.objects.filter(progress=self.progress).count(), 1)
            xp_event = DemoTargetXPEvent.objects.get(pk=row.xp_event_id)
            entry = Transaction.objects.get(pk=row.bank_transaction_id)
            grant = ItemGrant.objects.get(pk=row.item_grant_id)
            self.assertEqual(len(result.evolution_ids), 6)
            self.assertEqual(list(DemoTargetEvolutionEvent.objects.filter(xp_event=xp_event)
                .order_by("ordinal").values_list("ordinal", flat=True)), [2, 3, 4, 5, 6, 7])
            self.assertEqual(Wallet.objects.get(user=user).available_balance, 5)
            self.assertEqual(InventoryItem.objects.get(ducky__user=user, item=self.item).quantity, 1)
            identity = result.identity
            for prefix, label, ascii_, size, actual in (
                    ("rx1:", "xp", True, 28, xp_event.operation_key),
                    ("rb1:", "bank", True, 64, entry.operation_key),
                    ("ri1:", "item", False, 64, grant.operation_key)):
                array = [f"demo-reward-{label}-key-v1", identity.origin_code, identity.fact_id, identity.recipient_id]
                encoded = json.dumps(array, separators=(",", ":"), sort_keys=True,
                    ensure_ascii=ascii_, allow_nan=False).encode("utf-8")
                self.assertEqual(actual, prefix + sha256(encoded).hexdigest()[:size])
            self.assertEqual((entry.reference_type, entry.reference_id, entry.source_platform, entry.issuing_entity),
                ("demo_reward_fact_v1", entry.operation_key, "persist-demo-rewards", "EcomotorDemo"))
            self.assertEqual((grant.reference_type, grant.reference_id, grant.quantity, grant.item_level_id),
                ("demo_reward_item_v1", grant.operation_key, 1, None))
            self.assertEqual(row.snapshot["schema"], "demo-reward-result-v4")
            self.assertEqual(row.snapshot["anchor_xp_event_id"], xp_event.pk)
            self.assertEqual(row.snapshot["bank"], asdict(result.bank))
            self.assertEqual(row.snapshot["item"], asdict(result.item))
            self.assertEqual(set(row.snapshot), {"schema", "identity", "activity_type", "occurred_at",
                "fingerprint_version", "fingerprint", "status", "rule_set_version", "matched_rule_id", "eligible",
                "effects", "reason_codes", "xp_amount", "xp_event_id", "evolution_ids", "catalog",
                "anchor_xp_event_id", "progression", "coin_amount", "bank", "item"})
            self.assertEqual(row.snapshot["effects"], [["XP", 700], ["DUCKYCOINS", 5], ["ITEM", 1]])
            with self.assertRaises(FrozenInstanceError): result.xp_amount = 0
            with self.assertRaises(FrozenInstanceError): result.item.quantity = 0
            self.replay(token, result)
            evidence["observations"].append({"reward_events": 1, "causes": 3, "xp": 700,
                "coins": 5, "hint": 1, "evolutions": 6, "exact_keys": True, "snapshot_v4": True})

        def test_existing_state_and_old_modalities(self):
            self.direct(100)
            for activity in ("challenge", "coin_challenge", "item_challenge", "visit"):
                self.apply(self.token(activity), activity)
            increments = tuple((c, 10 if i == 0 else 0) for i, c in
                enumerate(("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")))
            playable.configure_demo_option(self.progress, option_code="persist-demo-tech-gamer", increments=increments,
                operation_token=playable.issue_playable_operation(self.progress, action="configure", session_token=secret),
                session_token=secret)
            configs = list(DemoTargetOptionConfiguration.objects.values())
            prior = list(DemoTargetRewardEvent.objects.filter(progress=self.progress).values())
            self.progress.refresh_from_db()
            user_id = self.progress.synthetic_user_id
            ducky_id = Ducky.objects.get(user_id=user_id).pk
            result = self.apply(self.token())
            self.progress.refresh_from_db()
            self.assertEqual(self.progress.xp_total, 1500)
            self.assertEqual(result.evolution_ids, ())
            self.assertEqual((result.bank.balance_before, result.bank.balance_after), (5, 10))
            self.assertEqual((result.item.user_id, result.item.ducky_id), (user_id, ducky_id))
            self.assertEqual(InventoryItem.objects.get(ducky_id=ducky_id, item=self.item).quantity, 2)
            self.assertEqual(list(DemoTargetOptionConfiguration.objects.values()), configs)
            self.assertEqual(list(DemoTargetRewardEvent.objects.filter(pk__in=[r["id"] for r in prior]).values()), prior)

        def test_history_v1_v2_v3_v4_and_changed_present(self):
            original_snapshot = rewards._snapshot
            def v1(*args, **kwargs):
                return original_snapshot(*args, **{**kwargs, "schema": rewards.V1_SNAPSHOT_VERSION})
            with patch.object(rewards, "_snapshot", side_effect=v1), patch.object(rules, "RULE_SET",
                RewardRuleSet("demo-rewards-rules-v1", (RewardRule("demo-challenge-700-v1", "challenge",
                    {"completed": True}, (ProposedEffect("XP", 700),)),))):
                self.apply(self.token("challenge"), "challenge")
                self.apply(self.token("visit"), "visit")
            self.apply(self.token("coin_challenge"), "coin_challenge")
            item_token = self.token("item_challenge")
            self.apply(item_token, "item_challenge")
            token = self.token()
            original = self.apply(token)
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            self.direct(100)
            bank.debit_coins(user, 10, source="combo-fixture", operation_key="spend-" + uuid4().hex)
            duckies.equip_item(user, self.item)
            duckies.consume_item(user, self.item, 2, "consume-" + uuid4().hex,
                server_accepted=True, game_reference="synthetic-combo-game")
            self.assertFalse(InventoryItem.objects.filter(ducky__user=user, item=self.item).exists())
            Item.objects.filter(pk=self.item.pk).update(is_active=False)
            try:
                with patch.object(rules, "COMBO_RULE_SET", RewardRuleSet("future-unused", ())):
                    self.replay(token, original)
                    db.close()
                    self.replay(token, original)
                self.assertEqual({r.snapshot["schema"] for r in DemoTargetRewardEvent.objects.filter(progress=self.progress)},
                    {"demo-reward-result-v1", "demo-reward-result-v2", "demo-reward-result-v3", "demo-reward-result-v4"})
                self.assertEqual(Wallet.objects.get(user=user).available_balance, 0)
                self.assertEqual(original.bank.balance_after, 10)
                self.assertTrue(ItemGrant.objects.filter(pk=original.item.item_grant_id).exists())
            finally:
                Item.objects.filter(pk=self.item.pk).update(is_active=True)
            evidence["observations"].append({"replay_after_spend_consume_xp_rules_reopen": True,
                "readonly_without_inventory_query": True, "v1_v2_v3_v4_coexist": True})

        def test_closed_token_and_semantics(self):
            before = rows()
            token = self.token()
            self.assertEqual(rows(), before)
            payload = signing.loads(token, salt=rewards.SALT)
            self.assertEqual(set(payload), {"progress", "owner", "activity", "fact_id", "fact_version", "occurred_at", "mapping_version", "item_code"})
            fact = rewards._fact(token, self.progress, services._owner(secret), "combo_challenge")
            self.assertEqual(dict(fact.result), {"completed": True})
            self.assertEqual(dict(fact.context), {"demo": "REW-MULTI-03", "fact_version": "demo-fact-v4",
                "mapping_version": "demo-item-map-v1", "item_code": "demo-reward-hint-v1"})
            self.assertEqual(rewards.SALT, "ecomotor.persistent-demo.reward-fact.v1")
            from .forms import REWARD_HTTP_ACTIVITIES
            self.assertIn("combo_challenge", dict(REWARD_HTTP_ACTIVITIES))
            variations = [dict(payload, **{key: value}) for key, value in (
                ("progress", True), ("progress", self.progress.pk + 999), ("owner", "ñ" * 64),
                ("owner", "0" * 64), ("activity", "challenge"), ("fact_id", "A" * 32),
                ("fact_id", "x"), ("fact_id", 2), ("fact_version", "demo-fact-v3"),
                ("mapping_version", "other"), ("item_code", "other"), ("occurred_at", True),
                ("occurred_at", payload["occurred_at"].replace("+00:00", "Z")),
                ("occurred_at", "2026-10-24T00:00:00+00:00"),
                ("occurred_at", "2026-10-24T00:00:00.000000"),
                ("occurred_at", "2026-99-24T00:00:00.000000+00:00"))]
            for key in payload:
                variations.append({k: v for k, v in payload.items() if k != key})
            for key in ("result", "context", "user_id", "wallet_id", "ducky_id", "item_id", "quantity", "balance", "xp"):
                variations.append(dict(payload, **{key: 1}))
            tokens = [signing.dumps(v, salt=rewards.SALT) for v in variations]
            tokens += [token + "x", signing.dumps(payload, salt="other-purpose")]
            class DuplicateSerializer(signing.JSONSerializer):
                def dumps(self, obj):
                    raw = super().dumps(obj)
                    return b'{"progress":' + str(obj["progress"]).encode() + b',' + raw[1:]
            tokens.append(signing.dumps(payload, salt=rewards.SALT, serializer=DuplicateSerializer))
            for invalid in tokens:
                with self.subTest(token_case=tokens.index(invalid)), self.assertRaises((services.DemoInputError, services.DemoAccessError)):
                    self.apply(invalid)
                self.assertEqual(rows(), before)
            with self.assertRaises(services.DemoAccessError):
                self.apply(token, owner="f" * 64)
            other = services.create_demo_progress(session_token=secret)
            with self.assertRaises(services.DemoAccessError):
                self.apply(token, progress=other)
            evidence["observations"].append({"closed_token_variations": len(tokens), "duplicate_fields_rejected": True})

        def test_invalid_complete_proposals(self):
            token = self.token()
            valid = (ProposedEffect("XP", 700), ProposedEffect("DUCKYCOINS", 5), ProposedEffect("ITEM", 1))
            proposals = [valid[:2], valid + (ProposedEffect("XP", 1),), (valid[0], valid[0], valid[2]),
                tuple(reversed(valid)), (ProposedEffect("XP", 701), *valid[1:]),
                (valid[0], ProposedEffect("DUCKYCOINS", 6), valid[2]),
                (*valid[:2], ProposedEffect("ITEM", 2)), (valid[0], valid[1], ProposedEffect("UNKNOWN", 1))]
            decisions = [RewardDecision("demo-rewards-rules-v4", "demo-combo-challenge-v4", True, v, ()) for v in proposals]
            decisions += [RewardDecision("wrong", "demo-combo-challenge-v4", True, valid, ()),
                RewardDecision("demo-rewards-rules-v4", "wrong", True, valid, ()),
                RewardDecision("demo-rewards-rules-v4", None, False, (), ("NO_MATCHING_RULE",))]
            before = rows()
            for decision in decisions:
                with self.subTest(decision=repr(decision)), patch.object(rewards, "evaluate_reward", return_value=decision), \
                        self.assertRaises(rewards.DemoRewardConfigurationError):
                    self.apply(token)
                self.assertEqual(rows(), before)
            ambiguous = RewardRuleSet("demo-rewards-rules-v4", (
                RewardRule("one", "combo_challenge", {}, valid), RewardRule("two", "combo_challenge", {}, valid)))
            with patch.object(rules, "COMBO_RULE_SET", ambiguous), self.assertRaises(AmbiguousRewardRulesError):
                self.apply(token)
            self.assertEqual(rows(), before)
            evidence["observations"].append({"invalid_proposals": len(decisions) + 1, "zero_partial_writes": True})

        def test_invalid_resources_and_boundaries(self):
            token = self.token()
            for changes in ({"is_active": False}, {"category": Item.ATTACK}, {"consumable": False}, {"code": "wrong-code"}):
                original = {key: getattr(self.item, key) for key in changes}
                try:
                    Item.objects.filter(pk=self.item.pk).update(**changes)
                    before = rows()
                    with self.assertRaises(rewards.DemoRewardConfigurationError): self.apply(token)
                    self.assertEqual(rows(), before)
                finally:
                    Item.objects.filter(pk=self.item.pk).update(**original)
            variant = ItemLevel.objects.create(item=self.item, level=1)
            try:
                before = rows()
                with self.assertRaises(rewards.DemoRewardConfigurationError): self.apply(token)
                self.assertEqual(rows(), before)
            finally:
                variant.delete()
            with patch.object(rules, "ITEM_MAPPING", replace(rules.ITEM_MAPPING, mapping_version="unknown")), \
                    self.assertRaises(rewards.DemoRewardConfigurationError):
                self.apply(token)
            prior_item = self.apply(self.token("item_challenge"), "item_challenge")
            inventory = InventoryItem.objects.get(ducky_id=prior_item.item.ducky_id, item=self.item)
            maximum = db.ops.integer_field_range(inventory._meta.get_field("quantity").get_internal_type())[1]
            InventoryItem.objects.filter(pk=inventory.pk).update(quantity=maximum)
            try:
                before = rows()
                with self.assertRaises(services.DemoIntegrityError): self.apply(token)
                self.assertEqual(rows(), before)
            finally:
                InventoryItem.objects.filter(pk=inventory.pk).update(quantity=1)
            # Outer caller blocks are rejected before any effect (not a savepoint workaround).
            with transaction.atomic(), self.assertRaises(services.DemoTransactionError): self.apply(token)
            with patch.object(rewards, "_bank_default", side_effect=services.DemoTransactionError("wrong alias")), \
                    self.assertRaises(services.DemoTransactionError), patch.object(bank, "credit_coins", side_effect=AssertionError):
                self.apply(token)

        def test_strict_snapshot_corruption(self):
            token = self.token()
            original = self.apply(token)
            row = DemoTargetRewardEvent.objects.get(pk=original.event_id)
            base = deepcopy(row.snapshot)
            variants = []
            for key in base:
                variants.append({k: v for k, v in base.items() if k != key})
            variants.append({**base, "extra": 1})
            for section in ("bank", "item", "identity", "catalog", "progression"):
                for key in base[section]:
                    snap = deepcopy(base)
                    del snap[section][key]
                    variants.append(snap)
                snap = deepcopy(base)
                snap[section]["extra"] = 1
                variants.append(snap)
            for path, value in ((('xp_event_id',), True), (('coin_amount',), 5.0), (('xp_amount',), 701),
                (('bank', 'transaction_id'), True), (('item', 'quantity'), True),
                (('item', 'item_level_id'), 1), (('bank', 'balance_after'), 999),
                (('effects',), [["XP", 700], ["ITEM", 1], ["DUCKYCOINS", 5]]),
                (('anchor_xp_event_id',), None), (('evolution_ids',), []), (('schema',), "unknown")):
                snap = deepcopy(base)
                target = snap
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                variants.append(snap)
            try:
                for index, snap in enumerate(variants):
                    DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=snap)
                    before = rows()
                    with self.subTest(snapshot_case=index), self.assertRaises(services.DemoIntegrityError):
                        self.apply(token)
                    self.assertEqual(rows(), before)
            finally:
                DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=base)
            self.replay(token, original)
            evidence["observations"].append({"snapshot_corruptions_rejected": len(variants)})

        def test_real_cause_and_identity_corruption(self):
            token = self.token()
            original = self.apply(token)
            row = DemoTargetRewardEvent.objects.get(pk=original.event_id)
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            other = services.create_demo_progress(session_token=secret)
            other_result = self.apply(self.token(progress=other), progress=other)
            spare = User(username="spare-" + uuid4().hex, is_active=False)
            spare.set_unusable_password()
            spare.save()
            entries = (
                (DemoTargetRewardEvent, row.pk, {"fingerprint": "0" * 64}),
                (DemoTargetRewardEvent, row.pk, {"activity_type": "challenge"}),
                (DemoTargetRewardEvent, row.pk, {"rule_set_version": "wrong"}),
                (DemoTargetRewardEvent, row.pk, {"reason_codes": ["unexpected"]}),
                (DemoTargetRewardEvent, row.pk, {"recipient_id": "demo-progress:999"}),
                (DemoTargetXPEvent, row.xp_event_id, {"operation_key": "rx1:" + "0" * 28}),
                (DemoTargetXPEvent, row.xp_event_id, {"progress_id": other.pk}),
                (DemoTargetXPEvent, other_result.xp_event_id, {"operation_key": rewards._xp_key(original.identity)}),
                (Transaction, row.bank_transaction_id, {"wallet_id": other_result.bank.wallet_id}),
                (Transaction, other_result.bank.transaction_id, {"operation_key": rewards._bank_key(original.identity)}),
                (Transaction, row.bank_transaction_id, {"reference_id": "other"}),
                (Transaction, row.bank_transaction_id, {"amount": 6}),
                (ItemGrant, row.item_grant_id, {"ducky_id": other_result.item.ducky_id}),
                (ItemGrant, row.item_grant_id, {"reference_type": "other"}),
                (ItemGrant, row.item_grant_id, {"operation_key": "ri1:" + "0" * 64}),
                (ItemGrant, row.item_grant_id, {"quantity": 2}),
                (ItemGrant, other_result.item.item_grant_id, {"operation_key": rewards._item_key(original.identity)}),
                (services.DemoTargetProgress, self.progress.pk, {"synthetic_user_id": None}),
                (Ducky, original.item.ducky_id, {"sex": "bad"}),
                (Ducky, original.item.ducky_id, {"user_id": spare.pk}),
                (Wallet, original.bank.wallet_id, {"user_id": spare.pk}),
                (User, user.pk, {"is_active": True}),
            )
            for model, pk, changes in entries:
                obj = model.objects.get(pk=pk)
                old = {key: getattr(obj, key) for key in changes}
                try:
                    model.objects.filter(pk=pk).update(**changes)
                    before = rows()
                    with self.subTest(model=model.__name__, fields=tuple(changes)), self.assertRaises(services.DemoIntegrityError):
                        self.apply(token)
                    self.assertEqual(rows(), before)
                finally:
                    model.objects.filter(pk=pk).update(**old)
            evolution = DemoTargetEvolutionEvent.objects.filter(xp_event_id=row.xp_event_id).first()
            saved = {f.attname: getattr(evolution, f.attname) for f in evolution._meta.concrete_fields}
            DemoTargetEvolutionEvent.objects.filter(pk=evolution.pk).delete()
            try:
                with self.assertRaises(services.DemoIntegrityError): self.apply(token)
            finally:
                DemoTargetEvolutionEvent.objects.create(**saved)
            # Deliberately broken references only in this disposable database;
            # restore immediately and recheck FKs, never relax file isolation.
            for field in ("xp_event_id", "bank_transaction_id", "item_grant_id"):
                original_pk = getattr(row, field)
                with db.constraint_checks_disabled():
                    DemoTargetRewardEvent.objects.filter(pk=row.pk).update(**{field: 2**63-1})
                try:
                    before = rows()
                    with self.subTest(missing_cause=field), self.assertRaises(services.DemoIntegrityError): self.apply(token)
                    self.assertEqual(rows(), before)
                finally:
                    DemoTargetRewardEvent.objects.filter(pk=row.pk).update(**{field: original_pk})
                db.check_constraints()
            self.replay(token, original)
            evidence["observations"].append({"row_corruptions_rejected": len(entries) + 4})

        def test_orphan_causes_and_conflict(self):
            token = self.token()
            fact = rewards._fact(token, self.progress, services._owner(secret), "combo_challenge")
            self.apply(self.token("coin_challenge"), "coin_challenge")
            self.apply(self.token("item_challenge"), "item_challenge")
            self.progress.refresh_from_db()
            user = self.progress.synthetic_user
            stages = ("xp", "bank", "item")
            for stage in stages:
                # Real owner work creates an intentionally orphaned cause; roll
                # the test setup back only after exercising a new outer boundary.
                before_setup = rows()
                old_wallet = Wallet.objects.get(user=user)
                if stage == "xp":
                    with services._xp_transaction(self.progress, session_token=secret) as context:
                        services._grant_xp_in_transaction(context, amount=700, operation_key=rewards._xp_key(fact.identity))
                    cause = DemoTargetXPEvent.objects.get(progress=self.progress, operation_key=rewards._xp_key(fact.identity))
                elif stage == "bank":
                    cause = bank.credit_coins(user, 5, source=rules.ORIGIN, issuing_entity="EcomotorDemo",
                        operation_key=rewards._bank_key(fact.identity), reference_type="demo_reward_fact_v1",
                        reference_id=rewards._bank_key(fact.identity)).transaction
                else:
                    cause = duckies.grant_item(user, self.item, 1, rewards._item_key(fact.identity),
                        reference_type="demo_reward_item_v1", reference_id=rewards._item_key(fact.identity))
                before = rows()
                with self.assertRaises(services.DemoIntegrityError): self.apply(token)
                self.assertEqual(rows(), before)
                if stage == "xp":
                    DemoTargetEvolutionEvent.objects.filter(xp_event=cause).delete()
                    services.DemoTargetProgress.objects.filter(pk=self.progress.pk).update(
                        xp_total=cause.xp_before, current_level=cause.level_before, current_epoch_id=cause.epoch_before_id)
                if stage == "bank":
                    Wallet.objects.filter(user=user).update(available_balance=cause.balance_after - 5,
                        updated_at=old_wallet.updated_at)
                if stage == "item":
                    InventoryItem.objects.filter(ducky__user=user, item=self.item).update(quantity=1)
                type(cause).objects.filter(pk=cause.pk).delete()
                self.assertEqual(rows(), before_setup)
            original = self.apply(token)
            payload = signing.loads(token, salt=rewards.SALT)
            payload["occurred_at"] = (rewards._instant(payload["occurred_at"]) + timedelta(seconds=1)).isoformat(timespec="microseconds")
            before = rows()
            with self.assertRaises(services.DemoConflictError):
                self.apply(signing.dumps(payload, salt=rewards.SALT))
            self.assertEqual(rows(), before)
            self.replay(token, original)

        def test_real_shared_transaction_and_order(self):
            token = self.token()
            native = db.connection
            statements, writes = [], []
            def inspect(execute, sql, params, many, context):
                targets = (("ecomotor_target_demo_demotargetxpevent", "xp"),
                    ("bank_transaction", "bank"), ("duckies_itemgrant", "item"),
                    ("ecomotor_target_demo_demotargetrewardevent", "reward"))
                for table, label in targets:
                    if sql.startswith('INSERT INTO "' + table + '"'):
                        self.assertIs(db.connection, native)
                        self.assertIs(context["connection"], db)
                        self.assertEqual(db.alias, "default")
                        self.assertEqual(len(db.atomic_blocks), 2 if label in ("bank", "item") else 1)
                        self.assertTrue(native.in_transaction)
                        writes.append(label)
                        result = execute(sql, params, many, context)
                        if label == "reward":
                            self.assertEqual(observe('SELECT COUNT(*) FROM ecomotor_target_demo_demotargetrewardevent WHERE progress_id=?',
                                (self.progress.pk,)), [(0,)])
                        return result
                return execute(sql, params, many, context)
            native.set_trace_callback(statements.append)
            try:
                with db.execute_wrapper(inspect): result = self.apply(token)
            finally:
                native.set_trace_callback(None)
            self.assertEqual(writes, ["xp", "bank", "item", "reward"])
            self.assertEqual(statements.count("BEGIN IMMEDIATE"), 1)
            self.assertEqual(statements.count("COMMIT"), 1)
            self.assertEqual(sum(s.startswith("SAVEPOINT") for s in statements), 2)
            self.assertEqual(sum(s.startswith("RELEASE SAVEPOINT") for s in statements), 2)
            self.assertEqual(observe('SELECT COUNT(*) FROM ecomotor_target_demo_demotargetrewardevent WHERE id=?',
                (result.event_id,)), [(1,)])
            evidence["observations"].append({"effect_order": writes, "same_native_default": True,
                "transaction_sql": [s for s in statements if s.startswith(("BEGIN", "SAVEPOINT", "RELEASE", "COMMIT", "ROLLBACK"))]})

        def test_complete_rollback_matrix(self):
            from django.db.models.query import QuerySet
            create = QuerySet.create
            def after(function):
                def wrapped(*args, **kwargs):
                    function(*args, **kwargs)
                    raise RuntimeError("injected after real work")
                return wrapped
            def fail(*args, **kwargs): raise RuntimeError("injected before work")
            def fail_reward(query, **kwargs):
                if query.model is DemoTargetRewardEvent: fail()
                return create(query, **kwargs)
            def after_reward(query, **kwargs):
                result = create(query, **kwargs)
                if query.model is DemoTargetRewardEvent: fail()
                return result
            def fail_v4_snapshot(*args, **kwargs):
                if kwargs.get("schema") == rewards.COMBO_SNAPSHOT_VERSION: fail()
                return snapshot(*args, **kwargs)
            snapshot = rewards._snapshot
            stages = [
                (services, "_grant_xp_in_transaction", fail),
                (services, "_grant_xp_in_transaction", after(services._grant_xp_in_transaction)),
                (rewards, "_wallet", after(rewards._wallet)),
                (bank, "credit_coins", fail), (bank, "credit_coins", after(bank.credit_coins)),
                (rewards, "_ducky", after(rewards._ducky)),
                (duckies, "grant_item", fail), (duckies, "grant_item", after(duckies.grant_item)),
                (QuerySet, "create", fail_reward), (QuerySet, "create", after_reward),
                (rewards, "_snapshot", fail_v4_snapshot),
                (rewards, "_recorded_combo", after(rewards._recorded_combo))]
            count = 0
            for existing in (False, True):
                progress = services.create_demo_progress(session_token=secret)
                if existing:
                    self.apply(self.token("coin_challenge", progress), "coin_challenge", progress)
                    self.apply(self.token("item_challenge", progress), "item_challenge", progress)
                token = self.token(progress=progress)
                for module, name, replacement in stages:
                    before = rows()
                    with self.subTest(existing=existing, stage=name), patch.object(module, name, replacement), \
                            self.assertRaisesRegex(RuntimeError, "injected"):
                        self.apply(token, progress=progress)
                    self.assertEqual(rows(), before)
                    self.assertEqual(observe('SELECT xp_total FROM ecomotor_target_demo_demotargetprogress WHERE id=?',
                        (progress.pk,)), [(0,)])
                    self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                    count += 1
            for failing_model in (Wallet, DemoTargetEvolutionEvent):
                progress = services.create_demo_progress(session_token=secret)
                token = self.token(progress=progress)
                seen = 0
                def fail_partial(query, **kwargs):
                    nonlocal seen
                    result = create(query, **kwargs)
                    if query.model is failing_model:
                        seen += 1
                        if seen == (3 if failing_model is DemoTargetEvolutionEvent else 1): fail()
                    return result
                before = rows()
                with patch.object(QuerySet, "create", fail_partial), self.assertRaisesRegex(RuntimeError, "injected"):
                    self.apply(token, progress=progress)
                self.assertEqual(rows(), before)
                self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                count += 1
            evidence["observations"].append({"rollback_stages": count, "all_tables_identical": True,
                "fresh_and_existing_provisioning": True})

        def concurrent(self, mode):
            tokens = [self.token(), self.token()]
            if mode in ("same", "conflict"): tokens[1] = tokens[0]
            if mode == "conflict":
                payload = signing.loads(tokens[1], salt=rewards.SALT)
                payload["occurred_at"] = (rewards._instant(payload["occurred_at"]) + timedelta(seconds=1)).isoformat(timespec="microseconds")
                tokens[1] = signing.dumps(payload, salt=rewards.SALT)
            operation = services.issue_demo_operation(self.progress, session_token=secret)
            barrier = Barrier(2)
            def worker(index):
                connection = connections["default"]
                try:
                    connection.ensure_connection()
                    native = connection.connection
                    barrier.wait(timeout=10)
                    try:
                        if mode == "direct" and index == 1:
                            services.grant_demo_target_xp(self.progress, amount=100,
                                operation_token=operation, session_token=secret)
                            return "ok", False, id(native)
                        if mode == "individual" and index == 1:
                            result = self.apply(tokens[1], "coin_challenge")
                        else: result = self.apply(tokens[index])
                        return "ok", result.replay, id(native)
                    except services.DemoConflictError:
                        return "conflict", False, id(native)
                finally:
                    connection.close()
            if mode == "individual": tokens[1] = self.token("coin_challenge")
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(worker, index) for index in range(2)]
                results = [future.result(timeout=25) for future in futures]
            self.assertNotEqual(results[0][2], results[1][2])
            self.assertEqual(sorted(r[0] for r in results), ["conflict", "ok"] if mode == "conflict" else ["ok", "ok"])
            count = 2 if mode == "distinct" else 1
            self.progress.refresh_from_db()
            self.assertEqual(self.progress.xp_total, 700 * count + (100 if mode == "direct" else 0))
            self.assertEqual(Wallet.objects.get(user_id=self.progress.synthetic_user_id).available_balance,
                5 * count + (5 if mode == "individual" else 0))
            self.assertEqual(InventoryItem.objects.get(ducky__user_id=self.progress.synthetic_user_id, item=self.item).quantity, count)
            self.assertEqual(DemoTargetRewardEvent.objects.filter(progress=self.progress).count(),
                count + (1 if mode == "individual" else 0))
            if mode == "same": self.assertEqual(sum(r[1] for r in results), 1)
            rewards.read_demo_rewards(self.progress, session_token=secret)
            evidence["observations"].append({"concurrency": mode, "independent_connections": True,
                "outcomes": [r[0] for r in results]})

        def test_concurrent_same(self): self.concurrent("same")
        def test_concurrent_conflict(self): self.concurrent("conflict")
        def test_concurrent_distinct(self): self.concurrent("distinct")
        def test_concurrent_direct_and_individual(self):
            self.concurrent("direct")
            self.progress = services.create_demo_progress(session_token=secret)
            self.concurrent("individual")

        def test_real_timeout_and_explicit_retry(self):
            token = self.token()
            before = rows()
            held, release = Event(), Event()
            def holder():
                connection = connections["default"]
                try:
                    with services._xp_transaction(self.progress, session_token=secret) as context:
                        services._check_xp_transaction(context)
                        held.set()
                        release.wait(timeout=15)
                finally: connection.close()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(holder)
                self.assertTrue(held.wait(timeout=10))
                start = monotonic()
                try:
                    with self.assertRaises(services.DemoBusyError): self.apply(token)
                    elapsed = monotonic() - start
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertLess(elapsed, 9)
                    self.assertEqual(rows(), before)
                    self.assertFalse(db.in_atomic_block or db.connection.in_transaction)
                finally: release.set()
                future.result(timeout=10)
            original = self.apply(token)
            self.replay(token, original)
            evidence["observations"].append({"real_timeout_seconds": round(elapsed, 3), "explicit_retry_no_duplicate": True})

    groups = {
        "functional": ("test_primary_and_exact_three_keys", "test_existing_state_and_old_modalities",
                       "test_history_v1_v2_v3_v4_and_changed_present"),
        "validation": ("test_closed_token_and_semantics", "test_invalid_complete_proposals", "test_invalid_resources_and_boundaries"),
        "integrity": ("test_strict_snapshot_corruption", "test_real_cause_and_identity_corruption", "test_orphan_causes_and_conflict"),
        "atomicity": ("test_real_shared_transaction_and_order", "test_complete_rollback_matrix"),
        "concurrency": ("test_concurrent_same", "test_concurrent_conflict", "test_concurrent_distinct",
                        "test_concurrent_direct_and_individual", "test_real_timeout_and_explicit_retry"),
    }
    if scenario not in groups: raise ValueError("Unknown combo scenario")
    try:
        try: demo_connection()
        except ImproperlyConfigured: pass
        else: raise AssertionError("Ordinary opening accepted an absent fixture")
        assert not path.exists()
        call_command("migrate", database="default", verbosity=0, stdout=StringIO())
        assert not MIGRATING.get()
        call_command("seed_persistent_target_demo", stdout=StringIO())
        db = demo_connection()
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(ComboTests(name) for name in groups[scenario]))
        if result.wasSuccessful() and scenario == "functional":
            call_command("check", databases=["default"], stdout=StringIO())
            call_command("makemigrations", check=True, dry_run=True, stdout=StringIO())
            evidence["checks_and_no_model_changes"] = True
        evidence.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
            skipped=len(result.skipped), success=result.wasSuccessful())
    finally:
        connections.close_all()
    evidence.update(connections_closed=all(c.connection is None for c in connections.all()),
        only_fixture_connections=bool(opened) and all(p in allowed for p in opened))
    print("COMBO_DEFAULT_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run(*sys.argv[1:]))
