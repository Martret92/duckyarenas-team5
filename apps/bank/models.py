from django.conf import settings
from django.db import models
from django.db.models import Q


class Wallet(models.Model):
    """Local DuckyArena wallet; global balance ownership remains a Core decision."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="duki_wallet",
    )
    available_balance = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        constraints = [
            models.CheckConstraint(
                condition=Q(available_balance__gte=0),
                name="bank_wallet_bal_nonneg",
            ),
        ]

    def __str__(self):
        return f"Wallet<{self.user_id}>: {self.available_balance}"


class TransactionType(models.TextChoices):
    REWARD = "REWARD", "Reward"
    PURCHASE = "PURCHASE", "Purchase"
    REFUND = "REFUND", "Refund"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class Transaction(models.Model):
    """Immutable ledger movement with persistent idempotency evidence."""

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    amount = models.BigIntegerField()
    balance_after = models.PositiveBigIntegerField()
    operation_key = models.CharField(max_length=255)
    source_platform = models.CharField(max_length=100)
    issuing_entity = models.CharField(max_length=100)
    reference_type = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)
    request_fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("wallet", "operation_key"),
                name="bank_txn_op_unique",
            ),
            models.CheckConstraint(
                condition=~Q(amount=0),
                name="bank_txn_amt_nonzero",
            ),
            models.CheckConstraint(
                condition=Q(balance_after__gte=0),
                name="bank_txn_bal_nonneg",
            ),
            models.CheckConstraint(
                condition=~Q(operation_key=""),
                name="bank_txn_key_nonempty",
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} ({self.operation_key})"
