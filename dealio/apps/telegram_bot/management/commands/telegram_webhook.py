from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider
from dealio.apps.telegram_bot.services import TelegramBotClient


class Command(BaseCommand):
    help = "Manage Telegram bot webhook."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)

        set_parser = subparsers.add_parser("set", help="Set Telegram webhook URL")
        set_parser.add_argument("--url", default=None, help="Override TELEGRAM_WEBHOOK_URL for this call")
        set_parser.add_argument("--no-drop", action="store_true", help="Do not drop pending Telegram updates")
        set_parser.add_argument("--secret", default=None, help="Override TELEGRAM_WEBHOOK_SECRET for this call")

        delete_parser = subparsers.add_parser("delete", help="Delete Telegram webhook")
        delete_parser.add_argument("--drop", action="store_true", help="Drop pending Telegram updates")

        subparsers.add_parser("info", help="Show Telegram webhook info")

    def handle(self, *args, **options):
        client = TelegramBotClient()
        if not client.is_configured:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        action = options["action"]
        if action == "set":
            url = options.get("url") or BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "webhook_url")
            if not url:
                raise CommandError("TELEGRAM_WEBHOOK_URL is required or pass --url.")
            secret = options.get("secret") or BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "webhook_secret")
            response = client.set_webhook(
                url,
                secret_token=secret or None,
                drop_pending_updates=not options["no_drop"],
            )
            self.stdout.write(self.style.SUCCESS(f"Webhook set: {response}"))
            return

        if action == "delete":
            response = client.delete_webhook(drop_pending_updates=options["drop"])
            self.stdout.write(self.style.SUCCESS(f"Webhook deleted: {response}"))
            return

        if action == "info":
            response = client.get_webhook_info()
            self.stdout.write(str(response))
