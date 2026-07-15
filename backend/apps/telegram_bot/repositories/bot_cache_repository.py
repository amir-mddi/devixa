from __future__ import annotations

from typing import Any

from backend.apps.telegram_bot.repositories.adapters.redis_cache_adapter import TelegramBotRedisCacheAdapter


class TelegramBotCacheRepository:
    """Repository for short-lived bot states stored in Redis/cache."""

    def __init__(self, adapter: TelegramBotRedisCacheAdapter | None = None):
        self.adapter = adapter or TelegramBotRedisCacheAdapter()

    def get(self, key: str, default: Any = None) -> Any:
        return self.adapter.get(key, default)

    def set(self, key: str, value: Any, *, timeout: int | None = None) -> None:
        self.adapter.set(key, value, timeout=timeout)

    def add(self, key: str, value: Any, *, timeout: int | None = None) -> bool:
        return self.adapter.add(key, value, timeout=timeout)

    def delete(self, key: str) -> None:
        self.adapter.delete(key)

    @classmethod
    def get_value(cls, key: str, default: Any = None) -> Any:
        return cls().get(key, default)

    @classmethod
    def set_value(cls, key: str, value: Any, *, timeout: int | None = None) -> None:
        cls().set(key, value, timeout=timeout)

    @classmethod
    def add_value(cls, key: str, value: Any, *, timeout: int | None = None) -> bool:
        return cls().add(key, value, timeout=timeout)

    @classmethod
    def delete_value(cls, key: str) -> None:
        cls().delete(key)
