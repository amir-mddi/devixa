from django.test import TestCase
from rest_framework.exceptions import NotFound, ValidationError

from dealio.apps.telegram_bot.models import BotSupportTicket
from dealio.apps.telegram_bot.repositories.logic.bot_support_logic import (
    BotSupportLogicRepository,
)
from dealio.tests.factories import UserFactory


class WebSupportLogicTests(TestCase):
    def setUp(self):
        self.logic = BotSupportLogicRepository()
        self.user = UserFactory.create()

    def test_create_account_ticket_does_not_require_messenger_profile(self):
        ticket = self.logic.create_account_ticket(
            user=self.user,
            subject="Website support",
            message="I need assistance.",
        )

        self.assertEqual(ticket.provider, "web")
        self.assertIsNone(ticket.profile_id)
        self.assertEqual(ticket.user_id, self.user.id)
        self.assertEqual(ticket.messages.count(), 1)

    def test_account_reply_is_limited_to_ticket_owner(self):
        ticket = self.logic.create_account_ticket(
            user=self.user,
            subject="Private",
            message="First message",
        )

        with self.assertRaises(NotFound):
            self.logic.add_account_user_message(
                ticket_id=ticket.id,
                user=UserFactory.create(),
                message="Not allowed",
            )

    def test_closed_account_ticket_rejects_new_user_messages(self):
        ticket = self.logic.create_account_ticket(
            user=self.user,
            subject="Closed",
            message="First message",
        )
        ticket.status = BotSupportTicket.STATUS_CLOSED
        ticket.save(update_fields=["status", "updated_at"])

        with self.assertRaises(ValidationError):
            self.logic.add_account_user_message(
                ticket_id=ticket.id,
                user=self.user,
                message="Late reply",
            )
