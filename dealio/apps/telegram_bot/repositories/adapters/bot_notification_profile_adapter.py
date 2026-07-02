from __future__ import annotations

from collections.abc import Iterable

from dealio.apps.telegram_bot.dtos.bot_notification_dtos import BotNotificationRecipientDTO
from dealio.apps.telegram_bot.models import TelegramProfile


class BotNotificationProfileAdapter:
    """Reads bot recipients from TelegramProfile.

    A recipient is a linked, verified, active bot profile. Keeping this lookup in
    an adapter makes the notification flow independent from the Telegram service
    orchestration and cheap to reuse for other providers later.
    """

    @staticmethod
    def list_linked_active_recipients(*, provider: str) -> list[BotNotificationRecipientDTO]:
        queryset = (
            TelegramProfile.objects
            .filter(
                messenger_provider=provider,
                is_active=True,
                is_verified=True,
                user__isnull=False,
            )
            .exclude(chat_id="")
            .order_by("chat_id")
            .values_list("chat_id", flat=True)
            .distinct()
        )
        return [BotNotificationRecipientDTO(provider=provider, chat_id=str(chat_id)) for chat_id in queryset]

    @staticmethod
    def count_linked_active_recipients(*, provider: str) -> int:
        return (
            TelegramProfile.objects
            .filter(
                messenger_provider=provider,
                is_active=True,
                is_verified=True,
                user__isnull=False,
            )
            .exclude(chat_id="")
            .values("chat_id")
            .distinct()
            .count()
        )

    @staticmethod
    def deactivate_recipients(*, provider: str, chat_ids: Iterable[str]) -> int:
        normalized_chat_ids = [str(chat_id) for chat_id in chat_ids if str(chat_id).strip()]
        if not normalized_chat_ids:
            return 0
        return (
            TelegramProfile.objects
            .filter(messenger_provider=provider, chat_id__in=normalized_chat_ids)
            .update(is_active=False)
        )
