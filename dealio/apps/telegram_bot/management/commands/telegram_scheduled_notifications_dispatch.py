from django.core.management.base import BaseCommand

from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.adapters.bot_client_factory import (
    BotClientFactory,
)
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import (
    BotNotificationLogicRepository,
)


class Command(BaseCommand):
    help = "Send due scheduled bot notifications for Telegram, Bale, and Rubika."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument(
            "--provider",
            choices=(
                BotSettingProviderEnum.TELEGRAM.value,
                BotSettingProviderEnum.BALE.value,
                BotSettingProviderEnum.RUBIKA.value,
                "all",
            ),
            default="all",
        )

    def handle(self, *args, **options):
        providers = (
            BotClientFactory.supported_providers()
            if options["provider"] == "all"
            else (options["provider"],)
        )
        logic = BotNotificationLogicRepository()
        delivered_any = False

        for provider in providers:
            due = logic.list_due_scheduled_notifications(
                provider=provider,
                limit=options["limit"],
            )
            if not due:
                continue

            try:
                client = BotClientFactory.create(provider)
            except (ValueError, RuntimeError) as exc:
                self.stderr.write(
                    self.style.WARNING(f"provider={provider} skipped: {exc}")
                )
                continue

            for notification in due:
                result = logic.deliver_scheduled_notification(
                    client=client,
                    notification=notification,
                )
                delivered_any = True
                self.stdout.write(
                    self.style.SUCCESS(
                        f"provider={provider} notification={notification.id} "
                        f"recipients={result.total_count} delivered={result.success_count} "
                        f"failed={result.failed_count}"
                    )
                )

        if not delivered_any:
            self.stdout.write("No due scheduled notifications.")
