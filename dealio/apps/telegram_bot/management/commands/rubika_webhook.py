from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider
from dealio.apps.telegram_bot.rubika_services import RubikaBotClient


class Command(BaseCommand):
    help = "Manage Rubika bot webhook/endpoints. Polling users do not need this command."

    ENDPOINT_TYPES = ("ReceiveUpdate", "ReceiveInlineMessage")

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)
        set_parser = subparsers.add_parser("set", help="Set Rubika webhook URL for message and inline events")
        set_parser.add_argument("--url", default=None, help="Override RUBIKA_WEBHOOK_URL for this call")
        subparsers.add_parser("delete", help="Remove Rubika webhook URLs by setting empty endpoints")

    def handle(self, *args, **options):
        client = RubikaBotClient()
        if not client.is_configured:
            raise CommandError("RUBIKA_BOT_TOKEN and RUBIKA_BOT_BASE_URL are required.")

        if options["action"] == "set":
            url = options.get("url") or BotRuntimeConfigProvider.get(BotSettingProviderEnum.RUBIKA.value, "webhook_url")
            if not url:
                raise CommandError("RUBIKA_WEBHOOK_URL is required or pass --url.")
            for endpoint_type in self.ENDPOINT_TYPES:
                response = client.update_bot_endpoint(url=url, endpoint_type=endpoint_type)
                self.stdout.write(self.style.SUCCESS(f"Rubika endpoint set for {endpoint_type}: {response}"))
            return

        if options["action"] == "delete":
            for endpoint_type in self.ENDPOINT_TYPES:
                response = client.update_bot_endpoint(url="", endpoint_type=endpoint_type)
                self.stdout.write(self.style.SUCCESS(f"Rubika endpoint cleared for {endpoint_type}: {response}"))
