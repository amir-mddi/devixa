from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from backend.apps.common.async_utils import call_maybe_async
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.telegram_bot.controllers.update_controller import BotUpdateController

logger = CommonUtils.get_project_logger(__name__)


class BotPollingService:
    """Non-blocking polling service with async controller delegation."""

    def __init__(
        self,
        *,
        provider: str,
        client: Any,
        service_factory: Callable[[], Any],
        update_id_getter: Callable[[dict[str, Any]], str | int | None],
    ):
        self.provider = provider
        self.client = client
        self.controller = BotUpdateController(
            provider=provider,
            service_factory=service_factory,
            update_id_getter=update_id_getter,
        )

    async def run_forever(
        self,
        *,
        timeout: int = 30,
        sleep_seconds: float = 1.0,
        drop_pending: bool = False,
        allowed_updates: list[str] | None = None,
        limit: int | None = None,
    ) -> None:
        delete_webhook = getattr(
            self.client,
            "adelete_webhook",
            getattr(self.client, "delete_webhook", None),
        )
        if delete_webhook:
            await call_maybe_async(
                delete_webhook,
                drop_pending_updates=drop_pending,
            )

        offset = None
        while True:
            try:
                kwargs: dict[str, Any] = {
                    "offset": offset,
                    "timeout": timeout,
                    "allowed_updates": allowed_updates,
                }
                if limit is not None:
                    kwargs["limit"] = limit

                get_updates = getattr(
                    self.client,
                    "aget_updates",
                    self.client.get_updates,
                )
                updates = await call_maybe_async(get_updates, **kwargs)
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        offset = update_id + 1
                    await self.controller.handle(update)

            except asyncio.CancelledError:
                raise
            except KeyboardInterrupt:
                raise
            except Exception:
                logger.exception("%s polling error", self.provider)
                await asyncio.sleep(sleep_seconds)
