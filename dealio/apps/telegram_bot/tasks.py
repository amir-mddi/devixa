import os
from datetime import timedelta

from celery import shared_task
from django.utils.timezone import now

from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import BotNotificationLogicRepository
from dealio.apps.telegram_bot.repositories.update_log_repository import TelegramUpdateLogRepository


@shared_task
def dispatch_due_telegram_scheduled_notifications(limit: int = 50):
    client = TelegramBotClient()
    logic = BotNotificationLogicRepository()
    results = []
    for notification in logic.list_due_scheduled_notifications(provider="telegram", limit=limit):
        result = logic.deliver_scheduled_notification(client=client, notification=notification)
        results.append({
            "notification_id": notification.id,
            "total": result.total_count,
            "success": result.success_count,
            "failed": result.failed_count,
        })
    return results


@shared_task
def cleanup_bot_update_logs() -> int:
    retention_days = max(1, min(int(os.environ.get("BOT_UPDATE_LOG_RETENTION_DAYS", "14")), 90))
    cutoff = now() - timedelta(days=retention_days)
    return TelegramUpdateLogRepository().cleanup_before(cutoff)
