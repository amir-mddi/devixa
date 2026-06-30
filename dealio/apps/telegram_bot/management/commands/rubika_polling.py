from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.application_services.rubika_polling_service import RubikaPollingService
from dealio.apps.telegram_bot.rubika_services import RubikaBotClient, RubikaBotService, RubikaUpdateNormalizer


class Command(BaseCommand):
    help = "Run Rubika bot with polling."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Rubika polling limit. Reads RUBIKA_POLLING_LIMIT when omitted.")
        parser.add_argument("--sleep", type=float, default=None, help="Sleep seconds between polling calls. Reads RUBIKA_POLLING_SLEEP_SECONDS when omitted.")
        parser.add_argument("--drop-pending", action="store_true", help="Drop old Rubika updates before polling starts.")

    def handle(self, *args, **options):
        client = RubikaBotClient()
        if not client.is_configured:
            raise CommandError("RUBIKA_BOT_TOKEN and RUBIKA_BOT_BASE_URL are required.")

        if options["limit"] is None and not os.environ.get("RUBIKA_POLLING_LIMIT"):
            raise CommandError("RUBIKA_POLLING_LIMIT is required when --limit is not provided.")
        if options["sleep"] is None and not os.environ.get("RUBIKA_POLLING_SLEEP_SECONDS"):
            raise CommandError("RUBIKA_POLLING_SLEEP_SECONDS is required when --sleep is not provided.")

        limit = options["limit"] if options["limit"] is not None else int(os.environ["RUBIKA_POLLING_LIMIT"])
        sleep_seconds = options["sleep"] if options["sleep"] is not None else float(os.environ["RUBIKA_POLLING_SLEEP_SECONDS"])

        polling_service = RubikaPollingService(
            provider=RubikaBotService.MESSENGER_PROVIDER,
            client=client,
            service_factory=lambda: RubikaBotService(client=client),
            update_id_getter=RubikaUpdateNormalizer.update_log_id,
        )

        if options["drop_pending"]:
            polling_service.drop_pending(limit=limit)
            self.stdout.write(self.style.WARNING("Dropped pending Rubika updates."))

        self.stdout.write(self.style.SUCCESS("Rubika polling started. Press Ctrl+C to stop."))
        try:
            polling_service.run_forever(limit=limit, sleep_seconds=sleep_seconds)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Rubika polling stopped."))
