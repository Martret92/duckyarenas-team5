import secrets

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import F, Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static

from apps.bank.models import Wallet
from apps.duckies.models import Ducky
from apps.duckies.item_visuals import outfit_visual_key, image_for_item
from apps.duckies.team5_ui.image_registry import item_image
from apps.duckies.team5_ui.views import SECTIONS
from django.views.decorators.http import require_GET, require_POST

from apps.bank.services import BankError
from apps.duckies.models import Item

from .forms import PurchaseForm
from .models import Purchase, ShopItem
from .services import ShopError, purchase_item


def _catalog_queryset():
    """Return only active offers whose persisted configuration matches Shop V1."""
    supported_configuration = (
        Q(
            item__category=Item.COSMETIC,
            item__consumable=False,
            item_level__isnull=True,
        )
        | Q(
            item__category__in=(Item.ATTACK, Item.DEFENSE),
            item__consumable=True,
            item_level__isnull=False,
            item_level__item_id=F("item_id"),
        )
        | Q(
            item__category=Item.HINT,
            item__consumable=True,
            item_level__isnull=True,
        )
    )
    return (
        ShopItem.objects.filter(
            is_available=True,
            item__is_active=True,
        )
        .filter(supported_configuration)
        .select_related("item", "item_level")
    )


def _ui_context(request, **extra):
    """Presentation-only context: never alters Shop, Bank or Duckies state."""
    ducky = Ducky.objects.select_related("selected_outfit").filter(user=request.user).first()
    visual_key = outfit_visual_key(ducky)
    wallet = Wallet.objects.filter(user=request.user).first()
    profile = None
    try:
        from apps.users.models import UserProfileEcomotor
        profile = UserProfileEcomotor.objects.filter(user=request.user).first()
    except DatabaseError:
        raise
    def decorate(offer):
        relative = image_for_item(offer.item, visual_key)
        offer.image_url = static(relative) if relative else item_image(offer.item)
        return offer
    if "shop_items" in extra:
        extra["shop_items"] = [decorate(offer) for offer in extra["shop_items"]]
    if extra.get("shop_item") is not None:
        decorate(extra["shop_item"])
    if "purchases" in extra:
        for purchase in extra["purchases"]:
            decorate(purchase.shop_item)
    return {
        "section": "shop", "section_title": "Tienda", "sections": SECTIONS,
        "ducky": ducky, "wallet": wallet, "profile": profile, **extra,
    }


def _purchase_form(data=None):
    if data is not None:
        return PurchaseForm(data)
    return PurchaseForm(initial={"operation_key": secrets.token_urlsafe(32), "quantity": 1})


@login_required
@require_GET
def catalog_view(request):
    try:
        return render(
            request,
            "shop/catalog.html",
            _ui_context(request, shop_items=_catalog_queryset()),
        )
    except DatabaseError:
        return HttpResponse("Servicio no disponible temporalmente.", status=503)


@login_required
@require_GET
def product_detail_view(request, sku_code):
    try:
        shop_item = _catalog_queryset().filter(code=sku_code).first()
        if shop_item is None:
            raise Http404("Producto no encontrado.")
        return render(
            request,
            "shop/detail.html",
            _ui_context(request, shop_item=shop_item, form=_purchase_form()),
        )
    except DatabaseError:
        return HttpResponse("Servicio no disponible temporalmente.", status=503)


@login_required
@require_POST
def purchase_view(request, sku_code):
    form = _purchase_form(request.POST)

    if not form.is_valid():
        try:
            shop_item = _catalog_queryset().filter(code=sku_code).first()
        except DatabaseError:
            return HttpResponse("Servicio no disponible temporalmente.", status=503)

        if shop_item is None:
            raise Http404("Producto no encontrado o no disponible.")

        return render(
            request,
            "shop/detail.html",
            _ui_context(request, shop_item=shop_item, form=form),
            status=400,
        )

    try:
        # The service must resolve completed operations before checking
        # whether the catalog offer is currently available.
        purchase_item(
            request.user,
            sku_code,
            operation_key=form.cleaned_data["operation_key"],
            quantity=form.cleaned_data["quantity"],
        )
    except (ShopError, BankError, ValueError) as exc:
        try:
            shop_item = _catalog_queryset().filter(code=sku_code).first()
        except DatabaseError:
            return HttpResponse("Servicio no disponible temporalmente.", status=503)

        if shop_item is None:
            raise Http404("Producto no encontrado o no disponible.") from exc

        return render(
            request,
            "shop/detail.html",
            _ui_context(request, shop_item=shop_item, form=form, error_message=str(exc)),
            status=409,
        )
    except DatabaseError:
        return HttpResponse("Servicio no disponible temporalmente.", status=503)

    return redirect("shop:purchase-history")


@login_required
@require_GET
def purchase_history_view(request):
    try:
        purchases = (
            Purchase.objects.filter(user=request.user)
            .select_related("shop_item", "bank_transaction")
            .order_by("-created_at", "-id")
        )
        page_obj = Paginator(purchases, 20).get_page(request.GET.get("page", 1))
        return render(
            request,
            "shop/purchase_history.html",
            _ui_context(request, page_obj=page_obj, purchases=page_obj.object_list),
        )
    except DatabaseError:
        return HttpResponse("Servicio no disponible temporalmente.", status=503)
