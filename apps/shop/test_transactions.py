from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from apps.bank.models import Transaction, TransactionType, Wallet
from apps.bank.services import credit_coins
from apps.duckies.models import Ducky, Item, ItemLevel, ItemGrant

from .models import Purchase, ShopItem
from .services import DeliveryRejected, purchase_item


class ShopTransactionBoundaryTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="shop-transaction-user")
        self.ducky = Ducky.objects.create(user=self.user, sex="male")
        Wallet.objects.create(user=self.user)
        self.item = Item.objects.create(
            code="transaction-smoke",
            name="Transaction smoke",
            category=Item.ATTACK,
            consumable=True,
            is_active=True,
        )
        self.level = ItemLevel.objects.create(
            item=self.item,
            level=1,
            effect_code="SMOKE",
            effect_value="5",
        )
        self.offer = ShopItem.objects.create(
            code="transaction-smoke-sku",
            item=self.item,
            item_level=self.level,
            name="Transaction smoke pack",
            price_coins=20,
            included_quantity=2,
        )
        credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="transaction-test-credit",
        )

    @patch("apps.shop.services.grant_item", side_effect=ValueError("simulated delivery error"))
    def test_delivery_error_rolls_back_all_local_purchase_effects(self, _grant_mock):
        with self.assertRaises(DeliveryRejected):
            purchase_item(
                self.user,
                self.offer.code,
                operation_key="transaction-failure-order",
                quantity=2,
            )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)
        self.assertFalse(Purchase.objects.filter(user=self.user).exists())
        self.assertFalse(
            Transaction.objects.filter(
                wallet__user=self.user,
                transaction_type=TransactionType.PURCHASE,
            ).exists()
        )
        self.assertFalse(ItemGrant.objects.filter(ducky=self.ducky).exists())
