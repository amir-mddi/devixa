from decimal import Decimal, InvalidOperation

from django import template

from backend.apps.billing.vo import BasketWebStatusLabelVO

register = template.Library()


@register.filter
def billing_money(value, currency="irr"):
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")
    if amount <= 0:
        return "رایگان"
    label = "ریال" if str(currency).lower() == "irr" else str(currency).upper()
    return f"{int(amount):,} {label}"


@register.filter
def payment_status_label(value):
    return BasketWebStatusLabelVO.PAYMENT.get(str(value), str(value))


@register.filter
def receipt_status_label(value):
    return BasketWebStatusLabelVO.RECEIPT.get(str(value), str(value))


@register.filter
def status_class(value):
    mapping = {
        "succeeded": "is-success",
        "approved": "is-success",
        "pending_receipt": "is-warning",
        "pending_verification": "is-warning",
        "pending": "is-warning",
        "receipt_rejected": "is-danger",
        "rejected": "is-danger",
        "failed": "is-danger",
        "cancelled": "is-muted",
        "refunded": "is-muted",
    }
    return mapping.get(str(value), "is-neutral")


@register.filter
def group_card_number(value):
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if not digits:
        return "ثبت نشده"
    return " ".join(digits[index:index + 4] for index in range(0, len(digits), 4))
