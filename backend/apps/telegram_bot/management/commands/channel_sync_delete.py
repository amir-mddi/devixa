from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from backend.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from backend.apps.telegram_bot.repositories.logic.channel_sync_logic import ChannelSyncLogicRepository


class Command(BaseCommand):
    help = (
        "Delete mirrored channel-sync messages. Use source-* to delete targets for an original message, "
        "target-* to delete the related original for a mirrored message, or direct-* to delete one exact message."
    )

    PROVIDERS = [MessengerProviderEnum.TELEGRAM.value, MessengerProviderEnum.BALE.value, MessengerProviderEnum.RUBIKA.value]

    def add_arguments(self, parser):
        source = parser.add_argument_group("source mapping delete")
        source.add_argument("--source-provider", choices=self.PROVIDERS, help="Provider of the original/source message.")
        source.add_argument("--source-chat-id", help="Source chat/channel ID.")
        source.add_argument("--source-message-id", help="Source message ID.")

        target = parser.add_argument_group("target mapping delete")
        target.add_argument("--target-provider", choices=self.PROVIDERS, help="Provider of the mirrored/target message.")
        target.add_argument("--target-chat-id", help="Target chat/channel ID.")
        target.add_argument("--target-message-id", help="Target message ID.")

        direct = parser.add_argument_group("direct delete")
        direct.add_argument("--direct-provider", choices=self.PROVIDERS, help="Provider of one exact message to delete.")
        direct.add_argument("--direct-chat-id", help="Chat/channel ID of one exact message to delete.")
        direct.add_argument("--direct-message-id", help="Message ID of one exact message to delete.")

        parser.add_argument("--show-recent", action="store_true", help="Show recent channel-sync mappings and exit.")
        parser.add_argument("--limit", type=int, default=20, help="Recent mapping limit for --show-recent or no-match hints.")

    def handle(self, *args, **options):
        if not ChannelSyncLogicRepository.is_enabled():
            raise CommandError("CHANNEL_SYNC_ENABLED must be true to delete synced channel messages.")

        if options["show_recent"]:
            self._print_recent(limit=options["limit"])
            return

        if self._has_source_options(options):
            deleted_count = ChannelSyncLogicRepository.delete_targets_for_source(
                source_provider=options["source_provider"],
                source_chat_id=options["source_chat_id"],
                source_message_id=options["source_message_id"],
            )
            if deleted_count == 0:
                self._print_no_mapping_hint("source", options)
                return
            self.stdout.write(self.style.SUCCESS(f"Delete requested for {deleted_count} synced target message(s)."))
            return

        if self._has_target_options(options):
            deleted_count = ChannelSyncLogicRepository.delete_related_for_target(
                target_provider=options["target_provider"],
                target_chat_id=options["target_chat_id"],
                target_message_id=options["target_message_id"],
            )
            if deleted_count == 0:
                self._print_no_mapping_hint("target", options)
                return
            self.stdout.write(self.style.SUCCESS(f"Delete requested for {deleted_count} related source message(s)."))
            return

        if self._has_direct_options(options):
            ChannelSyncLogicRepository.delete_exact_message(
                provider=options["direct_provider"],
                chat_id=options["direct_chat_id"],
                message_id=options["direct_message_id"],
            )
            self.stdout.write(self.style.SUCCESS("Direct delete requested."))
            return

        raise CommandError(
            "Provide source-*, target-*, direct-*, or --show-recent. "
            "Run with --show-recent to see real source/target message IDs from the mapping table."
        )

    @staticmethod
    def _has_source_options(options: dict) -> bool:
        return bool(options.get("source_provider") and options.get("source_chat_id") and options.get("source_message_id"))

    @staticmethod
    def _has_target_options(options: dict) -> bool:
        return bool(options.get("target_provider") and options.get("target_chat_id") and options.get("target_message_id"))

    @staticmethod
    def _has_direct_options(options: dict) -> bool:
        return bool(options.get("direct_provider") and options.get("direct_chat_id") and options.get("direct_message_id"))

    def _print_no_mapping_hint(self, mode: str, options: dict) -> None:
        self.stdout.write(self.style.WARNING("No synced mapping was found for this message."))
        self.stdout.write(
            "This usually means the message was not synced after channel-sync was enabled, "
            "or the chat/message ID is not the exact value stored in ChannelSyncMessage."
        )
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Recent mappings:"))
        self._print_recent(limit=options["limit"])

    def _print_recent(self, *, limit: int) -> None:
        mappings = list(ChannelSyncLogicRepository.recent_mappings(limit=limit))
        if not mappings:
            self.stdout.write(self.style.WARNING("No ChannelSyncMessage rows exist yet."))
            self.stdout.write("Send a new Telegram/Bale message while channel_sync_polling is running, then try again.")
            return

        for mapping in mappings:
            self.stdout.write(
                "source=(%s, chat=%s, msg=%s) -> target=(%s, chat=%s, msg=%s) error=%s"
                % (
                    mapping.source_provider,
                    mapping.source_chat_id,
                    mapping.source_message_id,
                    mapping.target_provider,
                    mapping.target_chat_id,
                    mapping.target_message_id or "<empty>",
                    mapping.last_error or "-",
                )
            )
