"""Create the initial, permanent tactical catalog for DuckyArena Shop.

Usage: python manage.py seed_shop_catalog

Existing catalog entries are validated, never silently overwritten. Prices are
initial defaults and can be edited by administrators after seeding.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.duckies.models import EquipmentSlot, Item, ItemLevel
from apps.shop.models import ShopItem


# Prices are initial proposals in Ducky Coins, not fixed game-balance rules.
CATALOG = (
    {
        "code": "shop_smoke_screen",
        "name": "Cortina de Humo",
        "category": Item.ATTACK,
        "description": "Interferencia visual temporal para el rival.",
        "prices": (50, 100, 150),
    },
    {
        "code": "shop_option_inflator",
        "name": "Inflador de Opciones",
        "category": Item.ATTACK,
        "description": "Añade opciones distractoras al rival durante la partida.",
        "prices": (60, 120, 180),
    },
    {
        "code": "shop_overclock",
        "name": "Overclock",
        "category": Item.ATTACK,
        "description": "Interferencia temporal sobre el ritmo de respuesta rival.",
        "prices": (70, 140, 210),
    },
    {
        "code": "shop_firewall_shield",
        "name": "Escudo Firewall",
        "category": Item.DEFENSE,
        "description": "Protección frente a ataques del rival.",
        "prices": (50, 100, 150),
    },
    {
        "code": "shop_noise_filter",
        "name": "Filtro de Ruido",
        "category": Item.DEFENSE,
        "description": "Defensa frente a interferencias durante la partida.",
        "prices": (60, 120, 180),
    },
    {
        "code": "shop_slow_time",
        "name": "Slow-Time",
        "category": Item.DEFENSE,
        "description": "Ventaja defensiva relacionada con el tiempo de respuesta.",
        "prices": (70, 140, 210),
    },
)

SLOTS = {
    Item.ATTACK: ("ATTACK", "Ataque"),
    Item.DEFENSE: ("DEFENSE", "Defensa"),
}


class Command(BaseCommand):
    help = "Crea el catálogo inicial permanente de 18 ofertas tácticas de Shop."

    @transaction.atomic
    def handle(self, *args, **options):
        counts = {"slots": 0, "items": 0, "levels": 0, "offers": 0}

        slots = {}
        for category, (code, name) in SLOTS.items():
            slot, created = EquipmentSlot.objects.get_or_create(
                code=code,
                defaults={"name": name, "is_main_piece": False},
            )
            if slot.is_main_piece:
                raise CommandError(
                    f"La ranura {code!r} ya existe como pieza principal; "
                    "no se puede utilizar para objetos tácticos."
                )
            slots[category] = slot
            counts["slots"] += int(created)

        for product in CATALOG:
            code = product["code"]
            category = product["category"]
            slot = slots[category]
            item, created = Item.objects.get_or_create(
                code=code,
                defaults={
                    "name": product["name"],
                    "description": product["description"],
                    "category": category,
                    "rarity": "COMMON",
                    "slot": slot,
                    "consumable": True,
                    "is_active": True,
                },
            )
            if (
                item.category != category
                or item.slot_id != slot.pk
                or not item.consumable
            ):
                raise CommandError(
                    f"El Item {code!r} ya existe con categoría, ranura "
                    "o tipo consumible incompatible. No se ha modificado."
                )
            counts["items"] += int(created)

            for level_number, price in enumerate(product["prices"], start=1):
                level, level_created = ItemLevel.objects.get_or_create(
                    item=item,
                    level=level_number,
                    defaults={
                        # Effects are intentionally left unconfigured until
                        # the battle engine's official contract is defined.
                        "effect_code": "",
                        "effect_value": "",
                    },
                )
                counts["levels"] += int(level_created)

                sku = f"{code}_lvl{level_number}"
                offer, offer_created = ShopItem.objects.get_or_create(
                    code=sku,
                    defaults={
                        "item": item,
                        "item_level": level,
                        "name": f"{product['name']} - Nivel {level_number}",
                        "description": product["description"],
                        "price_coins": price,
                        "included_quantity": 1,
                        "is_available": True,
                        "featured": False,
                    },
                )
                if (
                    offer.item_id != item.pk
                    or offer.item_level_id != level.pk
                    or offer.included_quantity != 1
                ):
                    raise CommandError(
                        f"El SKU {sku!r} ya existe con una configuración "
                        "incompatible. No se ha modificado."
                    )
                # Validate against Shop's business rules without changing
                # an existing price, name, description or availability.
                offer.full_clean()
                counts["offers"] += int(offer_created)

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogo Shop preparado: "
                f"{counts['slots']} ranuras, {counts['items']} objetos, "
                f"{counts['levels']} niveles y {counts['offers']} ofertas nuevas. "
                "Catálogo previsto: 18 ofertas tácticas."
            )
        )
