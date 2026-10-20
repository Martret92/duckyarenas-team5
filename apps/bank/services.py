import hashlib
import json
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q, Sum

from .models import Transaction, TransactionType, Wallet


MAX_BALANCE = (2**63) - 1


class BankError(Exception):
    """Base exception for Bank business errors."""


class InvalidAmount(BankError):
    """The requested monetary amount is invalid."""


class WalletNotProvisioned(BankError):
    """Core provisioning has not created a wallet for this user."""


class InsufficientFunds(BankError):
    """The wallet cannot cover the requested debit."""


class IdempotencyConflict(BankError):
    """An operation key was reused with different semantic input."""


@dataclass(frozen=True)
class LedgerResult:
    transaction: Transaction
    created: bool

    @property
    def already_applied(self):
        return not self.created


def _require_operation_key(operation_key):
    if not isinstance(operation_key, str) or not operation_key.strip():
        raise ValueError("operation_key must be a non-empty string.")
    if len(operation_key) > 255:
        raise ValueError("operation_key must not exceed 255 characters.")


def _require_text(value, field_name, max_length):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters.")


def _fingerprint(*, transaction_type, amount, source, issuing_entity, reference_type, reference_id):
    semantic_input = {
        "version": 1,
        "transaction_type": transaction_type,
        "amount": amount,
        "source": source,
        "issuing_entity": issuing_entity,
        "reference_type": reference_type,
        "reference_id": reference_id,
    }
    canonical = json.dumps(
        semantic_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _get_wallet_for_update(user):
    try:
        wallet = Wallet.objects.select_for_update().get(user=user)
    except Wallet.DoesNotExist as exc:
        raise WalletNotProvisioned(
            "The user has no provisioned Bank wallet."
        ) from exc
    return wallet


def _find_existing(*, wallet, operation_key, request_fingerprint):
    existing = Transaction.objects.filter(
        wallet=wallet,
        operation_key=operation_key,
    ).first()
    if existing is None:
        return None
    if existing.request_fingerprint != request_fingerprint:
        raise IdempotencyConflict(
            f"operation_key '{operation_key}' was already used with incompatible input."
        )
    return LedgerResult(transaction=existing, created=False)


def _record_movement(
    *,
    user,
    signed_amount,
    transaction_type,
    source,
    issuing_entity,
    operation_key,
    reference_type="",
    reference_id="",
    description="",
):
    _require_operation_key(operation_key)
    _require_text(source, "source", 100)
    _require_text(issuing_entity, "issuing_entity", 100)
    if len(reference_type) > 100 or len(reference_id) > 255 or len(description) > 255:
        raise ValueError("A reference or description exceeds its maximum length.")

    fingerprint = _fingerprint(
        transaction_type=transaction_type,
        amount=signed_amount,
        source=source,
        issuing_entity=issuing_entity,
        reference_type=reference_type,
        reference_id=reference_id,
    )

    with transaction.atomic():
        wallet = _get_wallet_for_update(user)
        existing = _find_existing(
            wallet=wallet,
            operation_key=operation_key,
            request_fingerprint=fingerprint,
        )
        if existing is not None:
            return existing

        new_balance = wallet.available_balance + signed_amount
        if new_balance < 0:
            raise InsufficientFunds("The available DukiCoins balance is insufficient.")
        if new_balance > MAX_BALANCE:
            raise InvalidAmount("The resulting balance exceeds the supported range.")

        wallet.available_balance = new_balance
        wallet.save(update_fields=("available_balance", "updated_at"))

        entry = Transaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=signed_amount,
            balance_after=new_balance,
            operation_key=operation_key,
            source_platform=source,
            issuing_entity=issuing_entity,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            request_fingerprint=fingerprint,
        )
        return LedgerResult(transaction=entry, created=True)


def credit_coins(
    user,
    amount,
    *,
    source,
    operation_key,
    issuing_entity="Ecomotor",
    reference_type="",
    reference_id="",
    description="",
):
    if type(amount) is not int or amount <= 0:
        raise InvalidAmount("The credit amount must be a positive integer.")
    return _record_movement(
        user=user,
        signed_amount=amount,
        transaction_type=TransactionType.REWARD,
        source=source,
        issuing_entity=issuing_entity,
        operation_key=operation_key,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )


def debit_coins(
    user,
    amount,
    *,
    source,
    operation_key,
    issuing_entity="DuckyShop",
    reference_type="purchase",
    reference_id="",
    description="",
):
    if type(amount) is not int or amount <= 0:
        raise InvalidAmount("The debit amount must be a positive integer.")
    return _record_movement(
        user=user,
        signed_amount=-amount,
        transaction_type=TransactionType.PURCHASE,
        source=source,
        issuing_entity=issuing_entity,
        operation_key=operation_key,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )


def adjust_wallet(
    user,
    amount,
    *,
    operation_key,
    description,
    source="admin",
    issuing_entity="DuckyBank",
    reference_type="adjustment",
    reference_id="",
):
    if type(amount) is not int or amount == 0:
        raise InvalidAmount("The adjustment must be a non-zero integer.")
    if not description:
        raise ValueError("An adjustment requires a reason in description.")
    return _record_movement(
        user=user,
        signed_amount=amount,
        transaction_type=TransactionType.ADJUSTMENT,
        source=source,
        issuing_entity=issuing_entity,
        operation_key=operation_key,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
    )


def wallet_summary(user):
    wallet = Wallet.objects.get(user=user)
    totals = wallet.transactions.aggregate(
        total_earned=Sum("amount", filter=Q(amount__gt=0)),
        total_spent=Sum("amount", filter=Q(amount__lt=0)),
    )
    return {
        "available_balance": wallet.available_balance,
        "total_earned": totals["total_earned"] or 0,
        "total_spent": abs(totals["total_spent"] or 0),
    }


def transaction_history(user, *, transaction_type=None, source=None):
    queryset = Transaction.objects.filter(wallet__user=user)
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)
    if source:
        queryset = queryset.filter(source_platform=source)
    return queryset.order_by("-created_at", "-id")
