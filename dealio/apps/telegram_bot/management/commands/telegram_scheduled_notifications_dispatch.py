from django.core.management.base import BaseCommand

from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import BotNotificationLogicRepository


class Command(BaseCommand):
    help = "Send due Telegram scheduled bot notifications. Run from cron/Celery beat every minute."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        client = TelegramBotClient()
        logic = BotNotificationLogicRepository()
        due = logic.list_due_scheduled_notifications(provider="telegram", limit=options["limit"])
        if not due:
            self.stdout.write("No due scheduled notifications.")
            return
        for notification in due:
            result = logic.deliver_scheduled_notification(client=client, notification=notification)
            self.stdout.write(
                self.style.SUCCESS(
                    f"notification={notification.id} recipients={result.total_count} delivered={result.success_count} failed={result.failed_count}"
                )
            )
