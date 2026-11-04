from django import template
from django.templatetags.static import static
from apps.duckies.item_visuals import image_for_item

register = template.Library()

@register.simple_tag
def item_image(item, visual_key=None):
    path = image_for_item(item, visual_key)
    return static(path) if path else ""
