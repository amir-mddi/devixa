from __future__ import annotations

from typing import Any, Callable

from dealio.apps.telegram_bot.repositories.adapters.bot_runtime_adapter import BotRuntimeAdapter


class BotRuntimeRepository:
    def __init__(self, service_factory: Callable[[], Any]):
        self.adapter = BotRuntimeAdapter(service_factory=service_factory)

    def process_update(self, update: dict[str, Any]) -> None:
        self.adapter.process_update(update)
