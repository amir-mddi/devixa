from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from backend.apps.telegram_bot.services import TelegramBotService
from backend.apps.telegram_bot.factories.service_factory import TelegramBotServiceFactory
from backend.apps.telegram_bot.application_services.polling_service import BotPollingService


class Command(BaseCommand):
    help = "Run Telegram bot with long polling."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=30, help="Telegram long polling timeout in seconds.")
        parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds after errors.")
        parser.add_argument("--drop-pending", action="store_true", help="Drop old Telegram updates before polling starts.")

    def handle(self, *args, **options):
        client = TelegramBotClient()
        if not client.is_configured:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        self.stdout.write(self.style.SUCCESS("Telegram polling started. Press Ctrl+C to stop."))

        polling_service = BotPollingService(
            provider=TelegramBotService.MESSENGER_PROVIDER,
            client=client,
            service_factory=lambda: TelegramBotServiceFactory.create(client=client),
            update_id_getter=lambda update: update.get("update_id"),
        )

        try:
            polling_service.run_forever(
                timeout=options["timeout"],
                sleep_seconds=options["sleep"],
                drop_pending=options["drop_pending"],
                allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Telegram polling stopped."))
