from __future__ import annotations

from backend.apps.common.utils.common_utils import CommonUtils
import time
from typing import Any, Callable

from backend.apps.telegram_bot.controllers.update_controller import BotUpdateController
from backend.apps.telegram_bot.repositories.bot_cache_repository import TelegramBotCacheRepository

logger = CommonUtils.get_project_logger(__name__)


class RubikaPollingService:
    """Rubika polling service.

    Rubika uses offset_id / next_offset_id instead of Telegram update_id + 1.
    Offset persistence is isolated in the cache repository.
    """

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

    def drop_pending(self, *, limit: int) -> None:
        _, next_offset_id = self.client.get_updates(limit=limit)
        self.cache_repository.set(self.CACHE_KEY, next_offset_id, timeout=None)

    def run_forever(self, *, limit: int, sleep_seconds: float) -> None:
        offset_id = self.cache_repository.get(self.CACHE_KEY)

        while True:
            try:
                updates, next_offset_id = self.client.get_updates(offset_id=offset_id, limit=limit)
                for update in updates:
                    self.controller.handle(update)

                if next_offset_id:
                    offset_id = next_offset_id
                    self.cache_repository.set(self.CACHE_KEY, offset_id, timeout=None)

                time.sleep(sleep_seconds)
            except KeyboardInterrupt:
                raise
            except Exception:
                logger.exception("%s polling error", self.provider)
                time.sleep(max(sleep_seconds, 3.0))
