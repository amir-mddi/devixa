from __future__ import annotations

from dealio.apps.common.utils.common_utils import CommonUtils
from typing import Any
from django.utils.timezone import now

from dealio.apps.telegram_bot.dtos.bot_notification_dtos import (
    BotNotificationDeliveryFailureDTO,
    BotNotificationDeliveryResultDTO,
)
from dealio.apps.telegram_bot.interfaces.bot_client_interface import BotClientInterface
from dealio.apps.telegram_bot.repositories.bot_notification_repository import BotNotificationRepository
from dealio.apps.telegram_bot.models import BotScheduledNotification

logger = CommonUtils.get_project_logger(__name__)


class BotNotificationLogicRepository:
    """Application logic for admin bot broadcasts.

    TelegramBotService owns the conversation. This class owns recipient lookup,
    delivery loop and inactive-recipient cleanup so the flow remains reusable
    outside services.py.
    """

    BLOCKED_RECIPIENT_ERROR_HINTS = (
        "bot was blocked",
        "user is deactivated",
        "chat not found",
        "forbidden",
    )

    def __init__(self, repository: BotNotificationRepository | None = None):
        self.repository = repository or BotNotificationRepository()

    def linked_recipient_count(self, *, provider: str) -> int:
        return self.repository.count_linked_active_recipients(provider=provider)

    def broadcast_to_linked_recipients(
        self,
        *,
        client: BotClientInterface,
        provider: str,
        message: str,
        disable_web_page_preview: bool = True,
    ) -> BotNotificationDeliveryResultDTO:
        recipients = self.repository.list_linked_active_recipients(provider=provider)
        failures: list[BotNotificationDeliveryFailureDTO] = []
        blocked_chat_ids: list[str] = []
        success_count = 0

        for recipient in recipients:
            try:
                client.send_message(
                    recipient.chat_id,
                    message,
                    disable_web_page_preview=disable_web_page_preview,
                )
                success_count += 1
            except Exception as exc:
                error = str(exc)
                failures.append(BotNotificationDeliveryFailureDTO(chat_id=recipient.chat_id, error=error[:500]))
                if self._is_blocked_recipient_error(error):
                    blocked_chat_ids.append(recipient.chat_id)
                logger.warning(
                    "Bot notification delivery failed.",
                    extra={"provider": provider, "chat_id": recipient.chat_id, "error": error[:500]},
                )

        if blocked_chat_ids:
            self.repository.deactivate_recipients(provider=provider, chat_ids=blocked_chat_ids)

        return BotNotificationDeliveryResultDTO(
            total_count=len(recipients),
            success_count=success_count,
            failed_count=len(failures),
            failures=failures,
        )


    def schedule_notification(self, *, provider: str, message: str, scheduled_at, created_by=None) -> BotScheduledNotification:
        recipient_count = self.linked_recipient_count(provider=provider)
        return BotScheduledNotification.objects.create(
            provider=provider,
            message=message,
            scheduled_at=scheduled_at,
            recipient_count=recipient_count,
            created_by=created_by,
        )

    def list_due_scheduled_notifications(self, *, provider: str = "telegram", limit: int = 50):
        return list(
            BotScheduledNotification.objects.filter(
                provider=provider,
                status=BotScheduledNotification.STATUS_PENDING,
                scheduled_at__lte=now(),
            ).order_by("scheduled_at")[:limit]
        )

    def deliver_scheduled_notification(self, *, client: BotClientInterface, notification: BotScheduledNotification):
        notification.status = BotScheduledNotification.STATUS_PROCESSING
        notification.save(update_fields=["status", "updated_at"])
        try:
            result = self.broadcast_to_linked_recipients(
                client=client,
                provider=notification.provider,
                message=notification.message,
            )
            notification.recipient_count = result.total_count
            notification.success_count = result.success_count
            notification.failed_count = result.failed_count
            notification.status = BotScheduledNotification.STATUS_SENT
            notification.sent_at = now()
            notification.last_error = ""
            notification.save(update_fields=["recipient_count", "success_count", "failed_count", "status", "sent_at", "last_error", "updated_at"])
            return result
        except Exception as exc:
            notification.status = BotScheduledNotification.STATUS_FAILED
            notification.last_error = str(exc)[:1000]
            notification.save(update_fields=["status", "last_error", "updated_at"])
            raise

    @classmethod
    def _is_blocked_recipient_error(cls, error: str) -> bool:
        normalized_error = (error or "").lower()
        return any(hint in normalized_error for hint in cls.BLOCKED_RECIPIENT_ERROR_HINTS)
