from decimal import Decimal

from django.test import TestCase

from dealio.apps.billing.enums import PaymentReceiptStatusEnum
from dealio.apps.billing.models import DiscountCode, DiscountRedemption, payment_receipt_upload_to
from dealio.tests.factories import (
    CourseFactory,
    OrderFactory,
    OrderItemFactory,
    PaymentFactory,
    PaymentReceiptFactory,
    UserFactory,
)


class BillingModelTests(TestCase):
    def test_order_and_payment_generate_business_numbers(self):
        order = OrderFactory.create()
        payment = PaymentFactory.create(order=order)

        self.assertTrue(order.order_number.startswith("ORD-"))
        self.assertTrue(payment.payment_number.startswith("PAY-"))

    def test_order_item_uses_course_snapshot_and_calculates_total(self):
        course = CourseFactory.create(title="Django Architecture", price=Decimal("250.00"))
        item = OrderItemFactory.create(course=course, course_title="", unit_price=Decimal("250.00"), quantity=3)

        self.assertEqual(item.course_title, "Django Architecture")
        self.assertEqual(item.total_price, Decimal("750.00"))

    def test_discount_codes_and_redemptions_are_normalized(self):
        user = UserFactory.create()
        order = OrderFactory.create(user=user)
        discount = DiscountCode.objects.create(code="  summer20 ", value=Decimal("20"))
        redemption = DiscountRedemption.objects.create(
            discount=discount,
            order=order,
            user=user,
            code=" summer20 ",
        )

        self.assertEqual(discount.code, "SUMMER20")
        self.assertEqual(redemption.code, "SUMMER20")

    def test_receipt_string_and_upload_path(self):
        receipt = PaymentReceiptFactory.create(status=PaymentReceiptStatusEnum.PENDING.value)

        path = payment_receipt_upload_to(receipt, "proof.JPG")

        self.assertIn(str(receipt.payment_id), path)
        self.assertTrue(path.endswith(".jpg"))
        self.assertIn(receipt.payment.payment_number, str(receipt))
