

"""Interfaz integrada de DuckyArena Equipo 5.

Las operaciones se delegan a los servicios de dominio.
Las compras se realizan exclusivamente mediante las vistas oficiales de Shop.
Las herramientas de demostración permanecen fuera de esta interfaz.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from apps.bank.models import Transaction, Wallet
from apps.bank.services import BankError

from apps.duckies.integration_services import (
    initialize_player_ducky,
    select_initial_specialization_and_outfit,
    switch_specialization_and_outfit,
)
from apps.duckies.item_visuals import image_for_item, outfit_visual_key
from apps.duckies.models import (
    Ducky,
    EquippedItem,
    InventoryItem,
    Item,
    ItemGrant,
    ItemLevel,
)
from apps.duckies.selectors import get_outfit_catalog
from apps.duckies.services import equip_item, select_outfit

from apps.ecomotor.models import (
    CharacterStats,
    EvolutionStage,
    LevelThreshold,
    Specialization,
)

from apps.shop.models import Purchase
from apps.users.models import UserProfileEcomotor

from .image_registry import ducky_image, item_image


SECTIONS = {
    "dashboard": "Inicio",
    "player": "Mi Pato",
    "evolution": "Evolución",
    "specialization": "Especialización",
    "wardrobe": "Vestuario",
    "inventory": "Inventario",
    "museum": "Museo",
    "shop": "Tienda",
    "wallet": "Banco",
    "rewards": "Rewards",
    "arena": "Arena",
}


# ============================================================
# DASHBOARD E INTERFAZ INTEGRADA
# ============================================================

@login_required
@require_GET
def dashboard(request, section="dashboard"):
    """Muestra las secciones integradas del Equipo 5.

    Solo consulta información de las aplicaciones de dominio.
    No concede XP, monedas ni artículos artificialmente.
    """

    if section not in SECTIONS:
        raise Http404()

    user = request.user

    # --------------------------------------------------------
    # DUCKY, PERFIL Y WALLET
    # --------------------------------------------------------

    ducky = (
        Ducky.objects
        .select_related("selected_outfit")
        .filter(user=user)
        .first()
    )

    profile = (
        UserProfileEcomotor.objects
        .filter(user=user)
        .first()
    )

    wallet = (
        Wallet.objects
        .filter(user=user)
        .first()
    )

    # --------------------------------------------------------
    # EVOLUCIÓN Y NIVELES
    # --------------------------------------------------------

    stage = None
    next_level = None

    if profile:
        stage = (
            EvolutionStage.objects
            .filter(code=profile.current_stage_code)
            .first()
        )

        next_level = (
            LevelThreshold.objects
            .filter(
                minimum_xp__gt=profile.historical_xp_total
            )
            .order_by("minimum_xp")
            .first()
        )

    # --------------------------------------------------------
    # VESTIMENTAS HISTÓRICAS Y ESPECIALIZACIONES
    # --------------------------------------------------------

    historical, spec_outfits = get_outfit_catalog(user)

    for outfit in historical:
        outfit["image_url"] = item_image(
            outfit["item"],
            ducky.sex if ducky else None,
        )

    for outfit in spec_outfits:
        outfit["image_url"] = item_image(
            outfit["item"],
            ducky.sex if ducky else None,
        )

    # --------------------------------------------------------
    # INVENTARIO CON VARIANTES VISUALES
    # --------------------------------------------------------

    visual_key = outfit_visual_key(ducky)

    inventory = list(
        InventoryItem.objects
        .filter(ducky=ducky)
        .select_related("item", "item_level")
    ) if ducky else []

    for entry in inventory:
        relative_image = image_for_item(
            entry.item,
            visual_key,
        )

        entry.image_url = (
            static(relative_image)
            if relative_image
            else item_image(entry.item)
        )

    # --------------------------------------------------------
    # ESTADÍSTICAS
    # --------------------------------------------------------

    stats = (
        CharacterStats.objects
        .filter(profile=profile)
        .first()
    ) if profile else None

    # --------------------------------------------------------
    # EQUIPAMIENTO Y ENTREGAS
    # --------------------------------------------------------

    equipped = list(
        EquippedItem.objects
        .filter(ducky=ducky)
        .select_related("inventory_item__item")
    ) if ducky else []

    # Utilizar las mismas variantes visuales del inventario.
    # La imagen depende de la vestimenta seleccionada,
    # no de la época desbloqueada ni del artículo comprado.
    for eq in equipped:
        item = eq.inventory_item.item

        relative_image = image_for_item(
            item,
            visual_key,
        )

        eq.image_url = (
            static(relative_image)
            if relative_image
            else item_image(item)
        )

    # Mantener las entregas de artículos en el contexto.
    # Esta consulta es independiente del equipamiento.
    item_grants = (
        ItemGrant.objects
        .filter(ducky=ducky)
        .select_related("item")
        .order_by("-created_at")[:15]
    ) if ducky else []

    # --------------------------------------------------------
    # BANK: MOVIMIENTOS Y COMPRAS
    # --------------------------------------------------------

    transactions = (
        Transaction.objects
        .filter(wallet=wallet)
        .order_by("-created_at")[:25]
    ) if wallet else []

    purchases = (
        Purchase.objects
        .filter(user=user)
        .select_related("shop_item")
        .order_by("-created_at")[:12]
    )

    # --------------------------------------------------------
    # CONTEXTO DE LA INTERFAZ
    # --------------------------------------------------------

    ctx = {
        "section": section,
        "section_title": SECTIONS[section],
        "sections": SECTIONS,

        "user": user,
        "ducky": ducky,
        "profile": profile,
        "wallet": wallet,

        "stage": stage,
        "next_xp": (
            next_level.minimum_xp
            if next_level
            else None
        ),

        "stats": stats,

        "stages": EvolutionStage.objects.order_by("ordinal"),
        "specializations": Specialization.objects.order_by("name"),

        "outfits": historical,
        "spec_outfits": spec_outfits,

        "inventory": inventory,
        "equipped": equipped,
        "item_grants": item_grants,

        "transactions": transactions,
        "purchases": purchases,

        # Nunca habilitar herramientas de demo aquí.
        "demo_enabled": False,

        "ducky_image": ducky_image(ducky),

        'rewards_lab_url': 'http://127.0.0.1:8002/demo/objetivo-persistente/',
    }

    return render(
        request,
        "team5_ui/page.html",
        ctx,
    )


# ============================================================
# ACCIONES DE LA INTERFAZ OFICIAL
# ============================================================

@login_required
@require_POST
def action(request):
    """Ejecuta operaciones autorizadas del Equipo 5.

    Las compras pertenecen a Shop y no se procesan aquí.
    Las operaciones de demostración tampoco se procesan aquí.
    """

    user = request.user

    name = request.POST.get("action", "")

    return_to = request.POST.get(
        "return_to",
        "dashboard",
    )

    if return_to not in SECTIONS:
        return_to = "dashboard"

    # --------------------------------------------------------
    # OPERACIONES PROHIBIDAS EN ESTA INTERFAZ
    # --------------------------------------------------------

    if name in ("xp", "coins", "hint"):
        return HttpResponseForbidden(
            "Operación exclusiva del módulo de demostración."
        )

    if name == "buy":
        return HttpResponseForbidden(
            "Las compras deben realizarse mediante Shop."
        )

    # --------------------------------------------------------
    # OPERACIONES DE DOMINIO
    # --------------------------------------------------------

    try:

        # CREACIÓN DEL DUCKY
        if name == "create":

            initialize_player_ducky(
                user,
                request.POST.get("sex", ""),
            )

        # ESPECIALIZACIÓN
        elif name == "specialization":

            profile = UserProfileEcomotor.objects.get(
                user=user
            )

            code = request.POST.get("code", "")

            if profile.active_specialization_code:

                switch_specialization_and_outfit(
                    user,
                    code,
                    profile.active_specialization_code,
                )

            else:

                select_initial_specialization_and_outfit(
                    user,
                    code,
                )

        # SELECCIÓN DE VESTIMENTA
        elif name == "outfit":

            item = Item.objects.get(
                pk=int(request.POST.get("item_id", "0"))
            )

            select_outfit(
                user,
                item,
            )

        # EQUIPAMIENTO DE OBJETOS
        elif name == "equip":

            item = Item.objects.get(
                pk=int(request.POST.get("item_id", "0"))
            )

            level = None

            if request.POST.get("code"):
                level = ItemLevel.objects.get(
                    pk=int(request.POST["code"])
                )

            equip_item(
                user,
                item,
                level,
            )

        else:
            raise ValueError(
                "Operación desconocida."
            )

    except (
        BankError,
        ValueError,
        ValidationError,
        DatabaseError,
        Item.DoesNotExist,
        ItemLevel.DoesNotExist,
        UserProfileEcomotor.DoesNotExist,
        Wallet.DoesNotExist,
        Ducky.DoesNotExist,
    ) as error:

        messages.error(
            request,
            str(error),
        )

    else:

        messages.success(
            request,
            "Operación realizada mediante el servicio del equipo.",
        )

    return redirect(
        "team5_ui:" + return_to
    )


# ============================================================
# REGISTRO DE USUARIOS
# ============================================================

@require_http_methods(["GET", "POST"])
def register(request):
    """Registro de usuarios para la interfaz integrada."""

    if request.user.is_authenticated:
        return redirect(
            "team5_ui:dashboard"
        )

    form = UserCreationForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        user = form.save()

        login(
            request,
            user,
        )

        return redirect(
            "team5_ui:dashboard"
        )

    return render(
        request,
        "registration/register.html",
        {
            "form": form,
        },
    )
