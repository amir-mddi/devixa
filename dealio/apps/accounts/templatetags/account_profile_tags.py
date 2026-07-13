from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import template

from dealio.apps.accounts.vo.profile_vo import AccountProfileStatusLabelVO

register = template.Library()


_STATUS_MAPS = {
    "order": AccountProfileStatusLabelVO.ORDER,
    "payment": AccountProfileStatusLabelVO.PAYMENT,
    "enrollment": AccountProfileStatusLabelVO.ENROLLMENT,
    "review": AccountProfileStatusLabelVO.REVIEW,
    "ticket": AccountProfileStatusLabelVO.TICKET,
    "receipt": AccountProfileStatusLabelVO.RECEIPT,
    "provider": AccountProfileStatusLabelVO.PROVIDER,
}


@register.filter
def profile_status_label(value, status_type: str) -> str:
    normalized = str(value or "")
    return _STATUS_MAPS.get(status_type, {}).get(normalized, normalized or "—")


@register.filter
def profile_status_class(value) -> str:
    normalized = str(value or "").replace("_", "-")
    return f"status-{normalized}" if normalized else "status-unknown"


@register.filter
def profile_provider_label(value) -> str:
    normalized = str(value or "")
    return AccountProfileStatusLabelVO.PROVIDER.get(normalized, normalized or "—")


@register.filter
def profile_money(value, currency: str = "irr") -> str:
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")
    label = AccountProfileStatusLabelVO.CURRENCY.get(str(currency or ""), str(currency or ""))
    return f"{amount:,.0f} {label}".strip()


@register.filter
def dict_get(mapping, key):
    if not mapping:
        return None
    return mapping.get(str(key))


@register.filter
def support_sender_label(value: str) -> str:
    return {
        "user": "شما",
        "admin": "پشتیبانی",
        "system": "سیستم",
    }.get(str(value or ""), "پیام")
