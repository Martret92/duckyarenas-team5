from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import (
    Purchase,
    PurchaseStatus,
    ShopItem,
    Transaction,
    TransactionType,
    Wallet,
)
from .services import (
    IdempotencyConflict,
    InsufficientFunds,
    ProductUnavailable,
    adjust_wallet,
    credit_wallet,
    debit_wallet,
    purchase_item,
    refund_purchase,
    transaction_history,
    wallet_summary,
)


class BankServiceTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="bank-user"
        )

    def test_wallet_starts_at_zero(self):
        wallet = Wallet.objects.create(
            user=self.user
        )

        self.assertEqual(
            wallet.available_balance,
            0,
        )

    def test_credit_updates_balance(self):
        result = credit_wallet(
            self.user,
            100,
            operation_key="reward:001",
            source_platform="test",
            issuing_entity="Rewards",
        )

        wallet = Wallet.objects.get(
            user=self.user
        )

        self.assertTrue(result.created)
        self.assertEqual(
            wallet.available_balance,
            100,
        )
        self.assertEqual(
            result.transaction.amount,
            100,
        )
        self.assertEqual(
            result.transaction.balance_after,
            100,
        )

    def test_credit_is_idempotent(self):
        first = credit_wallet(
            self.user,
            100,
            operation_key="reward:002",
        )

        second = credit_wallet(
            self.user,
            100,
            operation_key="reward:002",
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)

        self.assertEqual(
            Transaction.objects.count(),
            1,
        )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            100,
        )

    def test_operation_key_conflict(self):
        credit_wallet(
            self.user,
            100,
            operation_key="reward:003",
        )

        with self.assertRaises(
            IdempotencyConflict
        ):
            credit_wallet(
                self.user,
                200,
                operation_key="reward:003",
            )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            100,
        )

    def test_insufficient_funds(self):
        credit_wallet(
            self.user,
            50,
            operation_key="reward:004",
        )

        with self.assertRaises(
            InsufficientFunds
        ):
            debit_wallet(
                self.user,
                51,
                operation_key="purchase:001",
            )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            50,
        )

        self.assertEqual(
            Transaction.objects.count(),
            1,
        )

    def test_adjustment(self):
        credit_wallet(
            self.user,
            50,
            operation_key="reward:005",
        )

        adjust_wallet(
            self.user,
            -20,
            operation_key="adjustment:001",
            description="Corrección",
        )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            30,
        )

    def test_summary_and_history(self):
        credit_wallet(
            self.user,
            80,
            operation_key="reward:006",
        )

        debit_wallet(
            self.user,
            30,
            operation_key="purchase:002",
        )

        summary = wallet_summary(
            self.user
        )

        history = list(
            transaction_history(
                self.user
            )
        )

        self.assertEqual(
            summary["available_balance"],
            50,
        )

        self.assertEqual(
            summary["total_earned"],
            80,
        )

        self.assertEqual(
            summary["total_spent"],
            30,
        )

        self.assertEqual(
            len(history),
            2,
        )


class ShopPurchaseTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="shop-user"
        )

        self.item = ShopItem.objects.create(
            code="test-item",
            item_code="inventory-item-001",
            name="Objeto de prueba",
            description="Producto provisional",
            price_coins=30,
        )

        credit_wallet(
            self.user,
            100,
            operation_key="reward:shop",
        )

    def test_purchase_charges_server_price(self):
        deliveries = []

        purchase = purchase_item(
            self.user,
            self.item,
            operation_key="purchase:001",
            deliver=lambda value: deliveries.append(
                value.pk
            ),
        )

        wallet = Wallet.objects.get(
            user=self.user
        )

        self.assertEqual(
            wallet.available_balance,
            70,
        )

        self.assertEqual(
            purchase.total_price_coins,
            30,
        )

        self.assertEqual(
            purchase.bank_transaction.amount,
            -30,
        )

        self.assertEqual(
            deliveries,
            [purchase.pk],
        )

    def test_purchase_is_idempotent(self):
        deliveries = []

        first = purchase_item(
            self.user,
            self.item,
            operation_key="purchase:002",
            deliver=lambda value: deliveries.append(
                value.pk
            ),
        )

        second = purchase_item(
            self.user,
            self.item,
            operation_key="purchase:002",
            deliver=lambda value: deliveries.append(
                value.pk
            ),
        )

        self.assertEqual(
            first.pk,
            second.pk,
        )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            70,
        )

        self.assertEqual(
            Transaction.objects.filter(
                transaction_type=TransactionType.PURCHASE
            ).count(),
            1,
        )

        self.assertEqual(
            deliveries,
            [first.pk],
        )

    def test_unavailable_item_is_rejected(self):
        self.item.is_available = False

        self.item.save(
            update_fields=["is_available"]
        )

        with self.assertRaises(
            ProductUnavailable
        ):
            purchase_item(
                self.user,
                self.item,
                operation_key="purchase:003",
                deliver=lambda value: None,
            )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            100,
        )

    def test_delivery_failure_rolls_back(self):
        def fail(_purchase):
            raise RuntimeError(
                "Inventory no disponible"
            )

        with self.assertRaises(
            RuntimeError
        ):
            purchase_item(
                self.user,
                self.item,
                operation_key="purchase:004",
                deliver=fail,
            )

        self.assertFalse(
            Purchase.objects.exists()
        )

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            100,
        )

        self.assertEqual(
            Transaction.objects.filter(
                transaction_type=TransactionType.PURCHASE
            ).count(),
            0,
        )

    def test_refund_is_idempotent(self):
        purchase = purchase_item(
            self.user,
            self.item,
            operation_key="purchase:005",
            deliver=lambda value: None,
        )

        first = refund_purchase(
            purchase,
            operation_key="refund:001",
        )

        second = refund_purchase(
            purchase,
            operation_key="refund:001",
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)

        self.assertEqual(
            Wallet.objects.get(
                user=self.user
            ).available_balance,
            100,
        )

        self.assertEqual(
            Purchase.objects.get(
                pk=purchase.pk
            ).status,
            PurchaseStatus.REFUNDED,
        )

        self.assertEqual(
            Transaction.objects.filter(
                transaction_type=TransactionType.REFUND
            ).count(),
            1,
        )
