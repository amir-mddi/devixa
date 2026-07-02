from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.application_services.polling_service import BotPollingService
from dealio.apps.telegram_bot.bale_services import BaleBotClient, BaleBotService
from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider


class Command(BaseCommand):
    help = "Run Bale bot with long polling."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=None, help="Bale polling timeout in seconds. Reads BALE_POLLING_TIMEOUT when omitted.")
        parser.add_argument("--limit", type=int, default=None, help="Bale polling limit. Reads BALE_POLLING_LIMIT when omitted.")
        parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds after errors.")
        parser.add_argument("--drop-pending", action="store_true", help="Drop old Bale updates before polling starts.")

    def handle(self, *args, **options):
        client = BaleBotClient()
        if not client.is_configured:
            raise CommandError("BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required.")

        timeout = options["timeout"] if options["timeout"] is not None else BotRuntimeConfigProvider.get_int(
            BotSettingProviderEnum.BALE.value, "polling_timeout", 30
        )
        limit = options["limit"] if options["limit"] is not None else BotRuntimeConfigProvider.get_int(
            BotSettingProviderEnum.BALE.value, "polling_limit", 50
        )

        self.stdout.write(self.style.SUCCESS("Bale polling started. Press Ctrl+C to stop."))

        polling_service = BotPollingService(
            provider=BaleBotService.MESSENGER_PROVIDER,
            client=client,
            service_factory=lambda: BaleBotService(client=client),
            update_id_getter=lambda update: update.get("update_id"),
        )

        try:
            polling_service.run_forever(
                timeout=timeout,
                sleep_seconds=options["sleep"],
                drop_pending=options["drop_pending"],
                allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
                limit=limit,
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bale polling stopped."))
