from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.apps.telegram_bot.models import TelegramUpdateLog
from backend.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import TelegramBotPostgresAdapter


class TelegramUpdateLogRepository:
    def __init__(self, adapter: TelegramBotPostgresAdapter | None = None):
        self.adapter = adapter or TelegramBotPostgresAdapter()

    async def get_or_create(
        self,
        *,
        provider: str,
        update_id: str | int,
        payload: dict[str, Any],
    ) -> tuple[TelegramUpdateLog, bool]:
        return await self.adapter.aget_or_create_update_log(
            provider=provider,
            update_id=update_id,
            payload=payload,
        )

    async def mark_processed(self, update_log: TelegramUpdateLog) -> None:
        await self.adapter.amark_update_processed(update_log)

    async def mark_error(self, update_log: TelegramUpdateLog, error_text: str) -> None:
        await self.adapter.amark_update_error(update_log, error_text)

    async def cleanup_before(self, cutoff: datetime) -> int:
        return await self.adapter.adelete_update_logs_before(cutoff)
