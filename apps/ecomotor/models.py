from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    """Saldo oficial de Duki Coins administrado por DuckyBank."""

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

    def __str__(self):
        return f"Wallet<{self.user_id}>: {self.available_balance}"


class TransactionType(models.TextChoices):
    REWARD = "REWARD", "Recompensa"
    PURCHASE = "PURCHASE", "Compra"
    REFUND = "REFUND", "Reembolso"
    ADJUSTMENT = "ADJUSTMENT", "Ajuste"


class Transaction(models.Model):
    """Movimiento persistente e idempotente del ledger de Duki Coins."""

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
    description = models.CharField(max_length=255, blank=True)
    reference_type = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("wallet", "operation_key"),
                name="unique_wallet_transaction_operation",
            ),
            models.CheckConstraint(
                condition=models.Q(balance_after__gte=0),
                name="transaction_balance_non_negative",
            ),
        ]

    def __str__(self):
        return (
            f"{self.transaction_type} "
            f"{self.amount} "
            f"({self.operation_key})"
        )


class ShopItem(models.Model):
    """
    Oferta comercial de DuckyShop.

    item_code identifica contractualmente el objeto de Inventory.
    No se crea una FK contra Inventory mientras el contrato B/C
    no esté consolidado.
    """

    code = models.CharField(max_length=100, unique=True)
    item_code = models.CharField(max_length=100)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price_coins = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )
    included_quantity = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-featured", "name", "id")

    def __str__(self):
        return f"{self.name} ({self.price_coins} Duki Coins)"


class PurchaseStatus(models.TextChoices):
    COMPLETED = "COMPLETED", "Completada"
    REFUNDED = "REFUNDED", "Reembolsada"


class Purchase(models.Model):
    """Compra realizada por un usuario con idempotencia persistente."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="duki_purchases",
    )
    shop_item = models.ForeignKey(
        ShopItem,
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    operation_key = models.CharField(max_length=255)
    unit_price_coins = models.PositiveBigIntegerField()
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    total_price_coins = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.COMPLETED,
    )
    bank_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.PROTECT,
        related_name="purchase",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "operation_key"),
                name="unique_user_purchase_operation",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price_coins__gt=0),
                name="purchase_unit_price_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="purchase_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(total_price_coins__gt=0),
                name="purchase_total_positive",
            ),
        ]

    def __str__(self):
        return (
            f"Purchase<{self.id}> "
            f"{self.shop_item.code} "
            f"by {self.user_id}"
        )
