from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import urlsplit

SentryEvent = dict[str, Any]
BeforeSendHook = Callable[[SentryEvent, dict[str, Any]], SentryEvent | None]
BeforeTransactionHook = Callable[[SentryEvent, dict[str, Any]], SentryEvent | None]


def _normalize_prefixes(prefixes: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for raw_prefix in prefixes:
        prefix = raw_prefix.strip()
        if not prefix:
            continue
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        normalized.append(prefix)
    return tuple(dict.fromkeys(normalized))


def _request_path(event: SentryEvent) -> str:
    request = event.get("request") or {}
    url = request.get("url") or ""
    if not isinstance(url, str):
        return ""
    return urlsplit(url).path


def _transaction_name(event: SentryEvent) -> str:
    transaction = event.get("transaction") or ""
    return transaction if isinstance(transaction, str) else ""


def _matches_ignored_path(event: SentryEvent, prefixes: tuple[str, ...]) -> bool:
    path = _request_path(event)
    transaction = _transaction_name(event)
    return any(
        value.startswith(prefix)
        for prefix in prefixes
        for value in (path, transaction)
        if value
    )


def build_before_send(
    ignored_path_prefixes: Iterable[str],
) -> BeforeSendHook:
    prefixes = _normalize_prefixes(ignored_path_prefixes)

    def before_send(event: SentryEvent, hint: dict[str, Any]) -> SentryEvent | None:
        del hint
        if prefixes and _matches_ignored_path(event, prefixes):
            return None
        return event

    return before_send


def build_before_send_transaction(
    ignored_path_prefixes: Iterable[str],
) -> BeforeTransactionHook:
    prefixes = _normalize_prefixes(ignored_path_prefixes)

    def before_send_transaction(
        event: SentryEvent,
        hint: dict[str, Any],
    ) -> SentryEvent | None:
        del hint
        if prefixes and _matches_ignored_path(event, prefixes):
            return None
        return event

    return before_send_transaction
