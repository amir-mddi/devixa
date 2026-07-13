import os
from datetime import timedelta

from celery import shared_task
from django.utils.timezone import now

from dealio.apps.telegram_bot.repositories.adapters.bot_client_factory import (
    BotClientFactory,
)
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import (
    BotNotificationLogicRepository,
)
from dealio.apps.telegram_bot.repositories.update_log_repository import (
    TelegramUpdateLogRepository,
)


def _dispatch_due_bot_scheduled_notifications(*, limit: int, provider: str):
    providers = (
        BotClientFactory.supported_providers() if provider == "all" else (provider,)
    )
    logic = BotNotificationLogicRepository()
    results = []

    for current_provider in providers:
        due_notifications = logic.list_due_scheduled_notifications(
            provider=current_provider,
            limit=limit,
        )
        if not due_notifications:
            continue

        try:
            client = BotClientFactory.create(current_provider)
        except (ValueError, RuntimeError) as exc:
            results.append(
                {
                    "provider": current_provider,
                    "error": str(exc),
                }
            )
            continue

        for notification in due_notifications:
            result = logic.deliver_scheduled_notification(
                client=client,
                notification=notification,
            )
            results.append(
                {
                    "provider": current_provider,
                    "notification_id": notification.id,
                    "total": result.total_count,
                    "success": result.success_count,
                    "failed": result.failed_count,
                }
            )
    return results


@shared_task
def dispatch_due_bot_scheduled_notifications(limit: int = 50, provider: str = "all"):
    return _dispatch_due_bot_scheduled_notifications(limit=limit, provider=provider)


@shared_task
def dispatch_due_telegram_scheduled_notifications(limit: int = 50):
    """Backward-compatible task name for existing Celery beat schedules."""

    return _dispatch_due_bot_scheduled_notifications(limit=limit, provider="telegram")


@shared_task
def cleanup_bot_update_logs() -> int:
    retention_days = max(
        1, min(int(os.environ.get("BOT_UPDATE_LOG_RETENTION_DAYS", "14")), 90)
    )
    cutoff = now() - timedelta(days=retention_days)
    return TelegramUpdateLogRepository().cleanup_before(cutoff)
