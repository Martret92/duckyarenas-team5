

"""Interfaz aislada de Duckies; nunca modifica XP ni saldo de Bank."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.users.models import UserProfileEcomotor

from .image_registry import image_for
from .models import (
    Ducky,
    EquippedItem,
    EvolutionItem,
    InventoryItem,
    Item,
    SpecializationItem,
)
from .services import equip_item, select_outfit


def _context(request):
    """Obtiene el personaje y el perfil Ecomotor del usuario."""
    ducky = (
        Ducky.objects
        .select_related("selected_outfit")
        .filter(user=request.user)
        .first()
    )

    profile = (
        UserProfileEcomotor.objects
        .filter(user=request.user)
        .first()
    )

    return {
        "ducky": ducky,
        "profile": profile,
    }


def _prepared(request):
    """Comprueba que el usuario tenga Ducky y perfil Ecomotor."""
    context = _context(request)

    if not context["ducky"] or not context["profile"]:
        messages.info(
            request,
            "Primero necesitas un perfil Ecomotor y un Ducky. "
            "Consulta las instrucciones de preparación.",
        )
        return None

    return context


@login_required(login_url="duckies:login")
def setup(request):
    """Muestra el estado de preparación de Duckies."""
    context = _context(request)

    context["outfits_ready"] = EvolutionItem.objects.count()

    context["specialization_outfits_ready"] = (
        SpecializationItem.objects.count()
    )

    return render(
        request,
        "duckies/setup.html",
        context,
    )


@login_required(login_url="duckies:login")
def dashboard(request):
    """Muestra el personaje, su vestimenta y sus objetos."""
    context = _prepared(request)

    if context is None:
        return redirect("duckies:setup")

    ducky = context["ducky"]
    profile = context["profile"]
    outfit = ducky.selected_outfit

    context["outfit_image"] = (
        image_for(outfit, ducky.sex)
        if outfit
        else "duckies/images/placeholders/default.svg"
    )

    context["owned_count"] = (
        InventoryItem.objects
        .filter(ducky=ducky)
        .count()
    )

    context["equipped_count"] = (
        EquippedItem.objects
        .filter(ducky=ducky)
        .count()
    )

    context["active_specialization_code"] = (
        profile.active_specialization_code
    )

    context["selected_outfit"] = outfit

    return render(
        request,
        "duckies/dashboard.html",
        context,
    )


@login_required(login_url="duckies:login")
def inventory(request):
    """Muestra los objetos tácticos del inventario."""
    context = _prepared(request)

    if context is None:
        return redirect("duckies:setup")

    ducky = context["ducky"]

    entries = (
        InventoryItem.objects
        .filter(ducky=ducky)
        .select_related(
            "item",
            "item_level",
            "item__slot",
        )
        .order_by(
            "item__name",
            "item_level__level",
        )
    )

    context["entries"] = [
        {
            "entry": entry,
            "image": image_for(entry.item, ducky.sex),
        }
        for entry in entries
    ]

    context["equipped_ids"] = set(
        EquippedItem.objects
        .filter(ducky=ducky)
        .values_list("inventory_item_id", flat=True)
    )

    return render(
        request,
        "duckies/inventory.html",
        context,
    )


@login_required(login_url="duckies:login")
def equipment(request):
    """Muestra los objetos tácticos equipados."""
    context = _prepared(request)

    if context is None:
        return redirect("duckies:setup")

    ducky = context["ducky"]

    entries = (
        EquippedItem.objects
        .filter(ducky=ducky)
        .select_related(
            "slot",
            "inventory_item__item",
            "inventory_item__item_level",
        )
    )

    context["entries"] = [
        {
            "entry": entry,
            "image": image_for(
                entry.inventory_item.item,
                ducky.sex,
            ),
        }
        for entry in entries
    ]

    return render(
        request,
        "duckies/equipment.html",
        context,
    )


@login_required(login_url="duckies:login")
def museum(request):
    """
    Muestra las vestimentas históricas y las
    vestimentas exclusivas de especialización.
    """
    context = _prepared(request)

    if context is None:
        return redirect("duckies:setup")

    ducky = context["ducky"]
    profile = context["profile"]

    active_code = profile.active_specialization_code

    # --------------------------------------------------
    # VESTIMENTAS HISTÓRICAS
    # --------------------------------------------------

    historical_outfits = list(
        EvolutionItem.objects
        .select_related("stage", "item")
        .order_by("stage__ordinal")
    )

    current_stage = next(
        (
            association.stage.ordinal
            for association in historical_outfits
            if association.stage.code == profile.current_stage_code
        ),
        0,
    )

    context["entries"] = [
        {
            "outfit": association,
            "unlocked": (
                association.stage.ordinal <= current_stage
            ),
            "selected": (
                ducky.selected_outfit_id == association.item_id
            ),
            "image": image_for(
                association.item,
                ducky.sex,
            ),
            "selectable": (
                association.item.is_active
                and association.stage.ordinal <= current_stage
                and (
                    bool(active_code)
                    or association.stage.ordinal == current_stage
                )
            ),
        }
        for association in historical_outfits
    ]

    # --------------------------------------------------
    # VESTIMENTAS DE ESPECIALIZACIÓN
    # --------------------------------------------------

    specialization_outfits = (
        SpecializationItem.objects
        .select_related("specialization", "item")
        .order_by("specialization__code")
    )

    context["specialization_entries"] = [
        {
            "association": association,
            "item": association.item,
            "specialization": association.specialization,
            "selected": (
                ducky.selected_outfit_id == association.item_id
            ),
            "unlocked": (
                bool(active_code)
                and association.specialization.code == active_code
            ),
            "selectable": (
                association.item.is_active
                and bool(active_code)
                and association.specialization.code == active_code
            ),
            "image": image_for(
                association.item,
                ducky.sex,
            ),
        }
        for association in specialization_outfits
    ]

    context["active_specialization_code"] = active_code
    context["selected_outfit"] = ducky.selected_outfit

    return render(
        request,
        "duckies/museum.html",
        context,
    )


@login_required(login_url="duckies:login")
@require_POST
def action(request):
    """Procesa el equipamiento táctico y la selección de vestimentas."""
    context = _prepared(request)

    if context is None:
        return redirect("duckies:setup")

    kind = request.POST.get("kind")

    try:
        # --------------------------------------------------
        # EQUIPAR OBJETO TÁCTICO
        # --------------------------------------------------

        if kind == "equip":
            inv = (
                InventoryItem.objects
                .select_related("item", "item_level")
                .get(
                    pk=request.POST.get("inventory_id"),
                    ducky=context["ducky"],
                )
            )

            equip_item(
                request.user,
                inv.item,
                inv.item_level,
            )

            messages.success(
                request,
                "Objeto equipado correctamente.",
            )

            return redirect("duckies:equipment")

        # --------------------------------------------------
        # SELECCIONAR VESTIMENTA
        # --------------------------------------------------

        if kind == "outfit":
            item = Item.objects.get(
                pk=request.POST.get("item_id"),
                category__in=[
                    Item.HISTORICAL,
                    Item.SPECIALIZATION,
                ],
            )

            # El servicio valida:
            # - Histórico: etapa desbloqueada y reglas de selección.
            # - Especialización: debe coincidir con la activa.
            select_outfit(
                request.user,
                item,
            )

            messages.success(
                request,
                "Vestimenta seleccionada correctamente.",
            )

            return redirect("duckies:museum")

        messages.error(
            request,
            "Acción desconocida.",
        )

    except (
        ValueError,
        Item.DoesNotExist,
        InventoryItem.DoesNotExist,
        EvolutionItem.DoesNotExist,
        SpecializationItem.DoesNotExist,
        Ducky.DoesNotExist,
    ) as exc:
        messages.error(
            request,
            f"No se pudo completar la acción: {exc}",
        )

    return redirect(
        "duckies:museum"
        if kind == "outfit"
        else "duckies:inventory"
    )

