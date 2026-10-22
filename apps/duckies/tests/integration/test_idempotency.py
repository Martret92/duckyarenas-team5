from apps.bank.models import Transaction, TransactionType
from apps.bank.services import IdempotencyConflict, credit_coins
from apps.duckies.models import InventoryItem, ItemGrant
from apps.shop.models import Purchase
from apps.shop.services import PurchaseIdempotencyConflict, purchase_item

from .fixtures import IntegrationFixture


class CrossAppIdempotencyTests(IntegrationFixture):
    def test_same_purchase_key_returns_original_without_second_charge_or_delivery(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        first = purchase_item(self.user, offer.code, operation_key="once")
        second = purchase_item(self.user, offer.code, operation_key="once")
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky).count(), 1)
        self.assertEqual(
            Transaction.objects.filter(wallet=self.wallet, transaction_type=TransactionType.PURCHASE).count(),
            1,
        )
        self.assertEqual(
            InventoryItem.objects.get(ducky=self.ducky, item=item, item_level=level).quantity, 3
        )

    def test_replay_survives_price_and_availability_changes(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        first = purchase_item(self.user, offer.code, operation_key="price-frozen")
        offer.price_coins = 500
        offer.is_available = False
        offer.save(update_fields=["price_coins", "is_available"])
        replay = purchase_item(self.user, offer.code, operation_key="price-frozen")
        self.assertEqual(first.pk, replay.pk)
        self.assertEqual(replay.total_price_coins, 20)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 80)

    def test_same_purchase_key_different_quantity_conflicts(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        purchase_item(self.user, offer.code, operation_key="same-key")
        with self.assertRaises(PurchaseIdempotencyConflict):
            purchase_item(self.user, offer.code, operation_key="same-key", quantity=2)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 80)

    def test_bank_credit_replay_and_conflict(self):
        first = credit_coins(self.user, 25, source="test", operation_key="reward-key")
        replay = credit_coins(self.user, 25, source="test", operation_key="reward-key")
        self.assertEqual(first.transaction.pk, replay.transaction.pk)
        self.assertFalse(replay.created)
        with self.assertRaises(IdempotencyConflict):
            credit_coins(self.user, 30, source="test", operation_key="reward-key")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 25)
