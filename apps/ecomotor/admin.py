from django.contrib import admin

from .models import (
    Purchase,
    ShopItem,
    Transaction,
    Wallet,
)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "available_balance",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "wallet",
        "transaction_type",
        "amount",
        "balance_after",
        "operation_key",
    )
    list_filter = (
        "transaction_type",
        "source_platform",
        "issuing_entity",
    )
    search_fields = (
        "operation_key",
        "description",
        "reference_id",
    )
    readonly_fields = ("created_at",)


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "item_code",
        "price_coins",
        "included_quantity",
        "is_available",
        "featured",
    )
    list_filter = (
        "is_available",
        "featured",
    )
    search_fields = (
        "code",
        "item_code",
        "name",
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "user",
        "shop_item",
        "total_price_coins",
        "status",
        "operation_key",
    )
    list_filter = ("status",)
    search_fields = (
        "operation_key",
        "user__username",
        "shop_item__code",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
