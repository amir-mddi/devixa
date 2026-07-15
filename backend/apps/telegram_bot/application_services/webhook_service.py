from __future__ import annotations

import hmac
from typing import Any, Callable

from backend.apps.telegram_bot.controllers.update_controller import BotUpdateController


class BotWebhookService:
    """Webhook application service for Telegram/Bale/Rubika."""

    def __init__(
        self,
        *,
        provider: str,
        service_factory: Callable[[], Any],
        update_id_getter: Callable[[dict[str, Any]], str | int | None],
    ):
        self.controller = BotUpdateController(
            provider=provider,
            service_factory=service_factory,
            update_id_getter=update_id_getter,
        )

    @staticmethod
    def validate_secret(*, expected_secret: str, provided_secret: str) -> bool:
        if not expected_secret:
            return False
        return hmac.compare_digest(provided_secret or "", expected_secret)

    def process(self, update: dict[str, Any]) -> bool:
        return self.controller.handle(update)
