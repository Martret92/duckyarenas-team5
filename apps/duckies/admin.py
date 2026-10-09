
from django.contrib import admin
from .models import Ducky, EquipmentSlot, Item, ItemLevel, InventoryItem, EquippedItem, EquipmentHistory, EvolutionItem, ItemUsage

@admin.register(Ducky)
class DuckyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner")
    search_fields = ("name", "owner__username")

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "rarity", "is_consumable", "is_active")
    list_filter = ("category", "rarity", "is_active")
    search_fields = ("code", "name")

@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("ducky", "item", "item_level", "quantity")
    list_select_related = ("ducky", "item")

for model in (EquipmentSlot, ItemLevel, EquippedItem, EquipmentHistory, EvolutionItem, ItemUsage):
    admin.site.register(model)

