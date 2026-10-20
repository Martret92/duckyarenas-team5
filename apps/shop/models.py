from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.duckies.models import Item


class ShopItem(models.Model):
    """Commercial SKU for a digital Duckies item or item-level variant."""

    code = models.CharField(max_length=100, unique=True)
    item = models.ForeignKey(
        "duckies.Item",
        on_delete=models.PROTECT,
        related_name="shop_offers",
    )
    item_level = models.ForeignKey(
        "duckies.ItemLevel",
        on_delete=models.PROTECT,
        related_name="shop_offers",
        null=True,
        blank=True,
    )
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
        constraints = [
            models.CheckConstraint(
                condition=Q(price_coins__gt=0),
                name="shop_item_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(included_quantity__gt=0),
                name="shop_item_qty_positive",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.item_id:
            return
        category = self.item.category
        if category == Item.HISTORICAL:
            raise ValidationError({"item": "Historical items are not sold in Shop V1."})
        if category in (Item.ATTACK, Item.DEFENSE) and not self.item_level_id:
            raise ValidationError({
                "item_level": "Attack and defense offers require an item level."
            })
        if category not in (Item.ATTACK, Item.DEFENSE) and self.item_level_id:
            raise ValidationError({"item_level": "This item category cannot use an item level."})
        if self.item_level_id and self.item_level.item_id != self.item_id:
            raise ValidationError({"item_level": "The selected level belongs to another item."})
        if category in (Item.ATTACK, Item.DEFENSE, Item.HINT) and not self.item.consumable:
            raise ValidationError({"item": "Attack, defense, and hint items must be consumable."})
        if category == Item.COSMETIC and self.item.consumable:
            raise ValidationError({"item": "Cosmetic items must be permanent."})
        if not self.item.consumable and self.included_quantity != 1:
            raise ValidationError({
                "included_quantity": "Permanent items must be sold one unit per pack."
            })

    def __str__(self):
        return f"{self.code}: {self.name} ({self.price_coins} DukiCoins)"


class PurchaseStatus(models.TextChoices):
    COMPLETED = "COMPLETED", "Completed"
    REFUNDED = "REFUNDED", "Refunded"


class Purchase(models.Model):
    """Completed purchase record; V1 does not expose automatic refunds."""

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
    request_fingerprint = models.CharField(max_length=64)
    unit_price_coins = models.PositiveBigIntegerField()
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price_coins = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.COMPLETED,
    )
    bank_transaction = models.OneToOneField(
        "bank.Transaction",
        on_delete=models.PROTECT,
        related_name="purchase",
    )
    delivery_reference = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "operation_key"),
                name="shop_purchase_op_unique",
            ),
            models.CheckConstraint(
                condition=Q(unit_price_coins__gt=0),
                name="shop_pur_unit_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="shop_pur_qty_positive",
            ),
            models.CheckConstraint(
                condition=Q(total_price_coins__gt=0),
                name="shop_pur_total_positive",
            ),
            models.CheckConstraint(
                condition=Q(total_price_coins=F("unit_price_coins") * F("quantity")),
                name="shop_pur_total_matches",
            ),
        ]

    def __str__(self):
        return f"Purchase<{self.pk}> {self.shop_item.code} by {self.user_id}"
