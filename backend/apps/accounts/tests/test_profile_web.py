from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from backend.apps.billing.enums import PaymentReceiptSourceEnum, PaymentStatusEnum
from backend.apps.billing.models import PaymentReceipt
from backend.apps.telegram_bot.models import BotSupportMessage, BotSupportTicket
from backend.tests.factories import (
    CourseFactory,
    EnrollmentFactory,
    OrderFactory,
    PaymentFactory,
    ProjectConfigFactory,
    TelegramProfileFactory,
    UserFactory,
)


class AccountProfileWebTests(TestCase):
    def setUp(self):
        ProjectConfigFactory.create()
        self.user = UserFactory.create(
            phone_number="09121234567",
            email_verified=True,
            phone_number_verified=True,
        )
        self.rate_limit_patcher = patch(
            "backend.apps.common.helpers.decorators.rate_limit.is_rate_limit_allowed",
            return_value=True,
        )
        self.rate_limit_patcher.start()
        self.addCleanup(self.rate_limit_patcher.stop)

    def test_profile_panel_requires_login(self):
        response = self.client.get(reverse("accounts_web:profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts_web:login"), response.url)

    def test_profile_panel_aggregates_user_courses_billing_and_support(self):
        course = CourseFactory.create()
        EnrollmentFactory.create(user=self.user, course=course)
        order = OrderFactory.create(user=self.user)
        PaymentFactory.create(user=self.user, order=order)
        ticket = BotSupportTicket.objects.create(
            provider="web",
            user=self.user,
            subject="Need help",
        )
        BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_USER,
            sender_user=self.user,
            message="Please help",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts_web:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, course.title)
        self.assertContains(response, order.order_number)
        self.assertContains(response, "Need help")

    def test_contact_update_resets_only_changed_contact_verification(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts_web:profile_contact"),
            {
                "email": self.user.email,
                "phone_number": "09121234568",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("#contact"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertFalse(self.user.phone_number_verified)

    def test_user_can_create_web_support_ticket(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts_web:profile_ticket_create"),
            {"subject": "Billing question", "message": "Where is my receipt?"},
        )

        self.assertEqual(response.status_code, 302)
        ticket = BotSupportTicket.objects.get(user=self.user, provider="web")
        self.assertEqual(ticket.subject, "Billing question")
        self.assertEqual(ticket.messages.get().message, "Where is my receipt?")

    def test_user_cannot_reply_to_another_users_ticket(self):
        other_user = UserFactory.create()
        ticket = BotSupportTicket.objects.create(
            provider="web",
            user=other_user,
            subject="Private ticket",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "accounts_web:profile_ticket_reply",
                kwargs={"ticket_id": ticket.id},
            ),
            {"message": "Unauthorized reply"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ticket.messages.exists())

    def test_user_can_disconnect_owned_messenger_profile(self):
        profile = TelegramProfileFactory.create(
            user=self.user,
            is_verified=True,
            is_active=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "accounts_web:profile_messenger_disconnect",
                kwargs={"profile_id": profile.id},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("#overview"))
        profile.refresh_from_db()
        self.assertIsNone(profile.user_id)
        self.assertFalse(profile.is_verified)

    def test_user_cannot_disconnect_another_users_messenger_profile(self):
        profile = TelegramProfileFactory.create(
            user=UserFactory.create(),
            is_verified=True,
            is_active=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "accounts_web:profile_messenger_disconnect",
                kwargs={"profile_id": profile.id},
            )
        )

        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertIsNotNone(profile.user_id)
        self.assertTrue(profile.is_verified)

    def test_user_can_submit_receipt_for_owned_card_to_card_payment(self):
        order = OrderFactory.create(user=self.user, total_amount="250000")
        payment = PaymentFactory.create(
            user=self.user,
            order=order,
            amount="250000",
            status=PaymentStatusEnum.PENDING_RECEIPT.value,
        )
        self.client.force_login(self.user)
        prefix = f"receipt-{payment.id}"

        response = self.client.post(
            reverse(
                "accounts_web:profile_payment_receipt",
                kwargs={"payment_id": payment.id},
            ),
            {
                f"{prefix}-tracking_code": "TRACK-12345",
                f"{prefix}-payer_card_last4": "1234",
                f"{prefix}-paid_amount": "250000",
                f"{prefix}-note": "Paid from my bank card",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("#billing"))
        payment.refresh_from_db()
        receipt = PaymentReceipt.objects.get(payment=payment, user=self.user)
        self.assertEqual(payment.status, PaymentStatusEnum.PENDING_VERIFICATION.value)
        self.assertEqual(receipt.tracking_code, "TRACK-12345")
        self.assertEqual(receipt.source, PaymentReceiptSourceEnum.WEB.value)

    def test_user_cannot_submit_receipt_for_another_users_payment(self):
        other_user = UserFactory.create()
        order = OrderFactory.create(user=other_user, total_amount="250000")
        payment = PaymentFactory.create(
            user=other_user,
            order=order,
            amount="250000",
            status=PaymentStatusEnum.PENDING_RECEIPT.value,
        )
        self.client.force_login(self.user)
        prefix = f"receipt-{payment.id}"

        response = self.client.post(
            reverse(
                "accounts_web:profile_payment_receipt",
                kwargs={"payment_id": payment.id},
            ),
            {f"{prefix}-tracking_code": "PRIVATE-TRACK"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(PaymentReceipt.objects.filter(payment=payment).exists())
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatusEnum.PENDING_RECEIPT.value)
