from apps.bank.models import Transaction, TransactionType, Wallet
from apps.bank.services import InsufficientFunds, WalletNotProvisioned, credit_coins
from apps.duckies.models import Ducky, InventoryItem, ItemGrant
from apps.shop.models import Purchase
from apps.shop.services import (
    BuyerNotProvisioned, PermanentItemAlreadyOwned, ProductUnavailable,
    purchase_item,
)

from .fixtures import IntegrationFixture


class ShopBankDuckiesTests(IntegrationFixture):
    def test_purchase_debits_and_delivers_correct_pack(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        purchase = purchase_item(self.user, offer.code, operation_key="purchase-1", quantity=2)
        self.wallet.refresh_from_db()
        inventory = InventoryItem.objects.get(ducky=self.ducky, item=item, item_level=level)
        self.assertEqual(self.wallet.available_balance, 60)
        self.assertEqual(inventory.quantity, 6)
        self.assertEqual(purchase.total_price_coins, 40)
        self.assertEqual(purchase.bank_transaction.amount, -40)
        self.assertEqual(purchase.bank_transaction.wallet_id, self.wallet.pk)
        self.assertEqual(ItemGrant.objects.filter(ducky=self.ducky, item=item).count(), 1)

    def test_multiple_purchases_accumulate_consumables(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        purchase_item(self.user, offer.code, operation_key="purchase-a")
        purchase_item(self.user, offer.code, operation_key="purchase-b")
        inv = InventoryItem.objects.get(ducky=self.ducky, item=item, item_level=level)
        self.assertEqual(inv.quantity, 6)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 60)

    def test_insufficient_funds_leaves_no_purchase_or_delivery(self):
        offer, item, level = self.make_offer()
        with self.assertRaises(InsufficientFunds):
            purchase_item(self.user, offer.code, operation_key="no-money")
        self.assertFalse(Purchase.objects.filter(user=self.user).exists())
        self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())
        self.assertFalse(InventoryItem.objects.filter(ducky=self.ducky, item=item).exists())
        self.assertFalse(Transaction.objects.filter(wallet=self.wallet).exists())

    def test_disabled_offer_is_rejected_without_charge(self):
        offer, item, level = self.make_offer()
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        offer.is_available = False
        offer.save(update_fields=["is_available"])
        with self.assertRaises(ProductUnavailable):
            purchase_item(self.user, offer.code, operation_key="disabled")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 100)

    def test_permanent_cosmetic_cannot_be_purchased_twice(self):
        offer, item, level = self.make_offer(
            code="cosmetic-one", price=10, pack=1,
            category="COSMETIC", consumable=False, level=None,
        )
        credit_coins(self.user, 100, source="test", operation_key="initial-credit")
        purchase_item(self.user, offer.code, operation_key="cosmetic-first")
        with self.assertRaises(PermanentItemAlreadyOwned):
            purchase_item(self.user, offer.code, operation_key="cosmetic-second")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 90)
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)

    def test_missing_wallet_prevents_purchase(self):
        offer, item, level = self.make_offer()
        self.wallet.delete()
        with self.assertRaises(WalletNotProvisioned):
            purchase_item(self.user, offer.code, operation_key="wallet-missing")
        self.assertEqual(Purchase.objects.count(), 0)

    def test_missing_ducky_prevents_purchase(self):
        offer, item, level = self.make_offer()
        self.ducky.delete()
        with self.assertRaises(BuyerNotProvisioned):
            purchase_item(self.user, offer.code, operation_key="ducky-missing")
        self.assertEqual(Purchase.objects.count(), 0)

    def test_shop_never_sells_historical_outfits(self):
        from apps.shop.models import ShopItem
        outfit = self.historical["PREHISTORICO"]
        
        offer = ShopItem.objects.create(
            code="invalid-historical",
            item=outfit,
            name="Historical",
            price_coins=10,
            )

        credit_coins(
            self.user,
            100,
            source="test",
            operation_key="initial-credit",
            )

        with self.assertRaises(ProductUnavailable):
            purchase_item(
                self.user,
                offer.code,
                operation_key="historical-not-for-sale",
                )
            
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, 100)
