from __future__ import annotations

from collections.abc import Iterable

from dealio.apps.telegram_bot.dtos.bot_notification_dtos import BotNotificationRecipientDTO
from dealio.apps.telegram_bot.repositories.adapters.bot_notification_profile_adapter import BotNotificationProfileAdapter


class BotNotificationRepository:
    def __init__(self, adapter: BotNotificationProfileAdapter | None = None):
        self.adapter = adapter or BotNotificationProfileAdapter()

    def list_linked_active_recipients(self, *, provider: str) -> list[BotNotificationRecipientDTO]:
        return self.adapter.list_linked_active_recipients(provider=provider)

    def count_linked_active_recipients(self, *, provider: str) -> int:
        return self.adapter.count_linked_active_recipients(provider=provider)

    def deactivate_recipients(self, *, provider: str, chat_ids: Iterable[str]) -> int:
        return self.adapter.deactivate_recipients(provider=provider, chat_ids=chat_ids)
