from __future__ import annotations

from typing import Any

from dealio.apps.telegram_bot.models import TelegramProfile
from dealio.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import TelegramBotPostgresAdapter


class TelegramProfileRepository:
    def __init__(self, adapter: TelegramBotPostgresAdapter | None = None):
        self.adapter = adapter or TelegramBotPostgresAdapter()

    def upsert_profile(self, *, provider: str, chat_id: str | int, user_data: dict[str, Any]) -> TelegramProfile:
        return self.adapter.upsert_profile(provider=provider, chat_id=chat_id, user_data=user_data)

    def get_profile_language(self, *, provider: str, chat_id: str | int) -> str | None:
        return self.adapter.get_profile_language(provider=provider, chat_id=chat_id)

    @classmethod
    def upsert(cls, *, provider: str, chat_id: str | int, user_data: dict[str, Any]) -> TelegramProfile:
        return cls().upsert_profile(provider=provider, chat_id=chat_id, user_data=user_data)

    @classmethod
    def language(cls, *, provider: str, chat_id: str | int) -> str | None:
        return cls().get_profile_language(provider=provider, chat_id=chat_id)
