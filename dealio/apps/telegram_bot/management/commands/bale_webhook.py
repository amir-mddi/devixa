import os

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.bale_services import BaleBotClient


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
            url = options.get("url") or os.environ.get("BALE_WEBHOOK_URL")
            if not url:
                raise CommandError("BALE_WEBHOOK_URL is required or pass --url.")
            secret = options.get("secret") or os.environ.get("BALE_WEBHOOK_SECRET")
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
