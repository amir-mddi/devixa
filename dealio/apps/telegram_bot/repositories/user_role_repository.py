from __future__ import annotations

from dealio.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import TelegramBotPostgresAdapter


class TelegramUserRoleRepository:
    def __init__(self, adapter: TelegramBotPostgresAdapter | None = None):
        self.adapter = adapter or TelegramBotPostgresAdapter()

    def ensure_default_user_role(self) -> None:
        self.adapter.ensure_default_user_role()

    @classmethod
    def ensure_default_user(cls) -> None:
        cls().ensure_default_user_role()
