import hashlib
import json

from django.db import transaction

from apps.bank.services import debit_coins
from apps.duckies.models import Ducky, Item
from apps.duckies.services import get_item_ownership, grant_item

from .models import Purchase, PurchaseStatus, ShopItem


class ShopError(Exception):
    """Base exception for Shop business errors."""


class ProductUnavailable(ShopError):
    """The requested SKU is missing, disabled, or not eligible for sale."""


class InvalidProductConfiguration(ShopError):
    """The SKU's item, level, category, or pack configuration is invalid."""


class PermanentItemAlreadyOwned(ShopError):
    """A permanent item cannot be purchased more than once by the same user."""


class BuyerNotProvisioned(ShopError):
    """The user has no Duckies avatar/inventory to receive a digital item."""


class PurchaseIdempotencyConflict(ShopError):
    """A purchase operation key was reused with another SKU or quantity."""


class DeliveryRejected(ShopError):
    """Duckies rejected a requested delivery."""


def _require_operation_key(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("operation_key must be a non-empty string.")
    if len(value) > 255:
        raise ValueError("operation_key must not exceed 255 characters.")


def _require_sku_code(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("sku_code must be a non-empty string.")
    if len(value) > 100:
        raise ValueError("sku_code must not exceed 100 characters.")


def _require_quantity(value):
    if type(value) is not int or value <= 0:
        raise ValueError("quantity must be a positive integer.")
    if value > (2**31 - 1):
        raise ValueError("quantity exceeds the supported range.")


def _fingerprint(*, user_id, sku_code, quantity):
    payload = {
        "version": 1,
        "user_id": user_id,
        "sku_code": sku_code,
        "quantity": quantity,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _derived_operation_key(prefix, *parts):
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _validate_offer(shop_item):
    item = shop_item.item
    item_level = shop_item.item_level

    if not shop_item.is_available:
        raise ProductUnavailable("The commercial offer is not available.")
    if not item.is_active:
        raise ProductUnavailable("The underlying item is inactive.")
    if item.category == Item.HISTORICAL:
        raise ProductUnavailable("Historical items are not sold in Shop V1.")

    if item.category not in (Item.COSMETIC, Item.ATTACK, Item.DEFENSE, Item.HINT):
        raise InvalidProductConfiguration("The item category is not supported by Shop V1.")
    if item.category in (Item.ATTACK, Item.DEFENSE):
        if item_level is None:
            raise InvalidProductConfiguration("Attack and defense offers require an item level.")
    elif item_level is not None:
        raise InvalidProductConfiguration("This item category cannot use an item level.")

    if item_level is not None and item_level.item_id != item.pk:
        raise InvalidProductConfiguration("The selected level belongs to another item.")

    if item.category in (Item.ATTACK, Item.DEFENSE, Item.HINT) and not item.consumable:
        raise InvalidProductConfiguration("Attack, defense, and hint items must be consumable.")
    if item.category == Item.COSMETIC and item.consumable:
        raise InvalidProductConfiguration("Cosmetic items must be permanent.")

    if type(shop_item.price_coins) is not int or shop_item.price_coins <= 0:
        raise InvalidProductConfiguration("The server-side price must be positive.")
    if type(shop_item.included_quantity) is not int or shop_item.included_quantity <= 0:
        raise InvalidProductConfiguration("included_quantity must be positive.")

    if not item.consumable and shop_item.included_quantity != 1:
        raise InvalidProductConfiguration("Permanent items must have included_quantity=1.")


def purchase_item(user, sku_code, *, operation_key, quantity=1):
    """Buy a digital SKU and coordinate debit, delivery, and Purchase locally.

    The outer transaction is safe only while Bank, Shop, and Duckies use the same
    database alias and their services do not commit independently or perform I/O.
    """
    _require_operation_key(operation_key)
    _require_sku_code(sku_code)
    _require_quantity(quantity)

    request_fingerprint = _fingerprint(
        user_id=user.pk,
        sku_code=sku_code,
        quantity=quantity,
    )

    with transaction.atomic():
        # A replay must recover the original result before current availability/price checks.
        existing = (
            Purchase.objects.select_for_update()
            .select_related("shop_item", "bank_transaction")
            .filter(user=user, operation_key=operation_key)
            .first()
        )
        if existing is not None:
            if existing.request_fingerprint != request_fingerprint:
                raise PurchaseIdempotencyConflict(
                    "operation_key was already used with a different SKU or quantity."
                )
            return existing

        shop_item = (
            ShopItem.objects.select_for_update()
            .select_related("item", "item_level")
            .filter(code=sku_code)
            .first()
        )
        if shop_item is None:
            raise ProductUnavailable("The requested SKU does not exist.")

        _validate_offer(shop_item)
        item = shop_item.item
        item_level = shop_item.item_level

        try:
            Ducky.objects.select_for_update().get(user=user)
        except Ducky.DoesNotExist as exc:
            raise BuyerNotProvisioned(
                "The buyer has no initialized Ducky inventory."
            ) from exc

        if not item.consumable:
            if quantity != 1:
                raise InvalidProductConfiguration(
                    "Permanent items can only be purchased once per operation."
                )
            try:
                owned_quantity = get_item_ownership(user, item, item_level)
            except Ducky.DoesNotExist as exc:
                raise BuyerNotProvisioned(
                "The buyer has no initialized Ducky inventory."
            ) from exc
            if owned_quantity > 0:
                raise PermanentItemAlreadyOwned("This permanent item is already owned.")

        total_price = shop_item.price_coins * quantity
        max_positive_bigint = (2**63) - 1
        delivered_quantity = shop_item.included_quantity * quantity
        if total_price > max_positive_bigint or delivered_quantity > (2**31 - 1):
            raise InvalidProductConfiguration(
                "The requested package quantity exceeds the supported range."
            )

        debit_key = _derived_operation_key("shop-debit-v1", user.pk, operation_key)
        bank_reference = _derived_operation_key(
            "purchase-reference-v1", user.pk, operation_key, sku_code, quantity
        )
        ledger_result = debit_coins(
            user,
            total_price,
            source="shop",
            operation_key=debit_key,
            issuing_entity="DuckyShop",
            reference_type="purchase",
            reference_id=bank_reference,
            description=f"Shop purchase {sku_code}",
        )

        delivery_key = _derived_operation_key(
            "shop-grant-v1",
            user.pk,
            operation_key,
            sku_code,
            item.pk,
            item_level.pk if item_level else None,
        )
        try:
            grant = grant_item(
                user,
                item,
                delivered_quantity,
                delivery_key,
                item_level=item_level,
                reference_type="purchase",
                reference_id=operation_key,
            )
        except ValueError as exc:
            raise DeliveryRejected(str(exc)) from exc

        purchase = Purchase.objects.create(
            user=user,
            shop_item=shop_item,
            operation_key=operation_key,
            request_fingerprint=request_fingerprint,
            unit_price_coins=shop_item.price_coins,
            quantity=quantity,
            total_price_coins=total_price,
            status=PurchaseStatus.COMPLETED,
            bank_transaction=ledger_result.transaction,
            delivery_reference=f"ItemGrant:{grant.pk}",
        )
        return purchase
