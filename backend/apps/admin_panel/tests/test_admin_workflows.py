from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from backend.apps.billing.enums import (
    OrderStatusEnum,
    PaymentReceiptStatusEnum,
    PaymentStatusEnum,
)
from backend.apps.courses.enums import CourseStatusEnum, ReviewStatusEnum
from backend.apps.courses.models import Course, CourseEnrollment
from backend.apps.telegram_bot.models import BotSupportMessage, BotSupportTicket

User = get_user_model()

from backend.tests.factories import (
    BotSupportTicketFactory,
    CourseFactory,
    OrderFactory,
    OrderItemFactory,
    PaymentFactory,
    PaymentReceiptFactory,
    ReviewFactory,
    RoleFactory,
    TelegramProfileFactory,
    UserFactory,
)


class AdminPanelWorkflowTests(TestCase):
    def setUp(self):
        self.admin_role = RoleFactory.create(name="ادمین", symbol="admin")
        self.user_role = RoleFactory.create(name="کاربر", symbol="user")
        self.admin = UserFactory.create(role=self.admin_role)
        self.client.force_login(self.admin)

    def test_admin_can_reply_to_support_ticket(self):
        customer = UserFactory.create(role=self.user_role)
        profile = TelegramProfileFactory.create(user=customer, is_verified=True)
        ticket = BotSupportTicketFactory.create(profile=profile, user=customer)
        BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_USER,
            sender_user=customer,
            message="لطفا سفارش من را بررسی کنید",
        )

        response = self.client.post(
            reverse("admin_panel:ticket_reply", kwargs={"ticket_id": ticket.id}),
            {"message": "سفارش شما در حال بررسی است."},
        )

        self.assertRedirects(
            response,
            reverse("admin_panel:ticket_detail", kwargs={"ticket_id": ticket.id}),
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, BotSupportTicket.STATUS_ANSWERED)
        self.assertTrue(
            ticket.messages.filter(
                sender_type=BotSupportMessage.SENDER_ADMIN,
                sender_user=self.admin,
            ).exists()
        )

    def test_admin_can_approve_course_review(self):
        review = ReviewFactory.create(status=ReviewStatusEnum.PENDING.value)

        response = self.client.post(
            reverse("admin_panel:review_moderate", kwargs={"review_id": review.id}),
            {"status": ReviewStatusEnum.APPROVED.value, "admin_note": "مناسب است"},
        )

        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.status, ReviewStatusEnum.APPROVED.value)
        self.assertEqual(review.reviewed_by, self.admin)

    def test_admin_can_approve_card_to_card_receipt_and_enroll_user(self):
        customer = UserFactory.create(role=self.user_role)
        course = CourseFactory.create(price=Decimal("100000.00"))
        order = OrderFactory.create(
            user=customer,
            subtotal_amount=Decimal("100000.00"),
            total_amount=Decimal("100000.00"),
            status=OrderStatusEnum.PENDING.value,
        )
        OrderItemFactory.create(order=order, course=course)
        payment = PaymentFactory.create(
            order=order,
            user=customer,
            amount=Decimal("100000.00"),
            status=PaymentStatusEnum.PENDING_VERIFICATION.value,
        )
        receipt = PaymentReceiptFactory.create(
            payment=payment,
            user=customer,
            status=PaymentReceiptStatusEnum.PENDING.value,
            tracking_code="TRACK-100",
        )

        response = self.client.post(
            reverse("admin_panel:receipt_review", kwargs={"receipt_id": receipt.id}),
            {
                "action": "approve",
                "transaction_id": "BANK-100",
                "admin_note": "تأیید شد",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:billing"))
        receipt.refresh_from_db()
        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(receipt.status, PaymentReceiptStatusEnum.APPROVED.value)
        self.assertEqual(payment.status, PaymentStatusEnum.SUCCEEDED.value)
        self.assertEqual(order.status, OrderStatusEnum.PAID.value)
        self.assertTrue(
            CourseEnrollment.objects.filter(user=customer, course=course).exists()
        )

    def test_admin_can_create_user_from_management_form(self):
        response = self.client.post(
            reverse("admin_panel:user_create"),
            {
                "first_name": "علی",
                "last_name": "احمدی",
                "username": "newmanageruser",
                "email": "newmanageruser@gmail.com",
                "phone_number": "09123456789",
                "role_id": str(self.user_role.id),
                "is_active": "on",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:users"))
        created = User.objects.get(username="newmanageruser")
        self.assertEqual(created.role, self.user_role)
        self.assertTrue(created.check_password("StrongPass123!"))

    def test_admin_can_create_and_publish_course(self):
        response = self.client.post(
            reverse("admin_panel:course_create"),
            {
                "title": "دوره تست مدیریت",
                "short_description": "توضیح کوتاه دوره",
                "description": "توضیحات کامل دوره",
                "price": "250000",
                "currency": "irr",
                "level": "beginner",
                "status": CourseStatusEnum.PUBLISHED.value,
                "duration_minutes": "120",
                "category_id": "",
                "is_featured": "on",
            },
        )

        self.assertRedirects(response, reverse("admin_panel:courses"))
        course = Course.objects.get(title="دوره تست مدیریت")
        self.assertEqual(course.status, CourseStatusEnum.PUBLISHED.value)
        self.assertTrue(course.is_featured)


class AdminBotSettingsWorkflowTests(TestCase):
    def setUp(self):
        admin_role = RoleFactory.create(name="ادمین تنظیمات", symbol="admin")
        self.admin = UserFactory.create(role=admin_role)
        self.client.force_login(self.admin)

    def test_admin_can_save_and_reset_allow_listed_runtime_setting(self):
        from backend.apps.telegram_bot.models import BotRuntimeSetting
        from backend.apps.telegram_bot.repositories.logic.bot_setting_logic import (
            BotSettingLogicRepository,
        )

        url = f'{reverse("admin_panel:bot_settings")}?provider=commerce_bot'
        response = self.client.post(url, {"payment_sandbox_enabled": "true"})

        self.assertRedirects(response, url)
        runtime_setting = BotRuntimeSetting.objects.get(
            provider="commerce_bot",
            key="payment_sandbox_enabled",
        )
        self.assertTrue(runtime_setting.is_active)
        self.assertEqual(
            BotSettingLogicRepository().get_value(
                provider="commerce_bot",
                key="payment_sandbox_enabled",
            ),
            "true",
        )

        reset_response = self.client.post(
            reverse(
                "admin_panel:bot_setting_delete",
                kwargs={
                    "provider": "commerce_bot",
                    "key": "payment_sandbox_enabled",
                },
            )
        )

        self.assertRedirects(reset_response, url)
        runtime_setting.refresh_from_db()
        self.assertFalse(runtime_setting.is_active)

    def test_bot_settings_page_contains_rubika_provider(self):
        response = self.client.get(reverse("admin_panel:bot_settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "روبیکا")
        self.assertContains(response, "همگام‌سازی کانال")


class AdminUserDeletePermissionTests(TestCase):
    def setUp(self):
        self.admin_role = RoleFactory.create(name="ادمین حذف", symbol="admin")
        self.user_role = RoleFactory.create(name="کاربر حذف", symbol="user")
        self.admin = UserFactory.create(role=self.admin_role)
        self.client.force_login(self.admin)

    def test_admin_can_soft_delete_regular_user(self):
        customer = UserFactory.create(role=self.user_role)

        response = self.client.post(
            reverse("admin_panel:user_delete", kwargs={"user_id": customer.id})
        )

        self.assertRedirects(response, reverse("admin_panel:users"))
        customer.refresh_from_db()
        self.assertTrue(customer.is_deleted)
        self.assertFalse(customer.is_active)
        self.assertEqual(customer.user_updated_object, self.admin)

    def test_role_admin_cannot_modify_superuser(self):
        superuser = UserFactory.create(
            role=self.admin_role,
            is_staff=True,
            is_superuser=True,
        )

        response = self.client.post(
            reverse("admin_panel:user_delete", kwargs={"user_id": superuser.id})
        )

        self.assertEqual(response.status_code, 403)
        superuser.refresh_from_db()
        self.assertFalse(superuser.is_deleted)
        self.assertTrue(superuser.is_active)
