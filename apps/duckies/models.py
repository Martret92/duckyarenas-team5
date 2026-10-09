
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F


class Category(models.TextChoices):
    HISTORICAL = "HISTORICAL", "Pieza histórica"
    COSMETIC = "COSMETIC", "Cosmético"
    ATTACK = "ATTACK", "Ataque"
    DEFENSE = "DEFENSE", "Defensa"
    HINT = "HINT", "Pista"


class Rarity(models.TextChoices):
    COMMON = "COMMON", "Común"
    RARE = "RARE", "Raro"
    EPIC = "EPIC", "Épico"
    LEGENDARY = "LEGENDARY", "Legendario"


class EffectType(models.TextChoices):
    EXTRA_QUESTIONS = "EXTRA_QUESTIONS", "Preguntas extra"
    TIME_ACCELERATION = "TIME_ACCELERATION", "Aceleración de tiempo"
    SMOKE = "SMOKE", "Nube de humo"
    SHIELD = "SHIELD", "Escudo"
    EXTRA_TIME = "EXTRA_TIME", "Tiempo extra"
    FIFTY_FIFTY = "FIFTY_FIFTY", "Eliminar respuestas"
    EXTRA_HINT = "EXTRA_HINT", "Pista adicional"


class Ducky(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ducky")
    name = models.CharField(max_length=50, default="Ducky")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.owner_id})"


class EquipmentSlot(models.Model):
    # No se crean seis slots ficticios: los códigos oficiales siguen pendientes.
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=80)
    is_main_piece = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self):
        return self.name


class Item(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    rarity = models.CharField(max_length=12, choices=Rarity.choices, default=Rarity.COMMON)
    equipment_slot = models.ForeignKey(EquipmentSlot, on_delete=models.PROTECT, related_name="items", null=True, blank=True)
    image = models.ImageField(upload_to="ducky_items/", null=True, blank=True)
    is_consumable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.category in (Category.HISTORICAL, Category.COSMETIC) and self.is_consumable:
            raise ValidationError("Las piezas históricas y los cosméticos son permanentes.")
        if self.category in (Category.ATTACK, Category.DEFENSE, Category.HINT) and not self.is_consumable:
            raise ValidationError("Ataques, defensas y pistas deben ser consumibles.")
        if self.category == Category.HISTORICAL and (not self.equipment_slot_id or not self.equipment_slot.is_main_piece):
            raise ValidationError("Una pieza histórica requiere una zona principal.")
        if self.equipment_slot_id and self.category not in (Category.HISTORICAL, Category.COSMETIC):
            raise ValidationError("Solo las piezas y cosméticos pueden ocupar una zona.")

    def __str__(self):
        return self.name


class ItemLevel(models.Model):
    # Los parámetros definitivos de combate se acordarán con los equipos de juegos.
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="levels")
    level = models.PositiveSmallIntegerField()
    effect_code = models.CharField(max_length=30,choices=EffectType.choices)
    effect_value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    effect_unit = models.CharField(max_length=24, blank=True, help_text="seconds, percent, questions, multiplier, etc.")
    duration_seconds = models.PositiveIntegerField(default=0)
    cooldown_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["item_id", "level"]
        constraints = [
            models.UniqueConstraint(fields=["item", "level"], name="duckies_unique_item_level"),
            models.CheckConstraint(condition=Q(level__gte=1, level__lte=3), name="duckies_level_range"),
            models.CheckConstraint(condition=Q(effect_value__gte=0), name="duckies_effect_nonnegative"),
        ]

    def clean(self):
        super().clean()
        if self.item_id and self.item.category not in (Category.ATTACK, Category.DEFENSE):
            raise ValidationError("Solo los ataques y defensas tienen niveles.")

    def __str__(self):
        return f"{self.item} - nivel {self.level}"


class InventoryItem(models.Model):
    ducky = models.ForeignKey(Ducky, on_delete=models.CASCADE, related_name="inventory")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="inventory_entries")
    item_level = models.ForeignKey(ItemLevel, on_delete=models.PROTECT, null=True, blank=True, related_name="inventory_entries")
    quantity = models.PositiveIntegerField(default=1)
    obtained_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ducky", "item"], condition=Q(item_level__isnull=True), name="duckies_unique_base_inventory"),
            models.UniqueConstraint(fields=["ducky", "item_level"], condition=Q(item_level__isnull=False), name="duckies_unique_leveled_inventory"),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="duckies_inventory_positive"),
        ]

    def clean(self):
        super().clean()
        if self.item_level_id and self.item_level.item_id != self.item_id:
            raise ValidationError("El nivel debe pertenecer al objeto del inventario.")
        if self.item_id and not self.item.is_consumable and self.quantity != 1:
            raise ValidationError("Los objetos permanentes solo admiten una unidad.")
        if self.item_id and self.item.category in (Category.ATTACK, Category.DEFENSE) and not self.item_level_id:
            raise ValidationError("Los ataques y defensas requieren nivel.")
        if self.item_id and self.item.category not in (Category.ATTACK, Category.DEFENSE) and self.item_level_id:
            raise ValidationError("Este tipo de objeto no admite nivel.")

    def __str__(self):
        return f"{self.ducky}: {self.item} x{self.quantity}"


class EquippedItem(models.Model):
    ducky = models.ForeignKey(Ducky, on_delete=models.CASCADE, related_name="equipped_items")
    inventory_item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE, related_name="equipment")
    slot = models.ForeignKey(EquipmentSlot, on_delete=models.PROTECT, related_name="equipped_items")
    equipped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["ducky", "slot"], name="duckies_unique_equipped_slot")]

    def clean(self):
        super().clean()
        if self.inventory_item_id:
            if self.ducky_id != self.inventory_item.ducky_id:
                raise ValidationError("El objeto no pertenece al Ducky.")
            if self.inventory_item.item.equipment_slot_id != self.slot_id:
                raise ValidationError("El objeto no corresponde a esta zona.")


class EquipmentHistory(models.Model):
    class Action(models.TextChoices):
        EQUIP = "EQUIP", "Equipar"
        UNEQUIP = "UNEQUIP", "Desequipar"

    ducky = models.ForeignKey(Ducky, on_delete=models.CASCADE, related_name="equipment_history")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    slot = models.ForeignKey(EquipmentSlot, on_delete=models.PROTECT)
    action = models.CharField(max_length=10, choices=Action.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class EvolutionItem(models.Model):
    # stage_code es un contrato TEMPORAL: Ecomotor aún no ha publicado EvolutionStage.
    # No se crea una FK ficticia ni se duplica su modelo.
    stage_code = models.SlugField(max_length=60)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="evolution_unlocks")
    required_xp = models.PositiveBigIntegerField(default=0)
    is_automatic = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["stage_code", "item"], name="duckies_unique_stage_item")]

    def clean(self):
        super().clean()
        if self.item_id and self.item.category != Category.HISTORICAL:
            raise ValidationError("Los desbloqueos históricos deben referenciar piezas históricas.")


class ItemUsage(models.Model):
    ducky = models.ForeignKey(Ducky, on_delete=models.CASCADE, related_name="item_usages")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    item_level = models.ForeignKey(ItemLevel, on_delete=models.PROTECT, null=True, blank=True)
    operation_key = models.CharField(max_length=255)
    source_game = models.CharField(max_length=60)
    session_id = models.CharField(max_length=100)
    quantity_used = models.PositiveIntegerField(default=1)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ducky", "operation_key"], name="duckies_unique_usage_key"),
            models.CheckConstraint(condition=Q(quantity_used__gte=1), name="duckies_usage_positive"),
        ]

