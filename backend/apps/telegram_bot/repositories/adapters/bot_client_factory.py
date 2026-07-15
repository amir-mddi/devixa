from __future__ import annotations

from backend.apps.telegram_bot.bale_services import BaleBotClient
from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from backend.apps.telegram_bot.interfaces.bot_client_interface import BotClientInterface
from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import (
    TelegramBotClient,
)
from backend.apps.telegram_bot.rubika_services import RubikaBotClient


class BotClientFactory:
    """Build configured messenger clients without leaking provider details to use cases."""

    CLIENTS = {
        BotSettingProviderEnum.TELEGRAM.value: TelegramBotClient,
        BotSettingProviderEnum.BALE.value: BaleBotClient,
        BotSettingProviderEnum.RUBIKA.value: RubikaBotClient,
    }

    @classmethod
    def create(cls, provider: str) -> BotClientInterface:
        normalized_provider = (provider or "").strip().lower()
        client_class = cls.CLIENTS.get(normalized_provider)
        if client_class is None:
            raise ValueError("Unsupported messenger provider.")

        client = client_class()
        if not client.is_configured:
            raise RuntimeError("Selected messenger bot is not configured.")
        return client

    @classmethod
    def supported_providers(cls) -> tuple[str, ...]:
        return tuple(cls.CLIENTS)
