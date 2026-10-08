from dataclasses import dataclass
from typing import Callable

from django.db import transaction
from django.db.models import Q, Sum

from .models import (
    Purchase,
    PurchaseStatus,
    ShopItem,
    Transaction,
    TransactionType,
    Wallet,
)


class BankError(Exception):
    """Error base de DuckyBank."""


class InsufficientFunds(BankError):
    """El saldo disponible no permite realizar el débito."""


class IdempotencyConflict(BankError):
    """La operation_key ya fue utilizada con otros parámetros."""


class PurchaseError(Exception):
    """Error base de DuckyShop."""


class ProductUnavailable(PurchaseError):
    """La oferta comercial no está disponible."""


@dataclass(frozen=True)
class LedgerResult:
    transaction: Transaction
    created: bool


def _wallet_for_update(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)

    return Wallet.objects.select_for_update().get(
        pk=wallet.pk
    )


def _existing_transaction(
    wallet,
    operation_key,
    expected_amount,
    transaction_type,
):
    existing = Transaction.objects.filter(
        wallet=wallet,
        operation_key=operation_key,
    ).first()

    if existing is None:
        return None

    if (
        existing.amount != expected_amount
        or existing.transaction_type != transaction_type
    ):
        raise IdempotencyConflict(
            f"La operation_key '{operation_key}' "
            "ya fue utilizada con datos diferentes."
        )

    return LedgerResult(
        transaction=existing,
        created=False,
    )


def _record_transaction(
    *,
    wallet,
    amount,
    transaction_type,
    operation_key,
    source_platform,
    issuing_entity,
    description="",
    reference_type="",
    reference_id="",
):
    existing = _existing_transaction(
        wallet,
        operation_key,
        amount,
        transaction_type,
    )

    if existing is not None:
        return existing

    new_balance = wallet.available_balance + amount

    if new_balance < 0:
        raise InsufficientFunds(
            "Saldo insuficiente de Duki Coins."
        )

    wallet.available_balance = new_balance
    wallet.save(
        update_fields=[
            "available_balance",
            "updated_at",
        ]
    )

    entry = Transaction.objects.create(
        wallet=wallet,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=new_balance,
        operation_key=operation_key,
        source_platform=source_platform,
        issuing_entity=issuing_entity,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
    )

    return LedgerResult(
        transaction=entry,
        created=True,
    )


def credit_wallet(
    user,
    amount,
    *,
    operation_key,
    description="",
    source_platform="",
    issuing_entity="",
    reference_type="",
    reference_id="",
    transaction_type=TransactionType.REWARD,
):
    if amount <= 0:
        raise ValueError(
            "El crédito debe ser mayor que cero."
        )

    if not operation_key:
        raise ValueError(
            "operation_key es obligatoria."
        )

    with transaction.atomic():
        wallet = _wallet_for_update(user)

        return _record_transaction(
            wallet=wallet,
            amount=amount,
            transaction_type=transaction_type,
            operation_key=operation_key,
            source_platform=source_platform,
            issuing_entity=issuing_entity,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )


def debit_wallet(
    user,
    amount,
    *,
    operation_key,
    description="",
    source_platform="ducky_shop",
    issuing_entity="DuckyShop",
    reference_type="purchase",
    reference_id="",
):
    if amount <= 0:
        raise ValueError(
            "El débito debe ser mayor que cero."
        )

    if not operation_key:
        raise ValueError(
            "operation_key es obligatoria."
        )

    with transaction.atomic():
        wallet = _wallet_for_update(user)

        return _record_transaction(
            wallet=wallet,
            amount=-amount,
            transaction_type=TransactionType.PURCHASE,
            operation_key=operation_key,
            source_platform=source_platform,
            issuing_entity=issuing_entity,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )


def purchase_item(
    user,
    shop_item,
    *,
    operation_key,
    deliver: Callable,
):
    """
    Ejecuta una compra local.

    La función deliver representa el límite de integración
    con Inventory. No debe realizar HTTP ni I/O externo dentro
    de esta transacción.
    """

    if not operation_key:
        raise ValueError(
            "operation_key es obligatoria."
        )

    with transaction.atomic():

        current_item = (
            ShopItem.objects
            .select_for_update()
            .get(pk=shop_item.pk)
        )

        if not current_item.is_available:
            raise ProductUnavailable(
                "El producto no está disponible."
            )

        existing = (
            Purchase.objects
            .select_related(
                "shop_item",
                "bank_transaction",
            )
            .filter(
                user=user,
                operation_key=operation_key,
            )
            .first()
        )

        if existing is not None:

            if existing.shop_item_id != current_item.pk:
                raise IdempotencyConflict(
                    f"La operation_key '{operation_key}' "
                    "ya fue utilizada para otro producto."
                )

            return existing

        purchase = Purchase.objects.create(
            user=user,
            shop_item=current_item,
            operation_key=operation_key,
            unit_price_coins=current_item.price_coins,
            quantity=1,
            total_price_coins=current_item.price_coins,
            status=PurchaseStatus.COMPLETED,
        )

        ledger = debit_wallet(
            user,
            purchase.total_price_coins,
            operation_key=f"purchase:{operation_key}",
            description=(
                f"Compra: {current_item.name}"
            ),
            reference_type="purchase",
            reference_id=str(purchase.pk),
        )

        # Inventory debe trabajar localmente si se desea
        # rollback dentro de esta misma transacción.
        deliver(purchase)

        purchase.bank_transaction = ledger.transaction
        purchase.save(
            update_fields=[
                "bank_transaction",
                "updated_at",
            ]
        )

        return purchase


def refund_purchase(
    purchase,
    *,
    operation_key,
    description="Reembolso de compra",
):
    if not operation_key:
        raise ValueError(
            "operation_key es obligatoria."
        )

    with transaction.atomic():

        locked_purchase = (
            Purchase.objects
            .select_for_update()
            .get(pk=purchase.pk)
        )

        if locked_purchase.status == PurchaseStatus.REFUNDED:

            existing = (
                Transaction.objects
                .filter(
                    wallet__user=locked_purchase.user,
                    transaction_type=TransactionType.REFUND,
                    reference_type="purchase",
                    reference_id=str(
                        locked_purchase.pk
                    ),
                )
                .first()
            )

            if existing is None:
                raise IdempotencyConflict(
                    "La compra aparece reembolsada "
                    "pero no existe su movimiento."
                )

            if existing.operation_key != operation_key:
                raise IdempotencyConflict(
                    "La compra ya fue reembolsada "
                    "con otra operation_key."
                )

            return LedgerResult(
                transaction=existing,
                created=False,
            )

        result = credit_wallet(
            locked_purchase.user,
            locked_purchase.total_price_coins,
            operation_key=operation_key,
            transaction_type=TransactionType.REFUND,
            description=description,
            source_platform="ducky_shop",
            issuing_entity="DuckyShop",
            reference_type="purchase",
            reference_id=str(
                locked_purchase.pk
            ),
        )

        locked_purchase.status = (
            PurchaseStatus.REFUNDED
        )

        locked_purchase.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return result


def adjust_wallet(
    user,
    amount,
    *,
    operation_key,
    description,
    source_platform="admin",
    issuing_entity="DuckyBank",
    reference_type="adjustment",
    reference_id="",
):
    if amount == 0:
        raise ValueError(
            "El ajuste no puede ser cero."
        )

    if not operation_key:
        raise ValueError(
            "operation_key es obligatoria."
        )

    with transaction.atomic():

        wallet = _wallet_for_update(user)

        return _record_transaction(
            wallet=wallet,
            amount=amount,
            transaction_type=TransactionType.ADJUSTMENT,
            operation_key=operation_key,
            source_platform=source_platform,
            issuing_entity=issuing_entity,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
        )


def wallet_summary(user):
    wallet = Wallet.objects.get(user=user)

    totals = wallet.transactions.aggregate(
        total_earned=Sum(
            "amount",
            filter=Q(amount__gt=0),
        ),
        total_spent=Sum(
            "amount",
            filter=Q(amount__lt=0),
        ),
    )

    return {
        "available_balance": wallet.available_balance,
        "total_earned": totals["total_earned"] or 0,
        "total_spent": abs(
            totals["total_spent"] or 0
        ),
    }


def transaction_history(
    user,
    *,
    transaction_type=None,
    source_platform=None,
):
    queryset = Transaction.objects.filter(
        wallet__user=user
    )

    if transaction_type:
        queryset = queryset.filter(
            transaction_type=transaction_type
        )

    if source_platform:
        queryset = queryset.filter(
            source_platform=source_platform
        )

    return queryset.order_by(
        "-created_at",
        "-id",
    )
