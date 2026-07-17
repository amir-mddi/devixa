from __future__ import annotations

from typing import Any

from django.core.cache import cache


class TelegramBotRedisCacheAdapter:
    """Sync and async cache adapter for bot state persistence."""

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

    @staticmethod
    async def aget(key: str, default: Any = None) -> Any:
        value = await cache.aget(key)
        return default if value is None else value

    @staticmethod
    async def aset(key: str, value: Any, *, timeout: int | None = None) -> None:
        await cache.aset(key, value, timeout=timeout)

    @staticmethod
    async def aadd(key: str, value: Any, *, timeout: int | None = None) -> bool:
        return await cache.aadd(key, value, timeout=timeout)

    @staticmethod
    async def adelete(key: str) -> None:
        await cache.adelete(key)
