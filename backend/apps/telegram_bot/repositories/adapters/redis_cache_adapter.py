from __future__ import annotations

from typing import Any

from django.core.cache import cache


class TelegramBotRedisCacheAdapter:
    """Redis/cache infrastructure adapter.

    Bot logic and services should depend on repositories, not on Django's cache
    object directly. This keeps Redis replaceable and testable.
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        value = cache.get(key)
        return default if value is None else value

    @staticmethod
    def set(key: str, value: Any, *, timeout: int | None = None) -> None:
        cache.set(key, value, timeout=timeout)

    @staticmethod
    def add(key: str, value: Any, *, timeout: int | None = None) -> bool:
        return cache.add(key, value, timeout=timeout)

    @staticmethod
    def delete(key: str) -> None:
        cache.delete(key)
