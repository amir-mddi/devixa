from __future__ import annotations

from dealio.apps.telegram_bot.repositories.adapters.bot_client_factory import (
    BotClientFactory,
)


class AdminBotClientFactory:
    """Admin-panel adapter kept as a stable boundary over the shared bot factory."""

    @staticmethod
    def create(provider: str):
        return BotClientFactory.create(provider)
