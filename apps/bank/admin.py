from django.contrib import admin

from .models import Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "available_balance", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "available_balance", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
    list_filter = ("transaction_type", "source_platform", "issuing_entity")
    search_fields = (
        "operation_key",
        "description",
        "reference_type",
        "reference_id",
    )
    readonly_fields = (
        "wallet",
        "transaction_type",
        "amount",
        "balance_after",
        "operation_key",
        "source_platform",
        "issuing_entity",
        "reference_type",
        "reference_id",
        "description",
        "request_fingerprint",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
