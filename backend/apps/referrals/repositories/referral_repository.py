from __future__ import annotations

from backend.apps.referrals.models import ReferralCode, ReferralInvite


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
