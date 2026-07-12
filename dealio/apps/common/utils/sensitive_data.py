from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_SENSITIVE_KEY_PARTS = (
    "authorization",
    "credential",
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "merchant_id",
    "token",
    "card_number",
    "account_number",
    "iban",
)


def is_sensitive_key(key: object) -> bool:
    normalized = str(key or "").strip().lower().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def sanitize_mapping(
    value: Any,
    *,
    max_depth: int = 5,
    max_items: int = 50,
    max_string_length: int = 500,
) -> Any:
    """Return a bounded, JSON-compatible copy with common secrets redacted.

    This helper is intended for audit/debug payloads persisted in the database.
    It deliberately limits recursion, collection sizes, and string lengths so an
    untrusted provider payload cannot create oversized records.
    """

    def _sanitize(item: Any, depth: int) -> Any:
        if depth > max_depth:
            return "<max-depth>"

        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            for index, (key, nested) in enumerate(item.items()):
                if index >= max_items:
                    result["<truncated>"] = True
                    break
                safe_key = str(key)[:100]
                result[safe_key] = "***" if is_sensitive_key(key) else _sanitize(nested, depth + 1)
            return result

        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            result = [_sanitize(nested, depth + 1) for nested in list(item)[:max_items]]
            if len(item) > max_items:
                result.append("<truncated>")
            return result

        if isinstance(item, bytes):
            return f"<bytes:{len(item)}>"

        if item is None or isinstance(item, (bool, int, float)):
            return item

        text = str(item)
        if len(text) > max_string_length:
            return f"{text[:max_string_length]}...(truncated)"
        return text

    return _sanitize(value, 0)
