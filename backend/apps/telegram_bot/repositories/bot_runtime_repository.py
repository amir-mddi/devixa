from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.apps.telegram_bot.repositories.adapters.bot_runtime_adapter import BotRuntimeAdapter


class BotRuntimeRepository:
    def __init__(self, service_factory: Callable[[], Any]):
        self.adapter = BotRuntimeAdapter(service_factory=service_factory)

    async def process_update(self, update: dict[str, Any]) -> None:
        await self.adapter.process_update(update)
