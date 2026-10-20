from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q

class EquipmentSlot(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    is_main_piece = models.BooleanField(default=False)
    def __str__(self): return self.name

class Item(models.Model):
    HISTORICAL='HISTORICAL'; COSMETIC='COSMETIC'; ATTACK='ATTACK'; DEFENSE='DEFENSE'; HINT='HINT'
    CATEGORIES=[(x,x) for x in (HISTORICAL,COSMETIC,ATTACK,DEFENSE,HINT)]
    code=models.CharField(max_length=80,unique=True)
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    category=models.CharField(max_length=20,choices=CATEGORIES)
    rarity=models.CharField(max_length=30,default='COMMON')
    slot=models.ForeignKey(EquipmentSlot,null=True,blank=True,on_delete=models.PROTECT)
    consumable=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    image_path=models.CharField(max_length=255,blank=True)
    def __str__(self): return self.name

class ItemLevel(models.Model):
    item=models.ForeignKey(Item,on_delete=models.CASCADE,related_name='levels')
    level=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(3)])
    effect_code=models.CharField(max_length=80,blank=True)
    effect_value=models.CharField(max_length=80,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['item','level'],name='ducky_item_level_unique'),models.CheckConstraint(condition=Q(level__gte=1,level__lte=3),name='ducky_level_1_3')]

class Ducky(models.Model):
    SEX=[('male','Masculino'),('female','Femenino')]
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='ducky')
    sex=models.CharField(max_length=6,choices=SEX)
    selected_historical_item=models.ForeignKey(Item,null=True,blank=True,on_delete=models.PROTECT,related_name='selected_by')
    created_at=models.DateTimeField(auto_now_add=True)

class InventoryItem(models.Model):
    ducky=models.ForeignKey(Ducky,on_delete=models.CASCADE,related_name='inventory')
    item=models.ForeignKey(Item,on_delete=models.PROTECT)
    item_level=models.ForeignKey(ItemLevel,null=True,blank=True,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    class Meta:
        constraints=[models.UniqueConstraint(fields=['ducky','item','item_level'],name='ducky_inv_level_unique',condition=Q(item_level__isnull=False)),models.UniqueConstraint(fields=['ducky','item'],name='ducky_inv_base_unique',condition=Q(item_level__isnull=True)),models.CheckConstraint(condition=Q(quantity__gte=1),name='ducky_inventory_qty_positive')]

class EquippedItem(models.Model):
    ducky=models.ForeignKey(Ducky,on_delete=models.CASCADE,related_name='equipment')
    slot=models.ForeignKey(EquipmentSlot,on_delete=models.PROTECT)
    inventory_item=models.OneToOneField(InventoryItem,on_delete=models.CASCADE)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['ducky','slot'],name='ducky_slot_occupied_unique')]

class EquipmentHistory(models.Model):
    ducky=models.ForeignKey(Ducky,on_delete=models.CASCADE)
    slot=models.ForeignKey(EquipmentSlot,on_delete=models.PROTECT)
    item=models.ForeignKey(Item,on_delete=models.PROTECT)
    action=models.CharField(max_length=20)
    created_at=models.DateTimeField(auto_now_add=True)

class EvolutionItem(models.Model):
    stage=models.OneToOneField('ecomotor.EvolutionStage',on_delete=models.PROTECT,related_name='historical_outfit')
    item=models.ForeignKey(Item,on_delete=models.PROTECT)

class ItemGrant(models.Model):
    ducky=models.ForeignKey(Ducky,on_delete=models.CASCADE)
    item=models.ForeignKey(Item,on_delete=models.PROTECT)
    item_level=models.ForeignKey(ItemLevel,null=True,blank=True,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField()
    operation_key=models.CharField(max_length=255)
    reference_type=models.CharField(max_length=50,blank=True)
    reference_id=models.CharField(max_length=255,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['ducky','operation_key'],name='ducky_grant_operation_unique'),models.CheckConstraint(condition=Q(quantity__gt=0),name='ducky_grant_qty_positive')]

class ItemUsage(models.Model):
    ducky=models.ForeignKey(Ducky,on_delete=models.CASCADE)
    item=models.ForeignKey(Item,on_delete=models.PROTECT)
    item_level=models.ForeignKey(ItemLevel,null=True,blank=True,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField()
    operation_key=models.CharField(max_length=255)
    game_reference=models.CharField(max_length=255)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['ducky','operation_key'],name='ducky_usage_operation_unique'),models.CheckConstraint(condition=Q(quantity__gt=0),name='ducky_usage_qty_positive')]
