from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.repositories.logic.channel_member_sync_logic import (
    ChannelMemberSyncDirectionEnum,
    ChannelMemberSyncLogicRepository,
)


class Command(BaseCommand):
    help = "Audit known Telegram/Bale bot users and send channel invite links to users missing from the other channel."

    def add_arguments(self, parser):
        parser.add_argument(
            "--direction",
            choices=[
                ChannelMemberSyncDirectionEnum.TELEGRAM_TO_BALE.value,
                ChannelMemberSyncDirectionEnum.BALE_TO_TELEGRAM.value,
                ChannelMemberSyncDirectionEnum.BOTH.value,
            ],
            default=ChannelMemberSyncDirectionEnum.BOTH.value,
            help="Direction to audit/invite.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually send invite messages. Without this flag the command is dry-run only.",
        )

    def handle(self, *args, **options):
        direction = options["direction"]
        execute = bool(options["execute"])

        logic = ChannelMemberSyncLogicRepository()
        try:
            results = logic.sync(direction=direction, execute=execute)
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        mode = "EXECUTE" if execute else "DRY-RUN"
        self.stdout.write(self.style.WARNING(f"Channel member sync mode: {mode}"))

        for result in results:
            self.stdout.write(
                self.style.SUCCESS(
                    "direction={direction} checked={checked} already_member={already} "
                    "would_invite_or_invited={invited} skipped={skipped} failed={failed}".format(
                        direction=result.direction,
                        checked=result.checked_count,
                        already=result.already_member_count,
                        invited=result.invited_count,
                        skipped=result.skipped_count,
                        failed=result.failed_count,
                    )
                )
            )

        if not execute:
            self.stdout.write(self.style.WARNING("No messages were sent. Re-run with --execute to send invite links."))
