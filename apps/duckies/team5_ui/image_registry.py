"""Recursos visuales por Item real y género; independientes de seeds de demostración.

El Item/EvolutionItem/SpecializationItem de Duckies determina la vestimenta.
Las imágenes provisionales son sustituibles en static sin tocar las vistas.
"""
from pathlib import PurePosixPath
from django.templatetags.static import static

ITEM_ART = {
    'shop_smoke_screen': 'smoke.png',
    'shop_option_inflator': 'options.png',
    'shop_overclock': 'overclock.png',
    'shop_firewall_shield': 'shield.png',
    'shop_noise_filter': 'filter.png',
    'shop_slow_time': 'clock.png',
}
# Los códigos corresponden a asociaciones EvolutionItem y SpecializationItem,
# no a nombres arbitrarios creados por el seed de demostración.
STAGE_ART = {
    'PREHISTORIA': 'prehistoria', 'GRECIA': 'grecia', 'ROMA': 'roma',
    'MEDIEVAL': 'medieval', 'RENACIMIENTO': 'renacimiento',
    'REVOLUCION_INDUSTRIAL': 'revolucion_industrial', 'SIGLO_XX': 'siglo_xx',
}
SPECIALIZATION_ART = {
    'GAMER': 'gamer', 'DEVELOPER': 'developer', 'CIBER': 'ciber',
    'SISTEMAS': 'sistemas', 'DATA_IA': 'data_ia',
}


def _gender(sex):
    return 'female' if sex == 'female' else 'male'


def _official(item, sex):
    if not item.image_path:
        return None
    # Para publicar imágenes oficiales por género, basta colocar las variantes
    # junto al recurso original: p.ej. romano_male.webp y romano_female.webp.
    from django.contrib.staticfiles import finders
    path = PurePosixPath(item.image_path)
    candidate = str(path.with_name(f'{path.stem}_{_gender(sex)}{path.suffix}'))
    if finders.find(candidate):
        return static(candidate)
    return static(item.image_path)


def item_image(item, sex=None):
    if item is None:
        return static(f'team5_ui/img/characters/ducky_{_gender(sex)}.png')
    official = _official(item, sex)
    if official:
        return official
    if item.category == item.HISTORICAL:
        association = item.evolutionitem_set.select_related('stage').first()
        stem = STAGE_ART.get(association.stage.code) if association else None
        if stem:
            return static(f'team5_ui/img/outfits/{stem}_{_gender(sex)}.webp')
    if item.category == item.SPECIALIZATION:
        association = item.specialization_outfit if hasattr(item, 'specialization_outfit') else None
        stem = SPECIALIZATION_ART.get(association.specialization.code) if association else None
        if stem:
            return static(f'team5_ui/img/outfits/{stem}_{_gender(sex)}.webp')
    if item.category in (item.HISTORICAL, item.SPECIALIZATION):
        return static(f'team5_ui/img/characters/ducky_{_gender(sex)}.png')
    return static('team5_ui/img/items/' + ITEM_ART.get(item.code, 'shield.png'))


def ducky_image(ducky):
    if ducky and ducky.selected_outfit_id:
        return item_image(ducky.selected_outfit, ducky.sex)
    return static(f'team5_ui/img/characters/ducky_{_gender(ducky.sex if ducky else None)}.png')
