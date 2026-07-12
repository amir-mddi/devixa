from __future__ import annotations

from typing import Any

from datetime import datetime

from dealio.apps.telegram_bot.models import TelegramUpdateLog
from dealio.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import TelegramBotPostgresAdapter


class TelegramUpdateLogRepository:
    def __init__(self, adapter: TelegramBotPostgresAdapter | None = None):
        self.adapter = adapter or TelegramBotPostgresAdapter()

    def get_or_create(self, *, provider: str, update_id: str | int, payload: dict[str, Any]) -> tuple[TelegramUpdateLog, bool]:
        return self.adapter.get_or_create_update_log(provider=provider, update_id=update_id, payload=payload)

    def mark_processed(self, update_log: TelegramUpdateLog) -> None:
        self.adapter.mark_update_processed(update_log)

    def mark_error(self, update_log: TelegramUpdateLog, error_text: str) -> None:
        self.adapter.mark_update_error(update_log, error_text)

    def cleanup_before(self, cutoff: datetime) -> int:
        return self.adapter.delete_update_logs_before(cutoff)
