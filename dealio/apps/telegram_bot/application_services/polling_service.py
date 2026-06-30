from __future__ import annotations

import logging
import time
from typing import Any, Callable

from dealio.apps.telegram_bot.controllers.update_controller import BotUpdateController

logger = logging.getLogger("dealio")


class BotPollingService:
    """Polling application service.

    It fetches raw updates from a messenger API adapter and delegates processing
    to a controller. It does not know business rules or database details.
    """

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

    def run_forever(
        self,
        *,
        timeout: int = 30,
        sleep_seconds: float = 1.0,
        drop_pending: bool = False,
        allowed_updates: list[str] | None = None,
        limit: int | None = None,
    ) -> None:
        if hasattr(self.client, "delete_webhook"):
            self.client.delete_webhook(drop_pending_updates=drop_pending)

        offset = None
        while True:
            try:
                kwargs = {"offset": offset, "timeout": timeout, "allowed_updates": allowed_updates}
                if limit is not None:
                    kwargs["limit"] = limit
                updates = self.client.get_updates(**kwargs)
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        offset = update_id + 1
                    self.controller.handle(update)

            except KeyboardInterrupt:
                raise
            except Exception:
                logger.exception("%s polling error", self.provider)
                time.sleep(sleep_seconds)
