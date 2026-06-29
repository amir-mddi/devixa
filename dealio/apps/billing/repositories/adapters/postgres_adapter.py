from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import NotFound, ValidationError

from dealio.apps.billing.enums import OrderStatusEnum, PaymentStatusEnum
from dealio.apps.billing.models import Order, OrderItem, Payment
from dealio.apps.billing.vo import BillingMessagesVO
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.courses.enums import CourseStatusEnum
from dealio.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter
from dealio.apps.courses.vo import CourseMessagesVO


class BillingPostgresAdapter(metaclass=Singleton):
    def __init__(self):
        self.course_adapter = CoursePostgresAdapter()

    @staticmethod
    def get_order_for_user(order_id, user):
        order = (
            Order.objects.prefetch_related("items", "items__course")
            .filter(id=order_id, user=user, is_deleted=False)
            .first()
        )
        if not order:
            raise NotFound(BillingMessagesVO.ORDER_NOT_FOUND)
        return order

    @staticmethod
    def get_payment_for_user(payment_id, user):
        payment = (
            Payment.objects.select_related("order", "user")
            .prefetch_related("order__items", "order__items__course")
            .filter(id=payment_id, is_deleted=False)
            .first()
        )
        if not payment:
            raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
        if payment.user_id != user.id and not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
        return payment

    @staticmethod
    def list_user_orders(user):
        return (
            Order.objects.prefetch_related("items", "items__course", "items__course__category", "items__course__instructor")
            .filter(user=user, is_deleted=False)
            .order_by("-created_at")
        )

    @staticmethod
    def list_user_payments(user):
        return (
            Payment.objects.select_related("order")
            .prefetch_related("order__items", "order__items__course")
            .filter(user=user, is_deleted=False)
            .order_by("-created_at")
        )

    @staticmethod
    def list_orders_for_admin(status: str | None = None):
        queryset = Order.objects.select_related("user").prefetch_related("items", "items__course").filter(is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    @staticmethod
    def list_payments_for_admin(status: str | None = None):
        queryset = Payment.objects.select_related("order", "user").filter(is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    def get_or_create_checkout_order(self, user, course_id):
        course = self.course_adapter.get_course(course_id)
        if course.status != CourseStatusEnum.PUBLISHED.value or course.is_deleted or not course.is_active:
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        if self.course_adapter.user_has_active_enrollment(user, course):
            raise ValidationError(BillingMessagesVO.COURSE_ALREADY_PURCHASED)

        existing_order = (
            Order.objects.filter(
                user=user,
                status=OrderStatusEnum.PENDING.value,
                items__course=course,
                is_deleted=False,
            )
            .prefetch_related("items", "items__course")
            .order_by("-created_at")
            .first()
        )
        if existing_order:
            return existing_order, False

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                subtotal_amount=course.price,
                discount_amount=Decimal("0.00"),
                total_amount=course.price,
                currency=course.currency,
                expires_at=now() + timedelta(hours=24),
                user_created_object=user,
                user_updated_object=user,
            )
            OrderItem.objects.create(
                order=order,
                course=course,
                course_title=course.title,
                unit_price=course.price,
                quantity=1,
                total_price=course.price,
                user_created_object=user,
                user_updated_object=user,
            )
            if course.is_free:
                self.mark_order_paid(order=order, payment=None, actor=user)
            return order, True

    def create_payment(self, user, order, provider: str, gateway_result):
        if order.status == OrderStatusEnum.PAID.value:
            raise ValidationError(BillingMessagesVO.ORDER_ALREADY_PAID)
        existing_payment = Payment.objects.filter(
            order=order,
            user=user,
            provider=provider,
            status=PaymentStatusEnum.INITIATED.value,
            is_deleted=False,
        ).order_by("-created_at").first()
        if existing_payment:
            return existing_payment
        payment = Payment.objects.create(
            order=order,
            user=user,
            provider=provider,
            amount=order.total_amount,
            currency=order.currency,
            authority=gateway_result.authority,
            payment_url=gateway_result.payment_url,
            response_payload=gateway_result.raw_response,
            user_created_object=user,
            user_updated_object=user,
        )
        return payment

    def mark_payment_succeeded(self, payment, verification_result: dict, actor):
        with transaction.atomic():
            payment.status = PaymentStatusEnum.SUCCEEDED.value
            payment.transaction_id = verification_result.get("transaction_id", payment.transaction_id)
            payment.authority = verification_result.get("authority", payment.authority)
            payment.response_payload = verification_result.get("raw_response", payment.response_payload)
            payment.paid_at = now()
            payment.verified_at = now()
            payment.user_updated_object = actor
            payment.save()
            self.mark_order_paid(order=payment.order, payment=payment, actor=actor)
        return payment

    @staticmethod
    def mark_payment_failed(payment, verification_result: dict, actor):
        payment.status = PaymentStatusEnum.FAILED.value
        payment.failure_message = verification_result.get("failure_message", "Payment failed.")
        payment.response_payload = verification_result.get("raw_response", payment.response_payload)
        payment.verified_at = now()
        payment.user_updated_object = actor
        payment.save()
        return payment

    def mark_order_paid(self, order, payment, actor):
        order.status = OrderStatusEnum.PAID.value
        order.paid_at = now()
        order.user_updated_object = actor
        order.save(update_fields=["status", "paid_at", "user_updated_object", "updated_at"])
        for item in order.items.select_related("course").all():
            self.course_adapter.create_enrollment(
                user=order.user,
                course=item.course,
                source_order_number=order.order_number,
            )
        return order
