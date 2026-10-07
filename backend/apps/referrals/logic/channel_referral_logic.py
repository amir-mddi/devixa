from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from backend.apps.referrals.adapters import TelegramChannelInviteAdapter
from backend.apps.common.utils.network_security import force_https_scheme
from backend.apps.referrals.dtos import (
    ChannelReferralAdminSummaryDTO,
    TelegramChannelMemberUpdateDTO,
)
from backend.apps.referrals.entities import (
    TelegramChannelReferralLinkEntity,
    TelegramChannelReferralMemberEntity,
)
from backend.apps.referrals.enums import TelegramMemberStatusEnum
from backend.apps.referrals.repositories import ReferralRepository
from backend.apps.referrals.value_objects import (
    ReferralLimitVO,
    ReferralMessageVO,
    TelegramChannelReferralVO,
)


class ChannelReferralLogic:
    def __init__(
        self,
        repository: ReferralRepository | None = None,
        invite_adapter: TelegramChannelInviteAdapter | None = None,
    ):
        self.repository = repository or ReferralRepository()
        self.invite_adapter = invite_adapter or TelegramChannelInviteAdapter()

    @staticmethod
    def configured_channel() -> str:
        value = str(
            getattr(
                settings,
                "TELEGRAM_REFERRAL_CHANNEL_USERNAME",
                TelegramChannelReferralVO.DEFAULT_CHANNEL_USERNAME.value,
            )
            or ""
        ).strip()
        if value and not value.startswith("@"):
            value = f"@{value}"
        return value

    @staticmethod
    def configured_chat_id() -> str:
        return str(getattr(settings, "TELEGRAM_REFERRAL_CHANNEL_CHAT_ID", "") or "").strip()

    @classmethod
    def normalized_channel(cls, value: str | None = None) -> str:
        channel = str(value if value is not None else cls.configured_channel()).strip()
        if channel and not channel.startswith("@") and not channel.lstrip("-").isdigit():
            channel = f"@{channel}"
        return channel.lower()

    @classmethod
    def display_channel(cls) -> str:
        return cls.configured_channel()

    def get_link(self, user) -> TelegramChannelReferralLinkEntity | None:
        channel = self.normalized_channel()
        if not channel:
            return None
        record = self.repository.get_channel_link(owner=user, channel_username=channel)
        if record is None:
            return None
        return TelegramChannelReferralLinkEntity(
            channel_username=self.display_channel() or record.channel_username,
            invite_link=force_https_scheme(record.invite_link),
        )

    def get_or_create_link(self, user) -> TelegramChannelReferralLinkEntity:
        channel_display = self.display_channel()
        channel = self.normalized_channel(channel_display)
        if not channel:
            raise ValidationError(ReferralMessageVO.CHANNEL_NOT_CONFIGURED.value)

        existing = self.repository.get_channel_link(owner=user, channel_username=channel)
        if existing:
            return TelegramChannelReferralLinkEntity(
                channel_username=channel_display or existing.channel_username,
                invite_link=force_https_scheme(existing.invite_link),
            )

        invite_name = (
            f"{TelegramChannelReferralVO.INVITE_NAME_PREFIX.value}{str(user.id).replace('-', '')[:20]}"
        )[:32]
        try:
            invite_link = self.invite_adapter.create_invite_link(
                channel=channel_display or channel,
                invite_name=invite_name,
            )
        except RuntimeError as exc:
            raise ValidationError(ReferralMessageVO.CHANNEL_INVITE_CREATE_FAILED.value) from exc

        try:
            record = self.repository.create_channel_link(
                owner=user,
                channel_username=channel,
                channel_chat_id=self.configured_chat_id(),
                invite_link=invite_link,
                telegram_name=invite_name,
            )
        except IntegrityError:
            record = self.repository.get_channel_link(owner=user, channel_username=channel)
            if record is None:
                raise

        return TelegramChannelReferralLinkEntity(
            channel_username=channel_display or record.channel_username,
            invite_link=force_https_scheme(record.invite_link),
        )

    def matches_target_channel(self, *, chat_username: str, chat_id: str) -> bool:
        configured_chat_id = self.configured_chat_id()
        if configured_chat_id and chat_id and configured_chat_id == str(chat_id):
            return True
        configured_username = self.normalized_channel()
        update_username = self.normalized_channel(chat_username)
        return bool(configured_username and update_username == configured_username)

    @staticmethod
    def _status_is_member(status: str) -> bool:
        return str(status or "").strip().lower() in TelegramMemberStatusEnum.active_values()

    @transaction.atomic
    def process_member_update(self, dto: TelegramChannelMemberUpdateDTO) -> bool:
        """Record membership transitions and return True only for a new attribution."""
        if dto.is_bot or not dto.telegram_user_id:
            return False
        if not self.matches_target_channel(
            chat_username=dto.channel_username,
            chat_id=dto.channel_chat_id,
        ):
            return False

        channel = self.normalized_channel()
        was_member = self._status_is_member(dto.old_status)
        is_member = self._status_is_member(dto.new_status)
        if was_member == is_member:
            return False

        member = self.repository.get_channel_member_for_update(
            channel_username=channel,
            telegram_user_id=dto.telegram_user_id,
        )

        if is_member:
            if member is not None:
                # First attribution wins forever. Rejoining only changes presence.
                self.repository.mark_channel_member_joined(
                    member,
                    username=dto.username,
                    first_name=dto.first_name,
                    last_name=dto.last_name,
                    channel_chat_id=dto.channel_chat_id,
                    joined_at=dto.occurred_at,
                )
                return False

            referral_link = self.repository.find_channel_link_by_invite(
                channel_username=channel,
                invite_link=dto.invite_link,
            )
            try:
                with transaction.atomic():
                    self.repository.create_channel_member(
                        channel_username=channel,
                        channel_chat_id=dto.channel_chat_id,
                        telegram_user_id=dto.telegram_user_id,
                        username=dto.username,
                        first_name=dto.first_name,
                        last_name=dto.last_name,
                        referral_link=referral_link,
                        joined_at=dto.occurred_at,
                        is_current_member=True,
                    )
                return referral_link is not None
            except IntegrityError:
                member = self.repository.get_channel_member_for_update(
                    channel_username=channel,
                    telegram_user_id=dto.telegram_user_id,
                )
                if member is not None:
                    self.repository.mark_channel_member_joined(
                        member,
                        username=dto.username,
                        first_name=dto.first_name,
                        last_name=dto.last_name,
                        channel_chat_id=dto.channel_chat_id,
                        joined_at=dto.occurred_at,
                    )
                return False

        # A departure is also persisted when the member was not known yet. That
        # prevents a user who existed before referral tracking from being counted
        # as "new" when they later rejoin using someone's link.
        if member is None:
            try:
                with transaction.atomic():
                    self.repository.create_channel_member(
                        channel_username=channel,
                        channel_chat_id=dto.channel_chat_id,
                        telegram_user_id=dto.telegram_user_id,
                        username=dto.username,
                        first_name=dto.first_name,
                        last_name=dto.last_name,
                        referral_link=None,
                        joined_at=dto.occurred_at,
                        is_current_member=False,
                        left_at=dto.occurred_at,
                    )
            except IntegrityError:
                member = self.repository.get_channel_member_for_update(
                    channel_username=channel,
                    telegram_user_id=dto.telegram_user_id,
                )
                if member is not None:
                    self.repository.mark_channel_member_left(
                        member,
                        left_at=dto.occurred_at,
                        channel_chat_id=dto.channel_chat_id,
                    )
        else:
            self.repository.mark_channel_member_left(
                member,
                left_at=dto.occurred_at,
                channel_chat_id=dto.channel_chat_id,
            )
        return False

    @staticmethod
    def dto_from_chat_member_update(update: dict) -> TelegramChannelMemberUpdateDTO | None:
        chat = update.get("chat") or {}
        old_member = update.get("old_chat_member") or {}
        new_member = update.get("new_chat_member") or {}
        telegram_user = new_member.get("user") or old_member.get("user") or {}
        telegram_user_id = telegram_user.get("id")
        if not telegram_user_id:
            return None

        invite = update.get("invite_link") or {}
        occurred_timestamp = update.get("date")
        occurred_at = (
            datetime.fromtimestamp(int(occurred_timestamp), tz=now().tzinfo)
            if occurred_timestamp
            else now()
        )
        chat_username = str(chat.get("username") or "").strip()
        if chat_username and not chat_username.startswith("@"):
            chat_username = f"@{chat_username}"

        return TelegramChannelMemberUpdateDTO(
            channel_username=chat_username,
            channel_chat_id=str(chat.get("id") or ""),
            telegram_user_id=int(telegram_user_id),
            username=str(telegram_user.get("username") or "").strip(),
            first_name=str(telegram_user.get("first_name") or "").strip(),
            last_name=str(telegram_user.get("last_name") or "").strip(),
            invite_link=str(invite.get("invite_link") or "").strip(),
            old_status=str(old_member.get("status") or "").strip(),
            new_status=str(new_member.get("status") or "").strip(),
            occurred_at=occurred_at,
            is_bot=bool(telegram_user.get("is_bot")),
        )

    def process_chat_member_update(self, update: dict) -> bool:
        dto = self.dto_from_chat_member_update(update)
        return self.process_member_update(dto) if dto else False

    def admin_summary(self, user) -> ChannelReferralAdminSummaryDTO:
        channel = self.normalized_channel()
        link = self.repository.get_channel_link(owner=user, channel_username=channel) if channel else None
        members = self.repository.list_channel_referral_members(
            owner=user,
            channel_username=channel,
            limit=ReferralLimitVO.ADMIN_MEMBER_LIMIT.value,
        ) if channel else []
        return ChannelReferralAdminSummaryDTO(
            channel_username=self.display_channel(),
            invite_link=force_https_scheme(link.invite_link) if link else "",
            invited_count=self.repository.count_channel_referrals(
                owner=user,
                channel_username=channel,
            ) if channel else 0,
            current_member_count=self.repository.count_current_channel_referrals(
                owner=user,
                channel_username=channel,
            ) if channel else 0,
            members=tuple(
                TelegramChannelReferralMemberEntity(
                    telegram_user_id=item.telegram_user_id,
                    username=item.username,
                    full_name=" ".join(part for part in (item.first_name, item.last_name) if part).strip(),
                    first_joined_at=item.first_joined_at,
                    last_joined_at=item.last_joined_at,
                    left_at=item.left_at,
                    is_current_member=item.is_current_member,
                )
                for item in members
            ),
        )
