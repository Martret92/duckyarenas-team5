from unittest.mock import patch

from apps.bank.models import Transaction, TransactionType
from apps.bank.services import credit_coins
from apps.duckies.models import InventoryItem, ItemGrant
from apps.shop.models import Purchase
from apps.shop.services import DeliveryRejected, purchase_item

from .fixtures import IntegrationFixture


class CrossAppAtomicityTests(IntegrationFixture):
    def test_failed_delivery_rolls_back_bank_and_shop(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        with patch("apps.shop.services.grant_item", side_effect=ValueError("delivery failure")):
            with self.assertRaises(DeliveryRejected):
                purchase_item(self.user, offer.code, operation_key="rollback-delivery")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 100)
        self.assertFalse(Purchase.objects.filter(user=self.user).exists())
        self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())
        self.assertFalse(InventoryItem.objects.filter(ducky=self.ducky, item=item).exists())
        self.assertFalse(
            Transaction.objects.filter(wallet=self.wallet, transaction_type=TransactionType.PURCHASE).exists()
        )

    def test_purchase_record_failure_rolls_back_bank_and_duckies(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        with patch("apps.shop.services.Purchase.objects.create", side_effect=RuntimeError("write failure")):
            with self.assertRaises(RuntimeError):
                purchase_item(self.user, offer.code, operation_key="rollback-purchase")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 100)
        self.assertFalse(Purchase.objects.filter(user=self.user).exists())
        self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())
        self.assertFalse(InventoryItem.objects.filter(ducky=self.ducky, item=item).exists())
        self.assertFalse(
            Transaction.objects.filter(wallet=self.wallet, transaction_type=TransactionType.PURCHASE).exists()
        )

    def test_failed_xp_outfit_sync_rolls_back_ecomotor(self):
        from apps.duckies.integration_services import grant_xp_and_sync_outfit
        from apps.ecomotor.models import XPEvent, EvolutionEvent
        with patch(
            "apps.duckies.integration_services.sync_historical_outfit",
            side_effect=ValueError("outfit sync failure"),
        ):
            with self.assertRaises(ValueError):
                grant_xp_and_sync_outfit(self.user, 200, "rollback-xp")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.historical_xp_total, 0)
        self.assertEqual(XPEvent.objects.filter(profile=self.profile).count(), 0)
        self.assertEqual(EvolutionEvent.objects.filter(profile=self.profile).count(), 0)
