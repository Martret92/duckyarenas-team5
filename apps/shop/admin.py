from django.contrib import admin

from .models import Purchase, ShopItem


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "item",
        "item_level",
        "price_coins",
        "included_quantity",
        "is_available",
        "featured",
    )
    list_filter = ("is_available", "featured", "item__category")
    search_fields = ("code", "name", "item__code", "item__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "user",
        "shop_item",
        "quantity",
        "total_price_coins",
        "status",
        "operation_key",
    )
    list_filter = ("status",)
    search_fields = (
        "operation_key",
        "request_fingerprint",
        "user__username",
        "shop_item__code",
        "delivery_reference",
    )
    readonly_fields = (
        "user",
        "shop_item",
        "operation_key",
        "request_fingerprint",
        "unit_price_coins",
        "quantity",
        "total_price_coins",
        "status",
        "bank_transaction",
        "delivery_reference",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
