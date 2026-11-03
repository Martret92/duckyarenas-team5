from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Transaction, TransactionType, Wallet
from .services import (
    IdempotencyConflict,
    InsufficientFunds,
    InvalidAmount,
    WalletNotProvisioned,
    adjust_wallet,
    credit_coins,
    debit_coins,
    transaction_history,
    wallet_summary,
)


class BankServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="bank-user")
        self.wallet = Wallet.objects.create(user=self.user)

    def test_wallet_starts_at_zero(self):
        self.assertEqual(self.wallet.available_balance, 0)

    def test_missing_wallet_requires_core_provisioning(self):
        unprovisioned = get_user_model().objects.create_user(username="unprovisioned-user")
        with self.assertRaises(WalletNotProvisioned):
            credit_coins(
                unprovisioned,
                100,
                source="rewards",
                operation_key="reward-unprovisioned",
            )

    def test_credit_is_idempotent(self):
        first = credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="reward-002",
            reference_type="reward",
            reference_id="fact-002",
        )
        replay = credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="reward-002",
            reference_type="reward",
            reference_id="fact-002",
        )

        self.assertTrue(first.created)
        self.assertTrue(replay.already_applied)
        self.assertEqual(first.transaction.pk, replay.transaction.pk)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)

    def test_same_key_with_different_semantic_reference_conflicts(self):
        credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="reward-003",
            reference_type="reward",
            reference_id="fact-003",
        )

        with self.assertRaises(IdempotencyConflict):
            credit_coins(
                self.user,
                100,
                source="rewards",
                operation_key="reward-003",
                reference_type="reward",
                reference_id="different-fact",
            )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 100)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_same_key_with_different_source_conflicts(self):
        credit_coins(
            self.user,
            100,
            source="rewards",
            operation_key="operation-shared",
        )

        with self.assertRaises(IdempotencyConflict):
            credit_coins(
                self.user,
                100,
                source="admin",
                operation_key="operation-shared",
            )

    def test_debit_is_idempotent(self):
        credit_coins(
            self.user,
            100,
            source="test",
            operation_key="debit-replay-credit",
        )

        first = debit_coins(
            self.user,
            30,
            source="shop",
            operation_key="debit-replay-key",
            reference_type="purchase",
            reference_id="debit-replay-reference",
        )
        replay = debit_coins(
            self.user,
            30,
            source="shop",
            operation_key="debit-replay-key",
            reference_type="purchase",
            reference_id="debit-replay-reference",
        )

        self.assertTrue(first.created)
        self.assertFalse(replay.created)
        self.assertEqual(first.transaction.pk, replay.transaction.pk)
        self.assertEqual(first.transaction.amount, -30)
        self.assertEqual(
            Wallet.objects.get(user=self.user).available_balance,
            70,
        )
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertEqual(
            Transaction.objects.filter(
                transaction_type=TransactionType.PURCHASE,
            ).count(),
            1,
        )

    def test_debit_uses_signed_ledger_amount_and_rejects_insufficient_funds(self):
        credit_coins(
            self.user,
            50,
            source="rewards",
            operation_key="reward-004",
        )
        debit = debit_coins(
            self.user,
            30,
            source="shop",
            operation_key="purchase-004",
            reference_type="purchase_operation",
            reference_id="purchase-key-004",
        )

        self.assertEqual(debit.transaction.amount, -30)
        self.assertEqual(debit.transaction.transaction_type, TransactionType.PURCHASE)
        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 20)

        with self.assertRaises(InsufficientFunds):
            debit_coins(
                self.user,
                21,
                source="shop",
                operation_key="purchase-005",
            )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 20)
        self.assertEqual(Transaction.objects.count(), 2)

    def test_zero_amount_is_rejected(self):
        with self.assertRaises(InvalidAmount):
            credit_coins(
                self.user,
                0,
                source="rewards",
                operation_key="reward-zero",
            )

    def test_adjustment_supports_both_signs_and_requires_reason(self):
        credit_coins(
            self.user,
            50,
            source="rewards",
            operation_key="reward-006",
        )
        adjust_wallet(
            self.user,
            -10,
            operation_key="adjustment-001",
            description="Approved correction",
        )
        adjust_wallet(
            self.user,
            5,
            operation_key="adjustment-002",
            description="Approved correction",
        )

        self.assertEqual(Wallet.objects.get(user=self.user).available_balance, 45)
        self.assertEqual(
            Transaction.objects.filter(transaction_type=TransactionType.ADJUSTMENT).count(),
            2,
        )

    def test_summary_and_history(self):
        credit_coins(
            self.user,
            80,
            source="rewards",
            operation_key="reward-007",
        )
        debit_coins(
            self.user,
            25,
            source="shop",
            operation_key="purchase-007",
        )

        self.assertEqual(
            wallet_summary(self.user),
            {"available_balance": 55, "total_earned": 80, "total_spent": 25},
        )
        self.assertEqual(len(list(transaction_history(self.user))), 2)
        self.assertEqual(
            len(list(transaction_history(self.user, source="shop"))),
            1,
        )

    def test_database_rejects_zero_ledger_amount(self):
        wallet = self.wallet
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type=TransactionType.ADJUSTMENT,
                    amount=0,
                    balance_after=0,
                    operation_key="invalid-zero",
                    source_platform="test",
                    issuing_entity="test",
                    request_fingerprint="0" * 64,
                )
