"""Test-only HTTP V4: real Client/CSRF/coordinator and owned protected default.

Only this owned subprocess prepares the synthetic HINT. All owner APIs and
SQLite commits/rollback/concurrency are real; patches inject faults or observe.
"""

import json
import os
from pathlib import Path
import sys
from tempfile import gettempdir
import unittest


def run(root, scenario):
    root = Path(root).absolute()
    if (root.parent.resolve() != Path(gettempdir()).resolve()
            or not root.name.startswith("ducky-rewards-combo-http-") or not root.is_dir()
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
    from io import StringIO
    from dataclasses import replace
    from datetime import timedelta
    from threading import Event
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

    from django.core.exceptions import ImproperlyConfigured
    from django.core.management import call_command
    from django.db import connections
    from django.core import signing
    from django.test import Client
    from html.parser import HTMLParser
    from urllib.parse import urlencode
    import re
    from apps.bank.models import Wallet, Transaction
    from apps.bank import services as bank
    from apps.duckies.models import Item, ItemGrant, InventoryItem, EquipmentSlot
    from apps.duckies import services as duckies
    from . import services, reward_demo_services as rewards, reward_demo_rules as rules, playable_services as playable
    from .isolation import demo_connection, MIGRATING
    from .models import (DemoTargetXPEvent, DemoTargetEvolutionEvent, DemoTargetRewardEvent,
                         DemoTargetOptionConfiguration)

    db = connections["default"]
    evidence = {"scenario": scenario, "alias": "default", "file": str(path),
                "pid": os.getpid(), "observations": []}

    url = "/demo/objetivo-persistente/"
    label = "Desafío combinado ficticio (+700 XP, +5 DuckyCoins y +1 HINT)"
    applied = "APPLIED: +700 XP sintéticas, +5 DuckyCoins ficticias y +1 HINT sintético concedidos en una única recompensa."
    replayed = "Replay Rewards V4: resultado histórico recuperado (700 XP, 5 DuckyCoins y 1 HINT originales). No se ha vuelto a conceder ningún premio."

    class Forms(HTMLParser):
        def __init__(self, page):
            super().__init__()
            self.forms, self.current, self.ids = [], None, []
            self.feed(page)
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "form": self.current, self.ids = {}, []
            if tag == "input" and self.current is not None and "name" in attrs:
                self.current[attrs["name"]] = attrs.get("value", "")
                self.ids.append(attrs.get("id", ""))
        def handle_endtag(self, tag):
            if tag == "form" and self.current is not None:
                self.forms.append((self.current, tuple(self.ids)))
                self.current = None

    def business():
        with db.cursor() as cursor:
            return {table: cursor.execute('SELECT * FROM "' + table + '" ORDER BY rowid').fetchall()
                for table in db.introspection.table_names(cursor) if table not in ("django_session", "sqlite_sequence")}

    class HTTPTests(unittest.TestCase):
        def setUp(self):
            slot, _ = EquipmentSlot.objects.get_or_create(code="combo-http-hint", defaults={"name": "Synthetic"})
            self.item, _ = Item.objects.update_or_create(code="demo-reward-hint-v1", defaults={
                "name": "Synthetic HINT", "category": Item.HINT, "consumable": True, "is_active": True, "slot": slot})

        def post(self, client, payload, **kwargs):
            return client.post(url, payload, HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value, **kwargs)

        def start(self):
            client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
            before = business()
            self.assertEqual(client.get(url).status_code, 200)
            self.assertEqual(business(), before)
            self.assertEqual(self.post(client, {"action": "start"}).status_code, 302)
            self.assertEqual(client.get(url).status_code, 200)
            return client

        def progress(self, client):
            return services.DemoTargetProgress.objects.get(pk=client.session["demo_progress"])

        def form(self, client, activity="combo_challenge"):
            page = client.get(url).content.decode()
            found = [values for values, ids in Forms(page).forms if values.get("activity") == activity
                and any(identity == f"reward_{activity}_fact_token" for identity in ids)]
            self.assertEqual(len(found), 1)
            self.assertEqual(set(found[0]), {"action", "activity", "fact_token", "csrfmiddlewaretoken"})
            return found[0]

        def reward(self, client):
            return DemoTargetRewardEvent.objects.get(progress=self.progress(client), activity_type="combo_challenge")

        def safe(self, response):
            page = response.content.decode()
            for forbidden in (str(path), str(root), "Traceback", "private-failure", "SELECT private", "INSERT private"):
                self.assertNotIn(forbidden, page)
            return page

        def test_primary_real_http_and_three_blocks(self):
            client = self.start()
            before = business()
            page = client.get(url).content.decode()
            self.assertEqual(business(), before)
            self.assertIsNone(self.progress(client).synthetic_user_id)
            self.assertIn(label, page)
            from .forms import REWARD_HTTP_ACTIVITIES, RewardDemoForm
            self.assertEqual([a for a, _ in REWARD_HTTP_ACTIVITIES],
                ["challenge", "visit", "coin_challenge", "item_challenge", "combo_challenge"])
            self.assertEqual(tuple(RewardDemoForm().fields), ("action", "activity", "fact_token"))
            data = self.form(client)
            response = self.post(client, data)
            self.assertEqual((response.status_code, response["Location"]), (302, url))
            progress = self.progress(client)
            row = self.reward(client)
            self.assertEqual((progress.xp_total, progress.current_level, progress.current_epoch.ordinal), (700, 8, 7))
            self.assertEqual(DemoTargetRewardEvent.objects.filter(progress=progress).count(), 1)
            self.assertEqual(DemoTargetEvolutionEvent.objects.filter(progress=progress).count(), 6)
            self.assertEqual(row.snapshot["schema"], "demo-reward-result-v4")
            self.assertEqual(DemoTargetXPEvent.objects.get(pk=row.xp_event_id).amount, 700)
            self.assertEqual(Transaction.objects.get(pk=row.bank_transaction_id).amount, 5)
            self.assertEqual(ItemGrant.objects.get(pk=row.item_grant_id).quantity, 1)
            self.assertEqual(Wallet.objects.get(user=progress.synthetic_user).available_balance, 5)
            self.assertEqual(InventoryItem.objects.get(ducky__user=progress.synthetic_user, item=self.item).quantity, 1)
            response = client.get(url)
            self.assertIn("no-store", response["Cache-Control"])
            page = self.safe(response)
            self.assertIn(applied, page)
            self.assertEqual(page.count(f'data-reward-id="{row.pk}"'), 1)
            reward_row = re.search(r'<tr data-reward-id="' + str(row.pk) + r'">(.*?)</tr>', page, re.S).group(1)
            self.assertEqual(reward_row.count('class="reward-effect"'), 6)
            for text in ("+700 XP sintéticas", "+5 DuckyCoins ficticias", "+1 HINT sintético",
                    f"XPEvent #{row.xp_event_id}", f"Transaction #{row.bank_transaction_id}",
                    f"ItemGrant #{row.item_grant_id}", row.snapshot["bank"]["reference_id"],
                    row.snapshot["item"]["reference_id"], "demo-item-map-v1", "0 → 700", "1 → 8"):
                self.assertIn(text, reward_row)
            for old in ("Un hecho, un premio.", "UN EFECTO", "REW-MULTI-02 · Laboratorio"):
                self.assertNotIn(old, page)
            self.assertNotEqual(client.session["reward_tokens"]["combo_challenge"], data["fact_token"])
            self.export_preview(page)
            evidence["observations"].append({"prg": 302, "reward_events": 1, "causes": 3,
                "xp": 700, "coins": 5, "hint": 1, "evolutions": 6, "single_row_three_effects": True})

        def export_preview(self, page):
            destination = os.environ.get("COMBO_HTTP_PREVIEW_DIR")
            if not destination: return
            folder = Path(destination)
            if not folder.is_absolute() or not folder.is_dir() or folder.is_symlink():
                raise AssertionError("An explicit existing artifact directory is required")
            # Static, inert copy only. No server/Django/database/token is needed
            # for visual review after this disposable fixture has been removed.
            css = (Path(__file__).parent / "static/ecomotor_target_demo/persistent.css").read_text(encoding="utf-8")
            page = re.sub(r'<link rel="stylesheet"[^>]+>', lambda _: '<style>' + css + '</style>', page)
            page = re.sub(r'<input[^>]+type="hidden"[^>]*>', '', page)
            page = re.sub(r'<button', '<button disabled', page)
            page = re.sub(r'<form[^>]*>', '<div class="preview-form">', page).replace('</form>', '</div>')
            (folder / "combo-v4-preview.html").write_text(page, encoding="utf-8")
            evidence["preview_exported_without_tokens"] = True

        def test_original_last_row_replay_refresh_and_reopen(self):
            client = self.start()
            data = self.form(client)
            self.assertEqual(self.post(client, data).status_code, 302)
            row = self.reward(client)
            original = deepcopy(row.snapshot)
            page = client.get(url).content.decode()
            parsed = Forms(page).forms
            repeats = [values for values, ids in parsed if any(identity in ids for identity in
                ("reward_replay_fact_token", f"reward_history_{row.pk}_fact_token"))]
            self.assertEqual(len(repeats), 2)
            for payload in (data, *repeats):
                before = business()
                self.assertEqual(self.post(client, payload).status_code, 302)
                self.assertEqual(business(), before)
                page = client.get(url).content.decode()
                self.assertIn(replayed, page)
                self.assertNotIn(applied, page)
                self.assertEqual(client.get(url).status_code, 200)
                self.assertEqual(business(), before)
                row.refresh_from_db()
                self.assertEqual(row.snapshot, original)
            self.assertEqual(ItemGrant.objects.filter(pk=row.item_grant_id).count(), 1)
            db.close()
            before = business()
            self.assertEqual(self.post(client, repeats[1]).status_code, 302)
            self.assertEqual(business(), before)
            self.assertIn(replayed, client.get(url).content.decode())
            evidence["observations"].append({"original_last_row_replay": True, "business_rows_identical": True,
                "reopen_preserved": True})

        def test_replay_after_real_spend_consume_and_xp(self):
            client = self.start()
            data = self.form(client)
            self.assertEqual(self.post(client, data).status_code, 302)
            row = self.reward(client)
            original = deepcopy(row.snapshot)
            progress = self.progress(client)
            secret = client.session["demo_secret"]
            services.grant_demo_target_xp(progress, amount=200, operation_token=services.issue_demo_operation(
                progress, session_token=secret), session_token=secret)
            user = progress.synthetic_user
            bank.debit_coins(user, 5, source="combo-http-test", operation_key="spend-" + uuid4().hex)
            duckies.equip_item(user, self.item)
            duckies.consume_item(user, self.item, 1, "consume-" + uuid4().hex,
                server_accepted=True, game_reference="combo-http-synthetic-game")
            db.close()
            before = business()
            page = client.get(url).content.decode()
            self.assertIn('id="bank-balance">0</strong>', page)
            self.assertIn('id="hint-quantity">0</strong>', page)
            self.assertIn('id="xp-total">900</strong>', page)
            self.assertIn("Saldo después de aquella recompensa: 5 DuckyCoins", page)
            self.assertIn("Cantidad histórica entregada: 1", page)
            self.assertIn("0 → 700", page)
            replay_form = next(values for values, ids in Forms(page).forms
                if f"reward_history_{row.pk}_fact_token" in ids)
            self.assertEqual(self.post(client, replay_form).status_code, 302)
            self.assertEqual(business(), before)
            self.assertIn(replayed, client.get(url).content.decode())
            row.refresh_from_db()
            self.assertEqual(row.snapshot, original)
            self.assertFalse(InventoryItem.objects.filter(ducky__user=user, item=self.item).exists())
            evidence["observations"].append({"history_after_real_spend_consume_xp": True,
                "current_xp": 900, "current_balance": 0, "current_hint": 0, "original_snapshot_unchanged": True})

        def test_csrf_methods_get_and_strict_fields(self):
            client = self.start()
            data = self.form(client)
            before = business()
            no_csrf = {k: v for k, v in data.items() if k != "csrfmiddlewaretoken"}
            self.assertEqual(client.post(url, no_csrf).status_code, 403)
            self.assertEqual(client.post(url, {**no_csrf, "csrfmiddlewaretoken": "bad"}).status_code, 403)
            for method in ("put", "patch", "delete", "head", "options", "trace"):
                self.assertEqual(getattr(client, method)(url,
                    HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value).status_code, 405)
            for key in ("amount", "xp", "coin_amount", "quantity", "user_id", "wallet_id", "ducky_id", "item_id",
                    "xp_event_id", "transaction_id", "item_grant_id", "fact_id", "progress", "recipient_id", "origin_code", "other"):
                with self.subTest(extra=key):
                    self.assertEqual(self.post(client, {**data, key: "1"}).status_code, 400)
                    self.assertEqual(client.get(url, {key: "1"}).status_code, 400)
                    self.assertEqual(business(), before)
            for key in ("action", "activity", "fact_token"):
                self.assertEqual(self.post(client, {k: v for k, v in data.items() if k != key}).status_code, 400)
                duplicated = urlencode([*data.items(), (key, data[key])])
                self.assertEqual(self.post(client, duplicated, content_type="application/x-www-form-urlencoded").status_code, 400)
            self.assertEqual(business(), before)

        def test_closed_tokens_and_escaped_error(self):
            client = self.start()
            data = self.form(client)
            before = business()
            payload = signing.loads(data["fact_token"], salt=rewards.SALT)
            invalid = ["forged", data["fact_token"] + "x", client.session["demo_operation"],
                client.session["reward_tokens"]["challenge"], signing.dumps(payload, salt="other-purpose")]
            for key, value in (("progress", True), ("fact_id", "A" * 32), ("fact_version", "demo-fact-v3"),
                    ("mapping_version", "wrong"), ("item_code", "wrong"),
                    ("occurred_at", payload["occurred_at"].replace("+00:00", "Z")), ("extra", 1)):
                invalid.append(signing.dumps({**payload, key: value}, salt=rewards.SALT))
            for token in invalid:
                response = self.post(client, {**data, "fact_token": token})
                self.assertEqual(response.status_code, 403)
                self.assertNotIn(token, self.safe(response))
                self.assertEqual(business(), before)
            response = self.post(client, {**data, "activity": "<script>private-failure</script>"})
            self.assertEqual(response.status_code, 400)
            page = response.content.decode()
            self.assertNotIn("<script>private-failure</script>", page)
            self.assertIn("&lt;script&gt;private-failure&lt;/script&gt;", page)
            self.assertEqual(business(), before)

        def test_sessions_reset_and_private_history(self):
            a, b = self.start(), self.start()
            data = self.form(a)
            before = business()
            self.assertEqual(self.post(b, {**data,
                "csrfmiddlewaretoken": b.cookies[settings.CSRF_COOKIE_NAME].value}).status_code, 403)
            self.assertEqual(business(), before)
            self.assertEqual(self.post(a, data).status_code, 302)
            row = self.reward(a)
            self.assertNotIn(f'data-reward-id="{row.pk}"', b.get(url).content.decode())
            state = b.session
            original_pk = state["demo_progress"]
            state["demo_progress"] = self.progress(a).pk
            state.save()
            before = business()
            self.assertEqual(b.get(url).status_code, 403)
            self.assertEqual(business(), before)
            state = b.session
            state["demo_progress"] = original_pk
            state.save()
            old_pk = self.progress(a).pk
            self.assertEqual(self.post(a, {"action": "start"}).status_code, 302)
            self.assertNotEqual(self.progress(a).pk, old_pk)
            for key in ("reward_tokens", "reward_last", "reward_notice", "reward_confirmed_tokens"):
                self.assertNotIn(key, a.session)
            before = business()
            self.assertEqual(self.post(a, data).status_code, 403)
            self.assertEqual(business(), before)
            self.assertTrue(DemoTargetRewardEvent.objects.filter(pk=row.pk, progress_id=old_pk).exists())
            self.assertNotIn(f'data-reward-id="{row.pk}"', a.get(url).content.decode())
            self.assertEqual(self.post(b, self.form(b)).status_code, 302)
            self.assertNotEqual(row.snapshot["bank"]["user_id"], self.progress(b).synthetic_user_id)

        def test_conflict_corruption_and_no_stale_notice(self):
            client = self.start()
            data = self.form(client)
            self.assertEqual(self.post(client, data).status_code, 302)
            # Leave the success notice unconsumed, then fail a validly signed conflict.
            payload = signing.loads(data["fact_token"], salt=rewards.SALT)
            payload["occurred_at"] = (rewards._instant(payload["occurred_at"]) + timedelta(seconds=1)).isoformat(timespec="microseconds")
            before = business()
            response = self.post(client, {**data, "fact_token": signing.dumps(payload, salt=rewards.SALT)})
            self.assertEqual(response.status_code, 409)
            self.assertNotIn(applied, self.safe(response))
            self.assertNotIn(applied, client.get(url).content.decode())
            self.assertEqual(business(), before)
            row = self.reward(client)
            original = deepcopy(row.snapshot)
            for field in ("bank", "item", "progression"):
                changed = deepcopy(original)
                changed[field]["private-failure"] = 1
                DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=changed)
                before = business()
                response = client.get(url)
                self.assertEqual(response.status_code, 409)
                self.safe(response)
                self.assertEqual(business(), before)
            DemoTargetRewardEvent.objects.filter(pk=row.pk).update(snapshot=original)
            entry = Transaction.objects.get(pk=row.bank_transaction_id)
            Transaction.objects.filter(pk=entry.pk).update(reference_id="private-failure")
            try:
                self.assertEqual(client.get(url).status_code, 409)
            finally:
                Transaction.objects.filter(pk=entry.pk).update(reference_id=entry.reference_id)

        def test_unavailable_configuration_and_operational_errors(self):
            from django.db import OperationalError
            client = self.start()
            data = self.form(client)
            for changes in ({"code": "absent"}, {"is_active": False}, {"category": Item.ATTACK}):
                old = {key: getattr(self.item, key) for key in changes}
                Item.objects.filter(pk=self.item.pk).update(**changes)
                try:
                    before = business()
                    response = self.post(client, data)
                    self.assertEqual(response.status_code, 503)
                    self.assertNotIn(applied, self.safe(response))
                    self.assertEqual(business(), before)
                finally:
                    Item.objects.filter(pk=self.item.pk).update(**old)
            with patch.object(rules, "ITEM_MAPPING", replace(rules.ITEM_MAPPING, mapping_version="unknown")):
                before = business()
                self.assertEqual(self.post(client, data).status_code, 503)
                self.assertEqual(business(), before)
            def fail_sql(execute, sql, params, many, context):
                if 'INSERT INTO "bank_transaction"' in sql: raise OperationalError("SELECT private-failure " + str(path))
                return execute(sql, params, many, context)
            before = business()
            with db.execute_wrapper(fail_sql): response = self.post(client, data)
            self.assertEqual(response.status_code, 503)
            self.safe(response)
            self.assertEqual(business(), before)

        def test_real_http_rollback_representative_stages(self):
            from django.db.models.query import QuerySet
            from django.db import OperationalError
            create = QuerySet.create
            for target in (Transaction, ItemGrant, DemoTargetRewardEvent):
                client = self.start()
                data = self.form(client)
                before = business()
                def after_create(query, **kwargs):
                    result = create(query, **kwargs)
                    if query.model is target: raise OperationalError("private-failure after real write")
                    return result
                with patch.object(QuerySet, "create", after_create): response = self.post(client, data)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(business(), before)
                self.assertIsNone(self.progress(client).synthetic_user_id)
                self.assertNotIn(applied, self.safe(response))
            evidence["observations"].append({"http_rollback_stages": 3, "all_business_tables_identical": True})

        def test_real_timeout_and_explicit_retry(self):
            client = self.start()
            data = self.form(client)
            progress = self.progress(client)
            secret = client.session["demo_secret"]
            before = business()
            held, release = Event(), Event()
            def holder():
                try:
                    with services._xp_transaction(progress, session_token=secret):
                        held.set()
                        if not release.wait(15): raise AssertionError("Fixture lock not released")
                finally: connections["default"].close()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(holder)
                self.assertTrue(held.wait(10))
                start = monotonic()
                try:
                    response = self.post(client, data)
                    elapsed = monotonic() - start
                    self.assertEqual(response.status_code, 503)
                    self.assertGreaterEqual(elapsed, 4.5)
                    self.assertLess(elapsed, 9)
                    self.assertNotIn(applied, self.safe(response))
                finally:
                    release.set()
                    future.result(timeout=10)
            self.assertEqual(business(), before)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertEqual(self.post(client, data).status_code, 302)
            self.assertIn(replayed, client.get(url).content.decode())
            self.assertEqual(DemoTargetRewardEvent.objects.filter(progress=progress).count(), 1)
            evidence["observations"].append({"http_timeout": 503, "seconds": round(elapsed, 3), "explicit_retry_unique": True})

        def test_old_modalities_options_and_no_new_evolutions(self):
            client = self.start()
            expected = {"challenge": "APPLIED: +700 XP sintéticas y recompensa confirmadas juntas.",
                "coin_challenge": "APPLIED: +5 DuckyCoins ficticias confirmadas.",
                "item_challenge": "APPLIED: HINT sintético entregado y registrado.",
                "visit": "NO_REWARD: visita válida registrada, sin concesión de XP ni monedas ni objetos."}
            old_forms = []
            for activity, message in expected.items():
                data = self.form(client, activity)
                old_forms.append(data)
                self.assertEqual(self.post(client, data).status_code, 302)
                self.assertIn(message, client.get(url).content.decode())
            progress = self.progress(client)
            revision = None
            for option in ("persist-demo-tech-gamer", "persist-demo-epoch-3"):
                result = playable.configure_demo_option(progress, option_code=option,
                    increments=tuple((c, 0) for c in ("ATK", "DEF", "VEL", "INT", "LOG", "CUACK")),
                    operation_token=playable.issue_playable_operation(progress, action="configure", session_token=client.session["demo_secret"]),
                    expected_revision=revision, session_token=client.session["demo_secret"])
                revision = result.after.revision
            configs = list(DemoTargetOptionConfiguration.objects.values())
            self.assertEqual(self.post(client, self.form(client)).status_code, 302)
            row = self.reward(client)
            self.assertEqual(row.snapshot["evolution_ids"], [])
            page = client.get(url).content.decode()
            self.assertIn("Evoluciones históricas causadas: ninguna", page)
            self.assertIn("Gamer", page)
            self.assertIn("Romano", page)
            self.assertEqual(list(DemoTargetOptionConfiguration.objects.values()), configs)
            before = business()
            for data in old_forms:
                self.assertEqual(self.post(client, data).status_code, 302)
                self.assertIn("Replay Rewards histórico: sin nuevas concesiones", client.get(url).content.decode())
            self.assertEqual(business(), before)

    groups = {
        "functional": ("test_primary_real_http_and_three_blocks",),
        "replay": ("test_original_last_row_replay_refresh_and_reopen", "test_replay_after_real_spend_consume_and_xp"),
        "security": ("test_csrf_methods_get_and_strict_fields", "test_closed_tokens_and_escaped_error", "test_sessions_reset_and_private_history"),
        "errors": ("test_conflict_corruption_and_no_stale_notice", "test_unavailable_configuration_and_operational_errors",
                   "test_real_http_rollback_representative_stages", "test_real_timeout_and_explicit_retry"),
        "compatibility": ("test_old_modalities_options_and_no_new_evolutions",),
    }
    if scenario not in groups: raise ValueError("Unknown HTTP combo scenario")
    try:
        try: demo_connection()
        except ImproperlyConfigured: pass
        else: raise AssertionError("Ordinary open accepted an absent fixture")
        assert not path.exists()
        call_command("migrate", database="default", verbosity=0, stdout=StringIO())
        assert not MIGRATING.get()
        call_command("seed_persistent_target_demo", stdout=StringIO())
        db = demo_connection()
        result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(HTTPTests(name) for name in groups[scenario]))
        if result.wasSuccessful() and scenario == "functional":
            call_command("check", databases=["default"], stdout=StringIO())
            call_command("makemigrations", check=True, dry_run=True, stdout=StringIO())
            evidence["checks_and_no_model_changes"] = True
        evidence.update(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
            skipped=len(result.skipped), success=result.wasSuccessful())
    finally: connections.close_all()
    evidence.update(connections_closed=all(c.connection is None for c in connections.all()),
        only_fixture_connections=bool(opened) and all(p in allowed for p in opened))
    print("COMBO_HTTP_EVIDENCE=" + json.dumps(evidence, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run(*sys.argv[1:]))
