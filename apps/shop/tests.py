from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.bank.models import Transaction, TransactionType, Wallet
from apps.bank.services import InsufficientFunds, credit_coins
from apps.duckies.models import Ducky, InventoryItem, Item, ItemLevel
from apps.duckies.models import ItemGrant

from .models import Purchase, ShopItem
from .services import (
    DeliveryRejected,
    InvalidProductConfiguration,
    PermanentItemAlreadyOwned,
    ProductUnavailable,
    PurchaseIdempotencyConflict,
    purchase_item,
)


class ShopPurchaseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="shop-user")
        self.ducky = Ducky.objects.create(user=self.user, sex="male")
        Wallet.objects.create(user=self.user)
        self.attack = Item.objects.create(
            code="attack-smoke",
            name="Smoke",
            category=Item.ATTACK,
            consumable=True,
            is_active=True,
        )
        self.attack_level = ItemLevel.objects.create(
            item=self.attack,
            level=2,
            effect_code="SMOKE",
            effect_value="5",
        )
        self.offer = ShopItem.objects.create(
            code="smoke-pack-3",
            item=self.attack,
            item_level=self.attack_level,
            name="Smoke pack",
            price_coins=20,
            included_quantity=3,
        )
        credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="shop-test-initial-credit",
        )

    def test_purchase_uses_server_price_and_pack_quantity(self):
        purchase = purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-001",
            quantity=2,
        )

        wallet = Wallet.objects.get(user=self.user)
        inventory = InventoryItem.objects.get(
            ducky=self.ducky,
            item=self.attack,
            item_level=self.attack_level,
        )
        grant = ItemGrant.objects.get(pk=int(purchase.delivery_reference.split(":", 1)[1]))

        self.assertEqual(purchase.unit_price_coins, 20)
        self.assertEqual(purchase.quantity, 2)
        self.assertEqual(purchase.total_price_coins, 40)
        self.assertEqual(purchase.bank_transaction.amount, -40)
        self.assertEqual(wallet.available_balance, 60)
        self.assertEqual(inventory.quantity, 6)
        self.assertEqual(grant.quantity, 6)
        self.assertEqual(purchase.status, "COMPLETED")


    def test_repeat_consumable_purchases_accumulate_inventory(self):
        purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-accumulate-1",
            quantity=1,
        )
        purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-accumulate-2",
            quantity=2,
        )

        inventory = InventoryItem.objects.get(
            ducky=self.ducky,
            item=self.attack,
            item_level=self.attack_level,
        )
        self.assertEqual(inventory.quantity, 9)
        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 40)
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 2)

    def test_replay_returns_original_after_offer_is_disabled(self):
        first = purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-002",
            quantity=1,
        )
        self.offer.is_available = False
        self.offer.save(update_fields=("is_available", "updated_at"))

        replay = purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-002",
            quantity=1,
        )

        self.assertEqual(first.pk, replay.pk)
        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 80)
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(ItemGrant.objects.count(), 1)
        self.assertEqual(
            Transaction.objects.filter(transaction_type=TransactionType.PURCHASE).count(),
            1,
        )

        inventory = InventoryItem.objects.get(
            ducky=self.ducky,
            item=self.attack,
            item_level=self.attack_level,
        )
        self.assertEqual(inventory.quantity, self.offer.included_quantity)

    def test_reusing_key_with_different_quantity_conflicts(self):
        purchase_item(
            self.user,
            self.offer.code,
            operation_key="shop-order-003",
            quantity=1,
        )

        with self.assertRaises(PurchaseIdempotencyConflict):
            purchase_item(
                self.user,
                self.offer.code,
                operation_key="shop-order-003",
                quantity=2,
            )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 80)
        self.assertEqual(Purchase.objects.count(), 1)

    def test_insufficient_funds_does_not_deliver_or_persist_purchase(self):
        another_user = get_user_model().objects.create_user(username="poor-user")
        Ducky.objects.create(user=another_user, sex="female")
        Wallet.objects.create(user=another_user)

        with self.assertRaises(InsufficientFunds):
            purchase_item(
                another_user,
                self.offer.code,
                operation_key="shop-order-poor",
                quantity=1,
            )

        self.assertFalse(Purchase.objects.filter(user=another_user).exists())
        self.assertFalse(ItemGrant.objects.filter(ducky__user=another_user).exists())
        self.assertEqual(Wallet.objects.get(user=another_user).available_balance, 0)

    @patch("apps.shop.services.grant_item", side_effect=ValueError("simulated delivery failure"))
    def test_delivery_failure_rolls_back_debit_and_purchase(self, _grant_mock):
        with self.assertRaises(DeliveryRejected):
            purchase_item(
                self.user,
                self.offer.code,
                operation_key="shop-order-delivery-failure",
            )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)
        self.assertFalse(
            Purchase.objects.filter(operation_key="shop-order-delivery-failure").exists()
        )
        self.assertFalse(
            Transaction.objects.filter(
                wallet__user=self.user,
                transaction_type=TransactionType.PURCHASE,
            ).exists()
        )

    def test_historical_items_are_not_sold(self):
        historical = Item.objects.create(
            code="historical-hood",
            name="Historical hood",
            category=Item.HISTORICAL,
            consumable=False,
            is_active=True,
        )
        offer = ShopItem.objects.create(
            code="historical-hood-sku",
            item=historical,
            name="Historical hood",
            price_coins=10,
        )

        with self.assertRaises(ProductUnavailable):
            purchase_item(self.user, offer.code, operation_key="historical-order")

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)

    def test_specialization_items_cannot_be_offered_or_purchased(self):
        with patch.object(Item, "SPECIALIZATION", "SPECIALIZATION", create=True):
            specialization = Item.objects.create(
                code="specialization-cyber",
                name="Cyber specialization",
                category=Item.SPECIALIZATION,
                consumable=False,
                is_active=True,
            )
            offer = ShopItem.objects.create(
                code="specialization-cyber-sku",
                item=specialization,
                name="Cyber specialization",
                price_coins=10,
            )

            with self.assertRaises(ValidationError):
                offer.full_clean()

            with self.assertRaises(InvalidProductConfiguration):
                purchase_item(
                    self.user,
                    offer.code,
                    operation_key="specialization-order",
                )

            self.assertEqual(
                Wallet.objects.get(user=self.user).available_balance,
                100,
            )
            self.assertFalse(Purchase.objects.filter(shop_item=offer).exists())

    def test_invalid_item_level_for_another_item_is_rejected(self):
        other = Item.objects.create(
            code="other-attack",
            name="Other attack",
            category=Item.ATTACK,
            consumable=True,
            is_active=True,
        )
        invalid_offer = ShopItem.objects.create(
            code="invalid-variant-sku",
            item=other,
            item_level=self.attack_level,
            name="Invalid variant",
            price_coins=10,
        )

        with self.assertRaises(InvalidProductConfiguration):
            purchase_item(self.user, invalid_offer.code, operation_key="bad-variant-order")

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)

    def test_permanent_item_cannot_be_bought_twice(self):
        cosmetic = Item.objects.create(
            code="blue-hat",
            name="Blue hat",
            category=Item.COSMETIC,
            consumable=False,
            is_active=True,
        )
        cosmetic_offer = ShopItem.objects.create(
            code="blue-hat-sku",
            item=cosmetic,
            name="Blue hat",
            price_coins=15,
        )

        purchase_item(self.user, cosmetic_offer.code, operation_key="blue-hat-order-1")
        with self.assertRaises(PermanentItemAlreadyOwned):
            purchase_item(self.user, cosmetic_offer.code, operation_key="blue-hat-order-2")

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 85)
        self.assertEqual(Purchase.objects.filter(shop_item=cosmetic_offer).count(), 1)

    def test_purchase_rejects_quantity_above_supported_integer_range(self):
        with self.assertRaisesRegex(ValueError, "supported range"):
            purchase_item(
                self.user,
                "SKU-TEST",
                operation_key="quantity-above-int32",
                quantity=2**31,
            )
