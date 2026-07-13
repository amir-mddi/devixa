import os
import tempfile
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.exceptions import ValidationError

from dealio.apps.billing.dtos import BasketAddItemDTO, BasketApplyDiscountDTO, CheckoutDTO
from dealio.apps.billing.enums import (
    DiscountTypeEnum,
    OrderStatusEnum,
    PaymentStatusEnum,
)
from dealio.apps.billing.logic import BasketLogic
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.billing.models import DiscountCode, Order, Payment, PaymentReceipt
from dealio.apps.courses.models import CourseEnrollment
from dealio.tests.factories import CourseFactory, ProjectConfigFactory, UserFactory


def receipt_image(name="receipt.png"):
    stream = BytesIO()
    Image.new("RGB", (4, 4)).save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


class BasketWebTests(TestCase):
    def setUp(self):
        ProjectConfigFactory.create()
        self.user = UserFactory.create()
        self.course_one = CourseFactory.create(price=Decimal("100000"))
        self.course_two = CourseFactory.create(price=Decimal("250000"))

    def test_basket_pages_and_mutations_require_login(self):
        response = self.client.get(reverse("billing_web:basket"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts_web:login"), response.url)

        response = self.client.post(
            reverse("billing_web:add_item"),
            {"course_id": self.course_one.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.exists())

    def test_user_can_build_one_multi_course_basket_without_duplicates(self):
        self.client.force_login(self.user)

        for course in (self.course_one, self.course_two, self.course_one):
            response = self.client.post(
                reverse("billing_web:add_item"),
                {"course_id": course.id},
            )
            self.assertEqual(response.status_code, 302)

        basket = Order.objects.get(
            user=self.user,
            status=OrderStatusEnum.PENDING.value,
            metadata__kind="basket",
        )
        self.assertEqual(basket.items.filter(is_deleted=False).count(), 2)
        self.assertEqual(basket.subtotal_amount, Decimal("350000"))
        self.assertEqual(basket.total_amount, Decimal("350000"))

        page = self.client.get(reverse("billing_web:basket"))
        self.assertContains(page, self.course_one.title)
        self.assertContains(page, self.course_two.title)
        self.assertContains(page, "2 دوره")

    def test_course_specific_discount_only_uses_eligible_item_total(self):
        discount = DiscountCode.objects.create(
            code="ONECOURSE",
            discount_type=DiscountTypeEnum.PERCENT.value,
            value=Decimal("50"),
            applies_to_all_courses=False,
        )
        discount.courses.add(self.course_one)
        logic = BasketLogic()
        logic.add_item(self.user, BasketAddItemDTO(course_id=self.course_one.id))
        logic.add_item(self.user, BasketAddItemDTO(course_id=self.course_two.id))

        summary = logic.apply_discount(
            self.user,
            BasketApplyDiscountDTO(code="onecourse"),
        )

        self.assertEqual(summary.subtotal_amount, Decimal("350000"))
        self.assertEqual(summary.discount_amount, Decimal("50000"))
        self.assertEqual(summary.total_amount, Decimal("300000"))

    def test_single_course_api_checkout_does_not_reuse_multi_course_web_basket(self):
        logic = BasketLogic()
        basket, _ = logic.add_item(
            self.user,
            BasketAddItemDTO(course_id=self.course_one.id),
        )
        logic.add_item(
            self.user,
            BasketAddItemDTO(course_id=self.course_two.id),
        )

        direct_order, created = BillingLogicRepository().create_checkout_order(
            self.user,
            CheckoutDTO(course_id=self.course_one.id),
        )

        self.assertTrue(created)
        self.assertNotEqual(direct_order.id, basket.order.id)
        self.assertEqual(direct_order.items.filter(is_deleted=False).count(), 1)
        self.assertEqual(basket.order.items.filter(is_deleted=False).count(), 2)

    def test_checkout_shows_card_to_card_and_disabled_gateway(self):
        BasketLogic().add_item(
            self.user,
            BasketAddItemDTO(course_id=self.course_one.id),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("billing_web:checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "کارت‌به‌کارت")
        self.assertContains(response, "درگاه پرداخت آنلاین")
        self.assertContains(response, "به‌زودی")

    @patch.dict(
        os.environ,
        {
            "CARD_TO_CARD_CARD_NUMBER": "6037991234567890",
            "CARD_TO_CARD_ACCOUNT_OWNER": "Dealio Academy",
            "CARD_TO_CARD_BANK_NAME": "Test Bank",
            "CARD_TO_CARD_IBAN": "IR120000000000000000000000",
        },
        clear=False,
    )
    def test_card_to_card_payment_and_receipt_upload_flow(self):
        summary, _ = BasketLogic().add_item(
            self.user,
            BasketAddItemDTO(course_id=self.course_one.id),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("billing_web:start_payment"),
            {
                "order_id": summary.order.id,
                "provider": "card_to_card",
            },
        )

        payment = Payment.objects.get(user=self.user, order=summary.order)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(payment.status, PaymentStatusEnum.PENDING_RECEIPT.value)

        detail = self.client.get(
            reverse("billing_web:payment_detail", kwargs={"payment_id": payment.id})
        )
        self.assertContains(detail, "6037 9912 3456 7890")
        self.assertContains(detail, "تصویر رسید را بارگذاری کنید")

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            upload = self.client.post(
                reverse("billing_web:upload_receipt", kwargs={"payment_id": payment.id}),
                {
                    "receipt_file": receipt_image(),
                    "tracking_code": "BANK-123456",
                    "payer_card_last4": "7890",
                    "paid_amount": "100000",
                    "note": "Paid from web checkout",
                },
            )

        self.assertEqual(upload.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentStatusEnum.PENDING_VERIFICATION.value)
        receipt = PaymentReceipt.objects.get(payment=payment, user=self.user)
        self.assertEqual(receipt.tracking_code, "BANK-123456")
        self.assertEqual(receipt.payer_card_last4, "7890")

    def test_pending_receipt_review_locks_basket_changes(self):
        summary, _ = BasketLogic().add_item(
            self.user,
            BasketAddItemDTO(course_id=self.course_one.id),
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse("billing_web:start_payment"),
            {"order_id": summary.order.id, "provider": "card_to_card"},
        )
        payment = Payment.objects.get(order=summary.order)
        self.client.post(
            reverse("billing_web:upload_receipt", kwargs={"payment_id": payment.id}),
            {"tracking_code": "LOCK-123"},
        )

        with self.assertRaises(ValidationError):
            BasketLogic().add_item(
                self.user,
                BasketAddItemDTO(course_id=self.course_two.id),
            )

    def test_free_basket_completes_without_payment(self):
        free_course = CourseFactory.create(price=Decimal("0"))
        summary, _ = BasketLogic().add_item(
            self.user,
            BasketAddItemDTO(course_id=free_course.id),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("billing_web:start_payment"),
            {"order_id": summary.order.id, "provider": "card_to_card"},
        )

        summary.order.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(summary.order.status, OrderStatusEnum.PAID.value)
        self.assertTrue(
            CourseEnrollment.objects.filter(user=self.user, course=free_course).exists()
        )
        self.assertFalse(Payment.objects.filter(order=summary.order).exists())

    def test_user_payment_page_never_exposes_another_users_payment(self):
        other_user = UserFactory.create()
        summary, _ = BasketLogic().add_item(
            other_user,
            BasketAddItemDTO(course_id=self.course_one.id),
        )
        payment = Payment.objects.create(
            order=summary.order,
            user=other_user,
            amount=summary.total_amount,
            status=PaymentStatusEnum.PENDING_RECEIPT.value,
        )
        admin = UserFactory.create_admin()
        self.client.force_login(admin)

        response = self.client.get(
            reverse("billing_web:payment_detail", kwargs={"payment_id": payment.id})
        )

        self.assertEqual(response.status_code, 404)
