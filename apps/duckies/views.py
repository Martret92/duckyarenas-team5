"""Vistas reales de Duckies; independientes de la demo team5_ui."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from .forms import EquipItemForm, OutfitSelectionForm
from .models import InventoryItem, Item
from .selectors import get_ducky, get_equipment, get_inventory, get_outfit_catalog
from .services import equip_item, select_outfit


def _ducky_or_404(request):
    ducky = get_ducky(request.user)
    if ducky is None:
        raise Http404('El usuario no tiene un Ducky inicializado.')
    return ducky


@login_required
@require_GET
def detail_view(request):
    ducky = _ducky_or_404(request)
    return render(request, 'duckies/detail.html', {'ducky': ducky, 'equipment': get_equipment(ducky)})


@login_required
@require_GET
def inventory_view(request):
    ducky = _ducky_or_404(request)
    return render(request, 'duckies/inventory.html', {'ducky': ducky, 'inventory': get_inventory(ducky), 'equipment': get_equipment(ducky)})


@login_required
@require_GET
def outfits_view(request):
    ducky = _ducky_or_404(request)
    historical, specializations = get_outfit_catalog(request.user)
    return render(request, 'duckies/outfits.html', {'ducky': ducky, 'historical': historical, 'specializations': specializations})


@login_required
@require_GET
def museum_view(request):
    ducky = _ducky_or_404(request)
    historical, _ = get_outfit_catalog(request.user)
    return render(request, 'duckies/museum.html', {'ducky': ducky, 'historical': historical})


@login_required
@require_POST
def select_outfit_view(request):
    _ducky_or_404(request)
    form = OutfitSelectionForm(request.POST)
    if not form.is_valid():
        return HttpResponse('Identificador de vestimenta inválido.', status=400)
    item = Item.objects.filter(pk=form.cleaned_data['item_id']).first()
    if item is None:
        raise Http404('Vestimenta no encontrada.')
    try:
        select_outfit(request.user, item)
    except (ValueError, ValidationError, Item.DoesNotExist) as exc:
        return HttpResponse(str(exc), status=409)
    except DatabaseError:
        return HttpResponse('Servicio no disponible temporalmente.', status=503)
    messages.success(request, 'Vestimenta seleccionada.')
    return redirect('duckies:outfits')


@login_required
@require_POST
def equip_view(request):
    ducky = _ducky_or_404(request)
    form = EquipItemForm(request.POST)
    if not form.is_valid():
        return HttpResponse('Identificador de inventario inválido.', status=400)
    owned = InventoryItem.objects.select_related('item', 'item_level').filter(pk=form.cleaned_data['inventory_id'], ducky=ducky).first()
    if owned is None:
        raise Http404('Artículo no encontrado en tu inventario.')
    try:
        equip_item(request.user, owned.item, item_level=owned.item_level)
    except (ValueError, ValidationError, InventoryItem.DoesNotExist) as exc:
        return HttpResponse(str(exc), status=409)
    except DatabaseError:
        return HttpResponse('Servicio no disponible temporalmente.', status=503)
    messages.success(request, 'Objeto equipado.')
    return redirect('duckies:inventory')
