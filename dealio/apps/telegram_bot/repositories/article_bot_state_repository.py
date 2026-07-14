from __future__ import annotations

from typing import Any

from dealio.apps.telegram_bot.repositories.bot_cache_repository import TelegramBotCacheRepository


class ArticleBotStateRepository:
    TIMEOUT_SECONDS = 30 * 60

    def __init__(self, *, cache_prefix: str):
        self.cache_prefix = cache_prefix

    def key(self, chat_id: int) -> str:
        return f"{self.cache_prefix}_article_flow:{chat_id}"

    def get(self, chat_id: int) -> dict[str, Any]:
        value = TelegramBotCacheRepository.get_value(self.key(chat_id))
        return value if isinstance(value, dict) else {}

    def set(self, chat_id: int, state: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(
            self.key(chat_id),
            state,
            timeout=self.TIMEOUT_SECONDS,
        )

    def clear(self, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(self.key(chat_id))
