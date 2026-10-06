from __future__ import annotations

from backend.apps.referrals.models import (
    ReferralCode,
    ReferralInvite,
    TelegramChannelReferralLink,
    TelegramChannelReferralMember,
)


class ReferralRepository:
    def get_code_record(self, user):
        return ReferralCode.objects.filter(user=user, is_active=True, is_deleted=False).first()

    def find_code(self, code: str):
        return (
            ReferralCode.objects.select_related("user")
            .filter(code=code, is_active=True, is_deleted=False, user__is_active=True, user__is_deleted=False)
            .first()
        )

    def create_code(self, *, user, code: str):
        return ReferralCode.objects.create(user=user, code=code, user_created_object=user)

    def code_exists(self, code: str) -> bool:
        return ReferralCode.objects.filter(code=code).exists()

    def invite_exists_for_user(self, invitee) -> bool:
        return ReferralInvite.objects.filter(invitee=invitee, is_deleted=False).exists()

    def create_invite(self, *, inviter, invitee, referral_code):
        return ReferralInvite.objects.create(
            inviter=inviter,
            invitee=invitee,
            referral_code=referral_code,
            user_created_object=invitee,
        )

    def count_invites(self, user) -> int:
        return ReferralInvite.objects.filter(inviter=user, is_active=True, is_deleted=False).count()

    def recent_invites(self, user, *, limit: int):
        return list(
            ReferralInvite.objects.select_related("invitee")
            .filter(inviter=user, is_active=True, is_deleted=False)
            .order_by("-registered_at")[:limit]
        )

    def get_channel_link(self, *, owner, channel_username: str):
        return (
            TelegramChannelReferralLink.objects.filter(
                owner=owner,
                channel_username=channel_username,
                is_active=True,
                is_deleted=False,
                is_revoked=False,
            )
            .order_by("-created_at")
            .first()
        )

    def create_channel_link(
        self,
        *,
        owner,
        channel_username: str,
        channel_chat_id: str,
        invite_link: str,
        telegram_name: str,
    ):
        return TelegramChannelReferralLink.objects.create(
            owner=owner,
            channel_username=channel_username,
            channel_chat_id=channel_chat_id,
            invite_link=invite_link,
            telegram_name=telegram_name,
            user_created_object=owner,
        )

    def find_channel_link_by_invite(self, *, channel_username: str, invite_link: str):
        if not invite_link:
            return None
        return (
            TelegramChannelReferralLink.objects.select_related("owner")
            .filter(
                channel_username=channel_username,
                invite_link=invite_link,
                is_active=True,
                is_deleted=False,
                is_revoked=False,
            )
            .first()
        )

    def get_channel_member_for_update(self, *, channel_username: str, telegram_user_id: int):
        return (
            TelegramChannelReferralMember.objects.select_for_update()
            .select_related("referral_link", "referral_link__owner")
            .filter(
                channel_username=channel_username,
                telegram_user_id=telegram_user_id,
                is_deleted=False,
            )
            .first()
        )

    def create_channel_member(
        self,
        *,
        channel_username: str,
        channel_chat_id: str,
        telegram_user_id: int,
        username: str,
        first_name: str,
        last_name: str,
        referral_link,
        joined_at,
        is_current_member: bool,
        left_at=None,
    ):
        return TelegramChannelReferralMember.objects.create(
            channel_username=channel_username,
            channel_chat_id=channel_chat_id,
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            referral_link=referral_link,
            first_joined_at=joined_at if is_current_member else None,
            last_joined_at=joined_at if is_current_member else None,
            left_at=left_at,
            is_current_member=is_current_member,
        )

    @staticmethod
    def mark_channel_member_joined(
        member,
        *,
        username: str,
        first_name: str,
        last_name: str,
        channel_chat_id: str,
        joined_at,
    ):
        member.username = username
        member.first_name = first_name
        member.last_name = last_name
        member.channel_chat_id = channel_chat_id or member.channel_chat_id
        member.last_joined_at = joined_at
        member.left_at = None
        member.is_current_member = True
        member.save(
            update_fields=[
                "username",
                "first_name",
                "last_name",
                "channel_chat_id",
                "last_joined_at",
                "left_at",
                "is_current_member",
                "updated_at",
            ]
        )
        return member

    @staticmethod
    def mark_channel_member_left(member, *, left_at, channel_chat_id: str = ""):
        member.channel_chat_id = channel_chat_id or member.channel_chat_id
        member.left_at = left_at
        member.is_current_member = False
        member.save(
            update_fields=[
                "channel_chat_id",
                "left_at",
                "is_current_member",
                "updated_at",
            ]
        )
        return member

    def count_channel_referrals(self, *, owner, channel_username: str) -> int:
        return TelegramChannelReferralMember.objects.filter(
            referral_link__owner=owner,
            referral_link__channel_username=channel_username,
            referral_link__is_deleted=False,
            referral_link__is_revoked=False,
            is_deleted=False,
        ).count()

    def count_current_channel_referrals(self, *, owner, channel_username: str) -> int:
        return TelegramChannelReferralMember.objects.filter(
            referral_link__owner=owner,
            referral_link__channel_username=channel_username,
            is_current_member=True,
            is_deleted=False,
        ).count()

    def list_channel_referral_members(self, *, owner, channel_username: str, limit: int):
        return list(
            TelegramChannelReferralMember.objects.select_related("referral_link")
            .filter(
                referral_link__owner=owner,
                referral_link__channel_username=channel_username,
                is_deleted=False,
            )
            .order_by("-first_joined_at", "-created_at")[:limit]
        )
