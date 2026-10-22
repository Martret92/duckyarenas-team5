from django.contrib import admin
from .models import Ducky,Item,ItemLevel,InventoryItem,EvolutionItem,ItemGrant,ItemUsage,EquipmentSlot,EquippedItem,EquipmentHistory,SpecializationItem
admin.site.register(Ducky)
admin.site.register(Item)
admin.site.register(ItemLevel)
admin.site.register(InventoryItem)
admin.site.register(EvolutionItem)
admin.site.register(ItemGrant)
admin.site.register(ItemUsage)
admin.site.register(EquipmentSlot)
admin.site.register(EquippedItem)
admin.site.register(EquipmentHistory)
admin.site.register(SpecializationItem)