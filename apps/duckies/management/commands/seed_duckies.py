"""Catálogo Duckies idempotente: no crea progreso ni altera XP o Bank."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.ecomotor.models import EvolutionStage, Specialization
from apps.duckies.models import EquipmentSlot, Item, ItemLevel, EvolutionItem, SpecializationItem
from apps.duckies.image_registry import OUTFITS, SPECIALIZATION_OUTFITS, ITEM_IMAGES

HISTORICAL = (
    ("prehistorico", "Prehistórico"), ("griego", "Griego"),
    ("romano", "Romano"), ("medieval", "Medieval"),
    ("renacentista", "Renacentista"),
    ("revolucion_industrial", "Revolución Industrial"), ("siglo_xx", "Siglo XX"),
)
SPECIALIZATIONS = (
    ("DEVELOPER", "developer", "Developer"),
    ("GAMER", "gamer", "Gamer"),
    ("CIBER", "ciber", "Ciberseguridad"),
    ("SISTEMAS", "sistemas", "Sistemas"),
    ("DATA_IA", "data_ia", "Datos e IA"),
)
TACTICAL = (
    ("smoke", "Cortina de Humo", "ATTACK"),
    ("false_options", "Inflador de Opciones", "ATTACK"),
    ("overclock", "Acelerador de Tensión", "ATTACK"),
    ("firewall", "Escudo Firewall", "DEFENSE"),
    ("noise_filter", "Analizador de Datos", "HINT"),
    ("slow_time", "Amortiguador de Tiempo", "DEFENSE"),
)

class Command(BaseCommand):
    help = "Registra 7 vestimentas históricas, 5 especializaciones (si existen) y objetos tácticos."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        stages = list(EvolutionStage.objects.order_by("ordinal"))
        if len(stages) != 7 or [s.ordinal for s in stages] != list(range(1, 8)):
            raise CommandError("Ecomotor debe tener las siete etapas ordinales 1-7.")
        for stage, (slug, name) in zip(stages, HISTORICAL):
            code = f"outfit_{slug}"
            item, _ = Item.objects.get_or_create(code=code, defaults={
                "name": f"Vestimenta {name}", "category": Item.HISTORICAL,
                "consumable": False, "image_path": OUTFITS[slug]["male"],
            })
            if item.category != Item.HISTORICAL:
                raise CommandError(f"Categoría incorrecta para {code}.")
            link, _ = EvolutionItem.objects.get_or_create(stage=stage, defaults={"item": item})
            if link.item_id != item.pk:
                raise CommandError(f"Etapa {stage.code} ya asociada a otro ítem.")

        slot, _ = EquipmentSlot.objects.get_or_create(code="TACTICAL", defaults={"name": "Ranura táctica"})
        for code, name, category in TACTICAL:
            item, _ = Item.objects.get_or_create(code=code, defaults={
                "name": name, "category": category, "slot": slot,
                "consumable": True, "image_path": ITEM_IMAGES[code],
            })
            if item.category != category:
                raise CommandError(f"Categoría incorrecta para {code}.")
            for level in (1, 2, 3):
                ItemLevel.objects.get_or_create(item=item, level=level, defaults={
                    "effect_code": "PENDING_QUIZ_CONTRACT", "effect_value": "TBD",
                })

        missing = []
        for code, slug, name in SPECIALIZATIONS:
            specialization = Specialization.objects.filter(code=code).first()
            if specialization is None:
                missing.append(code)
                self.stdout.write(self.style.WARNING(f"Especialización {code} no registrada en Ecomotor. Se omite."))
                continue
            item_code = f"specialization_{slug}"
            item, _ = Item.objects.get_or_create(code=item_code, defaults={
                "name": f"Vestimenta {name}", "category": Item.SPECIALIZATION,
                "consumable": False, "image_path": SPECIALIZATION_OUTFITS[slug]["male"],
            })
            if item.category != Item.SPECIALIZATION:
                raise CommandError(f"Categoría incorrecta para {item_code}.")
            mapping, _ = SpecializationItem.objects.get_or_create(
                specialization=specialization, defaults={"item": item}
            )
            if mapping.item_id != item.pk:
                raise CommandError(f"Especialización {code} asociada a otro ítem.")
        self.stdout.write(self.style.SUCCESS(
            f"Catálogo Duckies procesado: 7 históricos, 6 tácticos, 18 niveles y {5-len(missing)} especializaciones vinculadas."
        ))
        if missing:
            self.stdout.write(f"Pendientes en Ecomotor: {', '.join(missing)}")
