from apps.bank.models import Wallet, Transaction
from apps.duckies.models import Ducky, InventoryItem, EvolutionItem, SpecializationItem, EquippedItem, ItemGrant
from apps.ecomotor.models import EvolutionStage, Specialization, CharacterStats, LevelThreshold
from apps.shop.models import ShopItem, Purchase
from apps.users.models import UserProfileEcomotor
from .demo_services import STAGES, SPECS

IMAGE_MAP={"shop_smoke_screen":"smoke.svg","shop_option_inflator":"options.svg","shop_overclock":"overclock.svg","shop_firewall_shield":"shield.svg","shop_noise_filter":"filter.svg","shop_slow_time":"clock.svg"}

def state(user):
    ducky=Ducky.objects.select_related("selected_outfit").filter(user=user).first()
    profile=UserProfileEcomotor.objects.filter(user=user).first()
    wallet=Wallet.objects.filter(user=user).first()
    stats=CharacterStats.objects.filter(profile=profile).first() if profile else None
    stages=list(EvolutionStage.objects.order_by("ordinal"))
    stage=next((s for s in stages if profile and s.code==profile.current_stage_code),None)
    level_next=LevelThreshold.objects.filter(level__gt=profile.current_level).order_by("level").first() if profile else None
    return {"ducky":ducky,"profile":profile,"wallet":wallet,"stats":stats,"stages":stages,"stage":stage,
        "next_xp":level_next.minimum_xp if level_next else None,"specializations":list(Specialization.objects.all()),
        "outfits":list(EvolutionItem.objects.select_related("item","stage").order_by("stage__ordinal")),
        "spec_outfits":list(SpecializationItem.objects.select_related("item","specialization")),
        "inventory":list(InventoryItem.objects.select_related("item","item_level","item__slot").filter(ducky=ducky).order_by("item__name")) if ducky else [],
        "item_grants":list(ItemGrant.objects.select_related("item").filter(ducky=ducky).order_by("-created_at")[:25]) if ducky else [],
        "equipped":list(EquippedItem.objects.select_related("inventory_item__item","slot").filter(ducky=ducky)) if ducky else [],
        "offers":list(ShopItem.objects.select_related("item","item_level").filter(is_available=True)),
        "transactions":list(Transaction.objects.filter(wallet=wallet).order_by("-created_at")[:25]) if wallet else [],
        "purchases":list(Purchase.objects.select_related("shop_item").filter(user=user)[:20]),
        "stage_names":dict(STAGES),"spec_names":dict(SPECS),"image_map":IMAGE_MAP}
