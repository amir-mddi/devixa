from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from backend.apps.common.async_utils import call_maybe_async
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.telegram_bot.controllers.update_controller import BotUpdateController
from backend.apps.telegram_bot.repositories.bot_cache_repository import TelegramBotCacheRepository

logger = CommonUtils.get_project_logger(__name__)


class RubikaPollingService:
    """Async Rubika polling service with persisted next-offset state."""

    CACHE_KEY = "rubika_polling_next_offset_id"

    def __init__(
        self,
        *,
        provider: str,
        client: Any,
        service_factory: Callable[[], Any],
        update_id_getter: Callable[[dict[str, Any]], str | int | None],
        cache_repository: TelegramBotCacheRepository | None = None,
    ):
        self.provider = provider
        self.client = client
        self.cache_repository = cache_repository or TelegramBotCacheRepository()
        self.controller = BotUpdateController(
            provider=provider,
            service_factory=service_factory,
            update_id_getter=update_id_getter,
        )

    async def drop_pending(self, *, limit: int) -> None:
        get_updates = getattr(self.client, "aget_updates", self.client.get_updates)
        _, next_offset_id = await call_maybe_async(get_updates, limit=limit)
        await self.cache_repository.aset(
            self.CACHE_KEY,
            next_offset_id,
            timeout=None,
        )

    async def run_forever(self, *, limit: int, sleep_seconds: float) -> None:
        offset_id = await self.cache_repository.aget(self.CACHE_KEY)

        while True:
            try:
                get_updates = getattr(
                    self.client,
                    "aget_updates",
                    self.client.get_updates,
                )
                updates, next_offset_id = await call_maybe_async(
                    get_updates,
                    offset_id=offset_id,
                    limit=limit,
                )
                for update in updates:
                    await self.controller.handle(update)

                if next_offset_id:
                    offset_id = next_offset_id
                    await self.cache_repository.aset(
                        self.CACHE_KEY,
                        offset_id,
                        timeout=None,
                    )

                await asyncio.sleep(sleep_seconds)
            except asyncio.CancelledError:
                raise
            except KeyboardInterrupt:
                raise
            except Exception:
                logger.exception("%s polling error", self.provider)
                await asyncio.sleep(max(sleep_seconds, 3.0))
