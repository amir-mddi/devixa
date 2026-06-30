from __future__ import annotations

import logging
import os
from enum import StrEnum

from dealio.apps.telegram_bot.dtos.channel_member_sync_dtos import ChannelMemberSyncResultDTO
from dealio.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from dealio.apps.telegram_bot.repositories.adapters.channel_member_sync_adapter import ChannelMemberSyncMessengerAdapter
from dealio.apps.telegram_bot.repositories.channel_member_sync_repository import ChannelMemberSyncRepository
from dealio.apps.telegram_bot.vo.channel_sync_vo import ChannelMemberSyncEnvVO, ChannelMemberSyncTextVO

logger = logging.getLogger("dealio")


class ChannelMemberSyncDirectionEnum(StrEnum):
    TELEGRAM_TO_BALE = "telegram-to-bale"
    BALE_TO_TELEGRAM = "bale-to-telegram"
    BOTH = "both"


class ChannelMemberSyncLogicRepository:
    """Audits known cross-provider users and invites missing members.

    Real limitation: Telegram/Bale bot APIs do not let a bot force-add arbitrary
    users to channels. This logic checks known, linked bot users and sends the
    appropriate invite link when the user is missing from the other channel.
    """

    def __init__(
        self,
        *,
        repository: ChannelMemberSyncRepository | None = None,
        adapter: ChannelMemberSyncMessengerAdapter | None = None,
    ) -> None:
        self.repository = repository or ChannelMemberSyncRepository()
        self.adapter = adapter or ChannelMemberSyncMessengerAdapter()

    @classmethod
    def validate_configuration(cls, *, direction: str) -> None:
        missing: list[str] = []
        required_by_direction = {
            ChannelMemberSyncDirectionEnum.TELEGRAM_TO_BALE.value: [
                ChannelMemberSyncEnvVO.TELEGRAM_CHANNEL_CHAT_ID,
                ChannelMemberSyncEnvVO.BALE_CHANNEL_CHAT_ID,
                ChannelMemberSyncEnvVO.BALE_INVITE_URL,
            ],
            ChannelMemberSyncDirectionEnum.BALE_TO_TELEGRAM.value: [
                ChannelMemberSyncEnvVO.BALE_CHANNEL_CHAT_ID,
                ChannelMemberSyncEnvVO.TELEGRAM_CHANNEL_CHAT_ID,
                ChannelMemberSyncEnvVO.TELEGRAM_INVITE_URL,
            ],
        }

        directions = cls._directions(direction)
        for sync_direction in directions:
            for env_name in required_by_direction[sync_direction]:
                if not (os.environ.get(env_name) or "").strip():
                    missing.append(env_name)

        if missing:
            unique_missing = sorted(set(missing))
            raise RuntimeError(f"Channel member sync env is missing: {', '.join(unique_missing)}")

    def sync(self, *, direction: str, execute: bool) -> list[ChannelMemberSyncResultDTO]:
        self.validate_configuration(direction=direction)
        results: list[ChannelMemberSyncResultDTO] = []

        for sync_direction in self._directions(direction):
            if sync_direction == ChannelMemberSyncDirectionEnum.TELEGRAM_TO_BALE.value:
                results.append(self._sync_telegram_to_bale(execute=execute))
            elif sync_direction == ChannelMemberSyncDirectionEnum.BALE_TO_TELEGRAM.value:
                results.append(self._sync_bale_to_telegram(execute=execute))

        return results

    def _sync_telegram_to_bale(self, *, execute: bool) -> ChannelMemberSyncResultDTO:
        """Known Telegram users who are missing in Bale get a Bale invite in Telegram."""
        checked = invited = already = skipped = failed = 0
        bale_channel_id = self._env(ChannelMemberSyncEnvVO.BALE_CHANNEL_CHAT_ID)
        bale_invite_url = self._env(ChannelMemberSyncEnvVO.BALE_INVITE_URL)

        for candidate in self.repository.known_candidates():
            if not candidate.telegram_chat_id or not candidate.telegram_user_id:
                skipped += 1
                continue

            checked += 1
            if candidate.bale_user_id:
                membership = self.adapter.check_member(
                    provider=MessengerProviderEnum.BALE.value,
                    channel_chat_id=bale_channel_id,
                    user_id=candidate.bale_user_id,
                )
                if membership.is_member:
                    already += 1
                    continue

            if execute:
                try:
                    self.adapter.send_invite(
                        provider=MessengerProviderEnum.TELEGRAM.value,
                        chat_id=candidate.telegram_chat_id,
                        text=ChannelMemberSyncTextVO.BALE_INVITE_MESSAGE.format(invite_url=bale_invite_url),
                    )
                    invited += 1
                except Exception as exc:
                    logger.exception("Failed to send Bale channel invite to Telegram user %s", candidate.user_id)
                    failed += 1
            else:
                invited += 1

        return ChannelMemberSyncResultDTO(
            direction=ChannelMemberSyncDirectionEnum.TELEGRAM_TO_BALE.value,
            checked_count=checked,
            invited_count=invited,
            already_member_count=already,
            skipped_count=skipped,
            failed_count=failed,
        )

    def _sync_bale_to_telegram(self, *, execute: bool) -> ChannelMemberSyncResultDTO:
        """Known Bale users who are missing in Telegram get a Telegram invite in Bale."""
        checked = invited = already = skipped = failed = 0
        telegram_channel_id = self._env(ChannelMemberSyncEnvVO.TELEGRAM_CHANNEL_CHAT_ID)
        telegram_invite_url = self._env(ChannelMemberSyncEnvVO.TELEGRAM_INVITE_URL)

        for candidate in self.repository.known_candidates():
            if not candidate.bale_chat_id or not candidate.bale_user_id:
                skipped += 1
                continue

            checked += 1
            if candidate.telegram_user_id:
                membership = self.adapter.check_member(
                    provider=MessengerProviderEnum.TELEGRAM.value,
                    channel_chat_id=telegram_channel_id,
                    user_id=candidate.telegram_user_id,
                )
                if membership.is_member:
                    already += 1
                    continue

            if execute:
                try:
                    self.adapter.send_invite(
                        provider=MessengerProviderEnum.BALE.value,
                        chat_id=candidate.bale_chat_id,
                        text=ChannelMemberSyncTextVO.TELEGRAM_INVITE_MESSAGE.format(invite_url=telegram_invite_url),
                    )
                    invited += 1
                except Exception as exc:
                    logger.exception("Failed to send Telegram channel invite to Bale user %s", candidate.user_id)
                    failed += 1
            else:
                invited += 1

        return ChannelMemberSyncResultDTO(
            direction=ChannelMemberSyncDirectionEnum.BALE_TO_TELEGRAM.value,
            checked_count=checked,
            invited_count=invited,
            already_member_count=already,
            skipped_count=skipped,
            failed_count=failed,
        )

    @classmethod
    def _directions(cls, direction: str) -> list[str]:
        if direction == ChannelMemberSyncDirectionEnum.BOTH.value:
            return [
                ChannelMemberSyncDirectionEnum.TELEGRAM_TO_BALE.value,
                ChannelMemberSyncDirectionEnum.BALE_TO_TELEGRAM.value,
            ]
        return [direction]

    @staticmethod
    def _env(name: str) -> str:
        value = (os.environ.get(name) or "").strip()
        if not value:
            raise RuntimeError(f"{name} is required.")
        return value
