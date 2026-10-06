from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils.timezone import now

from backend.apps.accounts.models import Role
from backend.apps.referrals.dtos import TelegramChannelMemberUpdateDTO
from backend.apps.referrals.logic import ChannelReferralLogic
from backend.apps.referrals.models import TelegramChannelReferralMember
from backend.apps.referrals.repositories import ReferralRepository


class FakeInviteAdapter:
    def __init__(self):
        self.calls = 0

    def create_invite_link(self, *, channel: str, invite_name: str) -> str:
        self.calls += 1
        return f"https://t.me/+referral{self.calls}"


@override_settings(
    TELEGRAM_REFERRAL_CHANNEL_USERNAME="@DevixaTEch",
    TELEGRAM_REFERRAL_CHANNEL_CHAT_ID="-1001234567890",
)
class ChannelReferralLogicTests(TestCase):
    def setUp(self):
        role = Role.objects.create(name="User", symbol="user")
        user_model = get_user_model()
        self.owner_a = user_model.objects.create_user(
            username="owner_a", email="a@example.com", password="x", role=role
        )
        self.owner_b = user_model.objects.create_user(
            username="owner_b", email="b@example.com", password="x", role=role
        )
        self.adapter = FakeInviteAdapter()
        self.logic = ChannelReferralLogic(invite_adapter=self.adapter)
        self.repo = ReferralRepository()

    def dto(self, *, user_id: int, invite_link: str, old_status="left", new_status="member"):
        return TelegramChannelMemberUpdateDTO(
            channel_username="@DevixaTEch",
            channel_chat_id="-1001234567890",
            telegram_user_id=user_id,
            username=f"tg{user_id}",
            first_name="Test",
            last_name="User",
            invite_link=invite_link,
            old_status=old_status,
            new_status=new_status,
            occurred_at=now(),
        )

    def test_link_generation_is_idempotent(self):
        first = self.logic.get_or_create_link(self.owner_a)
        second = self.logic.get_or_create_link(self.owner_a)
        self.assertEqual(first.invite_link, second.invite_link)
        self.assertEqual(self.adapter.calls, 1)

    def test_leave_and_rejoin_does_not_increment_again(self):
        link = self.logic.get_or_create_link(self.owner_a)
        self.assertTrue(self.logic.process_member_update(self.dto(user_id=10, invite_link=link.invite_link)))
        self.logic.process_member_update(
            self.dto(user_id=10, invite_link="", old_status="member", new_status="left")
        )
        self.assertFalse(self.logic.process_member_update(self.dto(user_id=10, invite_link=link.invite_link)))
        self.assertEqual(
            self.repo.count_channel_referrals(
                owner=self.owner_a, channel_username="@devixatech"
            ),
            1,
        )

    def test_rejoin_through_another_users_link_keeps_first_attribution(self):
        link_a = self.logic.get_or_create_link(self.owner_a)
        link_b = self.logic.get_or_create_link(self.owner_b)
        self.logic.process_member_update(self.dto(user_id=20, invite_link=link_a.invite_link))
        self.logic.process_member_update(
            self.dto(user_id=20, invite_link="", old_status="member", new_status="left")
        )
        self.logic.process_member_update(self.dto(user_id=20, invite_link=link_b.invite_link))
        member = TelegramChannelReferralMember.objects.get(telegram_user_id=20)
        self.assertEqual(member.referral_link.owner_id, self.owner_a.id)
        self.assertEqual(
            self.repo.count_channel_referrals(owner=self.owner_b, channel_username="@devixatech"),
            0,
        )

    def test_first_direct_join_is_never_later_attributed(self):
        self.logic.process_member_update(self.dto(user_id=30, invite_link=""))
        self.logic.process_member_update(
            self.dto(user_id=30, invite_link="", old_status="member", new_status="left")
        )
        link = self.logic.get_or_create_link(self.owner_a)
        self.logic.process_member_update(self.dto(user_id=30, invite_link=link.invite_link))
        member = TelegramChannelReferralMember.objects.get(telegram_user_id=30)
        self.assertIsNone(member.referral_link_id)
