from django.core.management.base import BaseCommand, CommandError

from backend.apps.common.utils.network_security import UnsafeOutboundUrlError, validate_public_https_url

from backend.apps.telegram_bot.bale_services import BaleBotClient
from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from backend.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider


class Command(BaseCommand):
    help = "Manage Bale bot webhook."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)

        set_parser = subparsers.add_parser("set", help="Set Bale webhook URL")
        set_parser.add_argument("--url", default=None, help="Override BALE_WEBHOOK_URL for this call")
        set_parser.add_argument("--no-drop", action="store_true", help="Do not drop pending Bale updates")
        set_parser.add_argument("--secret", default=None, help="Override BALE_WEBHOOK_SECRET for this call")

        delete_parser = subparsers.add_parser("delete", help="Delete Bale webhook")
        delete_parser.add_argument("--drop", action="store_true", help="Drop pending Bale updates")

        subparsers.add_parser("info", help="Show Bale webhook info")

    def handle(self, *args, **options):
        client = BaleBotClient()
        if not client.is_configured:
            raise CommandError("BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required.")

        action = options["action"]
        if action == "set":
            url = options.get("url") or BotRuntimeConfigProvider.get(BotSettingProviderEnum.BALE.value, "webhook_url")
            if not url:
                raise CommandError("BALE_WEBHOOK_URL is required or pass --url.")
            try:
                validate_public_https_url(url, resolve_dns=False)
            except UnsafeOutboundUrlError as exc:
                raise CommandError(str(exc)) from exc
            secret = options.get("secret") or BotRuntimeConfigProvider.get(BotSettingProviderEnum.BALE.value, "webhook_secret")
            if len(str(secret or "")) < 32:
                raise CommandError("A webhook secret of at least 32 characters is required.")
            response = client.set_webhook(
                url,
                secret_token=secret or None,
                drop_pending_updates=not options["no_drop"],
            )
            self.stdout.write(self.style.SUCCESS(f"Bale webhook set: {response}"))
            return

        if action == "delete":
            response = client.delete_webhook(drop_pending_updates=options["drop"])
            self.stdout.write(self.style.SUCCESS(f"Bale webhook deleted: {response}"))
            return

        if action == "info":
            response = client.get_webhook_info()
            self.stdout.write(str(response))
