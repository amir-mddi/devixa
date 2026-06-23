import time

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.services import TelegramBotClient, TelegramBotService


class Command(BaseCommand):
    help = "Run Telegram bot with long polling for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Telegram long polling timeout in seconds.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=1.0,
            help="Sleep seconds after errors.",
        )
        parser.add_argument(
            "--drop-pending",
            action="store_true",
            help="Drop old Telegram updates before polling starts.",
        )

    def handle(self, *args, **options):
        client = TelegramBotClient()

        if not client.is_configured:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        # Telegram cannot use webhook and polling at the same time.
        # For local development, remove webhook first.
        client.delete_webhook(drop_pending_updates=options["drop_pending"])

        service = TelegramBotService(client=client)
        offset = None

        self.stdout.write(
            self.style.SUCCESS("Telegram polling started. Press Ctrl+C to stop.")
        )

        while True:
            try:
                updates = client.get_updates(
                    offset=offset,
                    timeout=options["timeout"],
                    allowed_updates=["message", "edited_message", "callback_query"],
                )

                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        offset = update_id + 1

                    service.handle_update(update)

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("Telegram polling stopped."))
                break

            except Exception as exc:
                self.stderr.write(f"Polling error: {exc}")
                time.sleep(options["sleep"])
