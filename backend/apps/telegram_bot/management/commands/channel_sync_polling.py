from __future__ import annotations

import asyncio
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from backend.apps.common.async_utils import call_maybe_async
from backend.apps.telegram_bot.bale_services import BaleBotClient
from backend.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from backend.apps.telegram_bot.repositories.logic.channel_sync_logic import ChannelSyncLogicRepository


class Command(BaseCommand):
    help = "Run dedicated async channel sync polling for Telegram and/or Bale channels."

    TELEGRAM_CHANNEL_UPDATES = ["channel_post", "edited_channel_post"]
    BALE_CHANNEL_UPDATES = [
        "message",
        "edited_message",
        "deleted_message",
        "channel_post",
        "edited_channel_post",
        "deleted_channel_post",
        "callback_query",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider",
            choices=[
                "all",
                MessengerProviderEnum.TELEGRAM.value,
                MessengerProviderEnum.BALE.value,
            ],
            default="all",
            help="Which source provider to poll for channel sync.",
        )
        parser.add_argument("--telegram-timeout", type=int, default=5)
        parser.add_argument("--bale-timeout", type=int, default=5)
        parser.add_argument("--bale-limit", type=int, default=50)
        parser.add_argument("--sleep", type=float, default=1.0)
        parser.add_argument("--drop-pending", action="store_true")

    def handle(self, *args, **options):
        try:
            asyncio.run(self._run(options))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Channel sync polling stopped."))

    async def _run(self, options: dict[str, Any]) -> None:
        logic = ChannelSyncLogicRepository()
        enabled = await call_maybe_async(logic.is_enabled)
        if not enabled:
            raise CommandError(
                "CHANNEL_SYNC_ENABLED must be true to run channel_sync_polling."
            )

        provider = options["provider"]
        poll_telegram = provider in {
            "all",
            MessengerProviderEnum.TELEGRAM.value,
        }
        poll_bale = provider in {"all", MessengerProviderEnum.BALE.value}

        telegram_client = TelegramBotClient() if poll_telegram else None
        bale_client = BaleBotClient() if poll_bale else None

        if telegram_client and not await call_maybe_async(
            lambda: telegram_client.is_configured
        ):
            raise CommandError(
                "TELEGRAM_BOT_TOKEN is required for Telegram channel sync polling."
            )
        if bale_client and not await call_maybe_async(
            lambda: bale_client.is_configured
        ):
            raise CommandError(
                "BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required for Bale channel sync polling."
            )

        if poll_telegram:
            await call_maybe_async(
                logic.validate_configuration,
                source_provider=MessengerProviderEnum.TELEGRAM.value,
            )
        if poll_bale:
            await call_maybe_async(
                logic.validate_configuration,
                source_provider=MessengerProviderEnum.BALE.value,
            )

        if options["drop_pending"]:
            await self._drop_pending(
                telegram_client=telegram_client,
                bale_client=bale_client,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Channel sync polling started. Press Ctrl+C to stop."
            )
        )

        telegram_offset: int | None = None
        bale_offset: int | None = None
        while True:
            if telegram_client:
                telegram_offset = await self._poll_telegram(
                    client=telegram_client,
                    logic=logic,
                    offset=telegram_offset,
                    timeout=options["telegram_timeout"],
                )

            if bale_client:
                bale_offset = await self._poll_bale(
                    client=bale_client,
                    logic=logic,
                    offset=bale_offset,
                    timeout=options["bale_timeout"],
                    limit=options["bale_limit"],
                )

            await asyncio.sleep(options["sleep"])

    async def _drop_pending(
        self,
        *,
        telegram_client: Any | None,
        bale_client: Any | None,
    ) -> None:
        for client in (telegram_client, bale_client):
            if not client:
                continue
            delete_webhook = getattr(
                client,
                "adelete_webhook",
                getattr(client, "delete_webhook", None),
            )
            if delete_webhook:
                await call_maybe_async(
                    delete_webhook,
                    drop_pending_updates=True,
                )

    async def _poll_telegram(
        self,
        *,
        client: TelegramBotClient,
        logic: ChannelSyncLogicRepository,
        offset: int | None,
        timeout: int,
    ) -> int | None:
        updates = await client.aget_updates(
            offset=offset,
            timeout=timeout,
            allowed_updates=self.TELEGRAM_CHANNEL_UPDATES,
        )
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                offset = int(update_id) + 1
            await call_maybe_async(logic.handle_telegram_update, update)
        return offset

    async def _poll_bale(
        self,
        *,
        client: BaleBotClient,
        logic: ChannelSyncLogicRepository,
        offset: int | None,
        timeout: int,
        limit: int,
    ) -> int | None:
        get_updates = getattr(client, "aget_updates", client.get_updates)
        updates = await call_maybe_async(
            get_updates,
            offset=offset,
            timeout=timeout,
            limit=limit,
            allowed_updates=self.BALE_CHANNEL_UPDATES,
        )
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                offset = int(update_id) + 1
            await call_maybe_async(logic.handle_bale_update, update)
        return offset
