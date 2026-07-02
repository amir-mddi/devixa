from __future__ import annotations

from dealio.apps.telegram_bot.interfaces.bot_client_interface import BotClientInterface
from dealio.apps.telegram_bot.interfaces.commerce_bot_logic_interface import CommerceBotLogicInterface
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import BotNotificationLogicRepository
from dealio.apps.telegram_bot.repositories.logic.bot_support_logic import BotSupportLogicRepository
from dealio.apps.telegram_bot.repositories.logic.commerce_bot_logic import TelegramCommerceBotLogicRepository
from dealio.apps.telegram_bot.services import TelegramBotService


class TelegramBotServiceFactory:
    """Composition root for Telegram bot dependencies.

    Keep domain swaps here. For example, replacing courses with gym plans should
    be done by injecting a different CommerceBotLogicInterface implementation,
    not by changing TelegramBotService conversation logic.
    """

    @classmethod
    def create(
        cls,
        *,
        client: BotClientInterface | None = None,
        commerce_logic: CommerceBotLogicInterface | None = None,
        notification_logic: BotNotificationLogicRepository | None = None,
        support_logic: BotSupportLogicRepository | None = None,
    ) -> TelegramBotService:
        return TelegramBotService(
            client=client,
            commerce_logic=commerce_logic or TelegramCommerceBotLogicRepository(),
            notification_logic=notification_logic or BotNotificationLogicRepository(),
            support_logic=support_logic or BotSupportLogicRepository(),
        )
