from __future__ import annotations

from dealio.apps.telegram_bot.repositories.adapters.bot_setting_cache_adapter import BotSettingCacheAdapter
from dealio.apps.telegram_bot.repositories.adapters.bot_setting_crypto_adapter import BotSettingCryptoAdapter
from dealio.apps.telegram_bot.repositories.adapters.bot_setting_postgres_adapter import BotSettingPostgresAdapter


class BotSettingRepository:
    """Repository coordinating cache, postgres and secret encoding."""

    def __init__(
        self,
        *,
        postgres_adapter: type[BotSettingPostgresAdapter] = BotSettingPostgresAdapter,
        cache_adapter: type[BotSettingCacheAdapter] = BotSettingCacheAdapter,
        crypto_adapter: type[BotSettingCryptoAdapter] = BotSettingCryptoAdapter,
    ) -> None:
        self.postgres_adapter = postgres_adapter
        self.cache_adapter = cache_adapter
        self.crypto_adapter = crypto_adapter

    def get_value(self, *, provider: str, key: str, is_secret: bool = False) -> str | None:
        cached = self.cache_adapter.get(provider, key)
        if cached is not None:
            return self.crypto_adapter.decode(cached) if is_secret else cached

        value = self.postgres_adapter.get_value(provider=provider, key=key)
        if value is None:
            return None

        self.cache_adapter.set(provider, key, value)
        return self.crypto_adapter.decode(value) if is_secret else value

    def set_value(self, *, provider: str, key: str, value: str, is_secret: bool = False, user=None) -> None:
        stored_value = self.crypto_adapter.encode(value) if is_secret else value
        self.postgres_adapter.upsert_value(
            provider=provider,
            key=key,
            value=stored_value,
            is_secret=is_secret,
            user=user,
        )
        self.cache_adapter.delete(provider, key)

    def delete_value(self, *, provider: str, key: str, user=None) -> bool:
        deleted = self.postgres_adapter.delete_value(provider=provider, key=key, user=user)
        self.cache_adapter.delete(provider, key)
        return deleted
