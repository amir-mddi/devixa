from __future__ import annotations

import logging

from django.core.cache import cache

logger = logging.getLogger("dealio")


class BotSettingCacheAdapter:
    CACHE_TIMEOUT_SECONDS = 300
    CACHE_KEY_PREFIX = "bot_runtime_setting"

    @classmethod
    def key(cls, provider: str, setting_key: str) -> str:
        return f"{cls.CACHE_KEY_PREFIX}:{provider}:{setting_key}"

    @classmethod
    def get(cls, provider: str, setting_key: str) -> str | None:
        try:
            value = cache.get(cls.key(provider, setting_key))
        except Exception:
            logger.exception("Failed to read bot runtime setting from cache.")
            return None
        return value if isinstance(value, str) else None

    @classmethod
    def set(cls, provider: str, setting_key: str, value: str) -> None:
        try:
            cache.set(cls.key(provider, setting_key), value or "", timeout=cls.CACHE_TIMEOUT_SECONDS)
        except Exception:
            logger.exception("Failed to cache bot runtime setting.")

    @classmethod
    def delete(cls, provider: str, setting_key: str) -> None:
        try:
            cache.delete(cls.key(provider, setting_key))
        except Exception:
            logger.exception("Failed to delete bot runtime setting cache.")
