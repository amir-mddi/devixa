from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.apps.telegram_bot.dtos.bot_update_dtos import BotUpdateProcessDTO
from backend.apps.telegram_bot.logic.update_process_logic import BotUpdateProcessLogic
from backend.apps.telegram_bot.repositories.bot_runtime_repository import BotRuntimeRepository


class BotUpdateController:
    """Thin async controller for webhook and polling update processing."""

    def __init__(
        self,
        *,
        provider: str,
        service_factory: Callable[[], Any],
        update_id_getter: Callable[[dict[str, Any]], str | int | None],
    ):
        self.provider = provider
        self.update_id_getter = update_id_getter
        self.logic = BotUpdateProcessLogic(
            runtime_repository=BotRuntimeRepository(service_factory=service_factory),
        )

    async def handle(self, update: dict[str, Any]) -> bool:
        return await self.logic.process(
            BotUpdateProcessDTO(
                provider=self.provider,
                update=update,
                update_id=self.update_id_getter(update),
            )
        )
