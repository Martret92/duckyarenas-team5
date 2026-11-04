"""Visual-only variants for tactical items; never changes ownership or pricing."""
import json
from functools import lru_cache
from pathlib import Path
from django.contrib.staticfiles import finders
from .models import EvolutionItem, SpecializationItem

MANIFEST = Path(__file__).with_name("item_visual_variants.json")

@lru_cache(maxsize=1)
def visual_manifest():
    with MANIFEST.open(encoding="utf-8") as stream:
        return json.load(stream)

def outfit_visual_key(ducky):
    """Use the selected outfit, not the current unlocked stage."""
    if not ducky or not ducky.selected_outfit_id:
        return None
    outfit_id = ducky.selected_outfit_id
    specialization = SpecializationItem.objects.filter(item_id=outfit_id).select_related("specialization").first()
    if specialization:
        return "specialization:" + specialization.specialization.code
    evolution = EvolutionItem.objects.filter(item_id=outfit_id).select_related("stage").first()
    if evolution:
        return "stage:" + evolution.stage.code
    return None

def image_for_item(item, visual_key=None):
    """Return a static-relative path, or empty string if no asset is available."""
    if item is None:
        return ""
    config = visual_manifest().get(item.code, {})
    candidate = config.get(visual_key) if visual_key else None
    if candidate and finders.find(candidate):
        return candidate
    fallback = config.get("default") or item.image_path
    if fallback and finders.find(fallback):
        return fallback
    return ""
