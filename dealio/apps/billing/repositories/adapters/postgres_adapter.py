from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from rest_framework.exceptions import NotFound, ValidationError

from dealio.apps.billing.enums import (
    OrderStatusEnum,
    PaymentProviderEnum,
    PaymentReceiptStatusEnum,
    PaymentStatusEnum,
    DiscountTypeEnum,
)
from dealio.apps.billing.models import DiscountCode, DiscountRedemption, Order, OrderItem, Payment, PaymentReceipt
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
            .prefetch_related("order__items", "order__items__course", "receipts")
            .filter(id=payment_id, is_deleted=False)
            .first()
        )
        if not payment:
            raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
        if payment.user_id != user.id and not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
            raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
        return payment

    @staticmethod
    def get_payment_for_gateway_callback(provider: str, payload: dict, *, lock: bool = False):
        payment_id = payload.get("payment_id") or payload.get("PaymentId") or payload.get("paymentId")
        authority = payload.get("authority") or payload.get("Authority") or payload.get("token") or payload.get("ref_id")
        order_number = payload.get("order_number") or payload.get("order_id") or payload.get("OrderId")

        queryset = Payment.objects.select_related("order", "user").filter(
            provider=provider,
            is_deleted=False,
        )
        if lock:
            queryset = queryset.select_for_update()
        if payment_id:
            payment = queryset.filter(id=payment_id).first()
            if payment:
                if authority and payment.authority and payment.authority != authority:
                    raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
                if order_number and payment.order.order_number != str(order_number):
                    raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
                return payment
        if authority:
            payment = queryset.filter(authority=authority).first()
            if payment:
                if order_number and payment.order.order_number != str(order_number):
                    raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
                return payment
        if order_number:
            payment = queryset.filter(order__order_number=order_number).order_by("-created_at").first()
            if payment:
                return payment
        raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)

    @staticmethod
    def get_receipt_for_admin(receipt_id):
        receipt = (
            PaymentReceipt.objects.select_related("payment", "payment__order", "payment__user", "user")
            .prefetch_related("payment__order__items", "payment__order__items__course")
            .filter(id=receipt_id, is_deleted=False)
            .first()
        )
        if not receipt:
            raise NotFound(BillingMessagesVO.RECEIPT_NOT_FOUND)
        return receipt

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
            .prefetch_related("order__items", "order__items__course", "receipts")
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
        queryset = Payment.objects.select_related("order", "user").prefetch_related("receipts").filter(is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    @staticmethod
    def list_receipts_for_admin(status: str | None = None):
        queryset = PaymentReceipt.objects.select_related("payment", "payment__order", "user", "reviewed_by").filter(is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    def get_or_create_checkout_order(self, user, course_id, discount_code: str = ""):
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
            if discount_code:
                self.apply_discount_to_order(order=existing_order, code=discount_code, user=user)
            if existing_order.total_amount <= Decimal("0.00"):
                self.mark_order_paid(order=existing_order, payment=None, actor=user)
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
            if discount_code:
                self.apply_discount_to_order(order=order, code=discount_code, user=user)
            if order.total_amount <= Decimal("0.00") or course.is_free:
                self.mark_order_paid(order=order, payment=None, actor=user)
            return order, True


    @staticmethod
    def normalize_discount_code(code: str) -> str:
        return (code or "").strip().upper()

    def list_discount_codes_for_admin(self):
        return (
            DiscountCode.objects
            .prefetch_related("courses")
            .filter(is_deleted=False)
            .order_by("-created_at")
        )

    def create_discount_code(self, actor, dto):
        from dealio.apps.courses.models import Course

        code = self.normalize_discount_code(dto.code)
        if not code:
            raise ValidationError("Discount code is required.")
        discount_type = str(dto.discount_type or "").strip().lower()
        if discount_type not in {DiscountTypeEnum.PERCENT.value, DiscountTypeEnum.AMOUNT.value}:
            raise ValidationError("Discount type must be percent or amount.")
        value = Decimal(str(dto.value))
        if value <= Decimal("0.00"):
            raise ValidationError("Discount value must be greater than zero.")
        if discount_type == DiscountTypeEnum.PERCENT.value and value > Decimal("100.00"):
            raise ValidationError("Percent discount cannot be greater than 100.")

        with transaction.atomic():
            discount, created = DiscountCode.objects.update_or_create(
                code=code,
                defaults={
                    "title": dto.title or code,
                    "discount_type": discount_type,
                    "value": value,
                    "max_discount_amount": dto.max_discount_amount,
                    "minimum_order_amount": dto.minimum_order_amount or Decimal("0.00"),
                    "usage_limit": dto.usage_limit,
                    "per_user_limit": max(int(dto.per_user_limit or 1), 1),
                    "valid_until": dto.valid_until,
                    "applies_to_all_courses": dto.course_id is None,
                    "is_active": True,
                    "is_deleted": False,
                    "user_updated_object": actor,
                },
            )
            if created:
                discount.user_created_object = actor
                discount.save(update_fields=["user_created_object", "updated_at"])
            discount.courses.clear()
            if dto.course_id is not None:
                course = Course.objects.filter(id=dto.course_id, is_deleted=False).first()
                if not course:
                    raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
                discount.courses.add(course)
            return discount

    @staticmethod
    def delete_discount_code(actor, discount_id):
        discount = DiscountCode.objects.filter(id=discount_id, is_deleted=False).first()
        if not discount:
            raise NotFound("Discount code not found.")
        discount.is_active = False
        discount.user_updated_object = actor
        discount.delete()
        return discount

    def apply_discount_to_order(self, *, order, code: str, user):
        normalized_code = self.normalize_discount_code(code)
        if not normalized_code:
            return order
        discount = (
            DiscountCode.objects.prefetch_related("courses")
            .filter(code=normalized_code, is_active=True, is_deleted=False)
            .first()
        )
        if not discount:
            raise ValidationError("Discount code is invalid.")
        current_time = now()
        if discount.valid_from and discount.valid_from > current_time:
            raise ValidationError("Discount code is not active yet.")
        if discount.valid_until and discount.valid_until < current_time:
            raise ValidationError("Discount code is expired.")
        if discount.usage_limit is not None and discount.used_count >= discount.usage_limit:
            raise ValidationError("Discount usage limit has been reached.")
        if order.subtotal_amount < discount.minimum_order_amount:
            raise ValidationError("Order amount is lower than this discount minimum amount.")
        course_ids = [item.course_id for item in order.items.all()]
        if not discount.applies_to_all_courses and not discount.courses.filter(id__in=course_ids).exists():
            raise ValidationError("Discount code is not valid for this course.")
        user_redemptions = DiscountRedemption.objects.filter(discount=discount, user=user, is_deleted=False).exclude(order=order).count()
        if user_redemptions >= discount.per_user_limit:
            raise ValidationError("You have already used this discount code.")

        subtotal = order.subtotal_amount
        if discount.discount_type == DiscountTypeEnum.PERCENT.value:
            amount = (subtotal * discount.value / Decimal("100.00")).quantize(Decimal("0.01"))
        else:
            amount = discount.value
        if discount.max_discount_amount is not None:
            amount = min(amount, discount.max_discount_amount)
        amount = max(Decimal("0.00"), min(amount, subtotal))

        previous = DiscountRedemption.objects.filter(order=order, is_deleted=False).first()
        if previous and previous.discount_id != discount.id:
            previous.discount.used_count = max(previous.discount.used_count - 1, 0)
            previous.discount.save(update_fields=["used_count", "updated_at"])
            previous.delete()
        redemption, created = DiscountRedemption.objects.update_or_create(
            discount=discount,
            order=order,
            defaults={
                "user": user,
                "code": discount.code,
                "amount": amount,
                "user_updated_object": user,
                "is_active": True,
                "is_deleted": False,
            },
        )
        if created:
            redemption.user_created_object = user
            redemption.save(update_fields=["user_created_object", "updated_at"])
            discount.used_count += 1
            discount.save(update_fields=["used_count", "updated_at"])

        order.discount_amount = amount
        order.total_amount = max(Decimal("0.00"), subtotal - amount)
        order.metadata = {**(order.metadata or {}), "discount_code": discount.code, "discount_id": str(discount.id)}
        order.user_updated_object = user
        order.save(update_fields=["discount_amount", "total_amount", "metadata", "user_updated_object", "updated_at"])
        return order

    @staticmethod
    def initial_status_for_provider(provider: str) -> str:
        if provider in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}:
            return PaymentStatusEnum.PENDING_RECEIPT.value
        return PaymentStatusEnum.INITIATED.value

    def get_or_create_pending_payment(self, user, order, provider: str):
        if order.status == OrderStatusEnum.PAID.value:
            raise ValidationError(BillingMessagesVO.ORDER_ALREADY_PAID)
        reusable_statuses = [
            PaymentStatusEnum.INITIATED.value,
            PaymentStatusEnum.PENDING_RECEIPT.value,
            PaymentStatusEnum.PENDING_VERIFICATION.value,
            PaymentStatusEnum.RECEIPT_REJECTED.value,
        ]
        existing_payment = (
            Payment.objects.filter(
                order=order,
                user=user,
                provider=provider,
                status__in=reusable_statuses,
                is_deleted=False,
            )
            .exclude(status=PaymentStatusEnum.FAILED.value)
            .order_by("-created_at")
            .first()
        )
        if existing_payment:
            if existing_payment.amount != order.total_amount or existing_payment.currency != order.currency:
                existing_payment.amount = order.total_amount
                existing_payment.currency = order.currency
                existing_payment.user_updated_object = user
                existing_payment.save(update_fields=["amount", "currency", "user_updated_object", "updated_at"])
            return existing_payment
        return Payment.objects.create(
            order=order,
            user=user,
            provider=provider,
            amount=order.total_amount,
            currency=order.currency,
            status=self.initial_status_for_provider(provider),
            user_created_object=user,
            user_updated_object=user,
        )

    @staticmethod
    def update_payment_gateway_result(payment, gateway_request, gateway_result, actor):
        payment.authority = gateway_result.authority
        payment.payment_url = gateway_result.payment_url
        payment.request_payload = gateway_request.as_payload()
        payment.response_payload = gateway_result.raw_response
        if gateway_result.next_status:
            payment.status = gateway_result.next_status
        payment.failure_message = ""
        payment.user_updated_object = actor
        payment.save()
        return payment

    def create_payment(self, user, order, provider: str, gateway_result):
        payment = self.get_or_create_pending_payment(user=user, order=order, provider=provider)
        payment.authority = gateway_result.authority
        payment.payment_url = gateway_result.payment_url
        payment.response_payload = gateway_result.raw_response
        if gateway_result.next_status:
            payment.status = gateway_result.next_status
        payment.user_updated_object = user
        payment.save()
        return payment

    def upload_receipt(self, user, payment, dto):
        if payment.user_id != user.id:
            raise NotFound(BillingMessagesVO.PAYMENT_NOT_FOUND)
        if payment.order.status == OrderStatusEnum.PAID.value:
            raise ValidationError(BillingMessagesVO.ORDER_ALREADY_PAID)
        if payment.provider not in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}:
            raise ValidationError(BillingMessagesVO.RECEIPT_PROVIDER_NOT_ALLOWED)
        if payment.status == PaymentStatusEnum.PENDING_VERIFICATION.value:
            raise ValidationError(BillingMessagesVO.RECEIPT_ALREADY_PENDING)
        if not dto.receipt_file and not dto.receipt_file_url and not dto.tracking_code:
            raise ValidationError(BillingMessagesVO.RECEIPT_REQUIRED)

        receipt = PaymentReceipt.objects.create(
            payment=payment,
            user=user,
            receipt_file=dto.receipt_file or "",
            receipt_file_url=dto.receipt_file_url,
            tracking_code=dto.tracking_code.strip(),
            payer_card_last4=dto.payer_card_last4.strip()[-4:],
            paid_amount=dto.paid_amount or payment.amount,
            paid_at=dto.paid_at,
            note=dto.note.strip(),
            source=dto.source.value if hasattr(dto.source, "value") else dto.source,
            user_created_object=user,
            user_updated_object=user,
        )
        payment.status = PaymentStatusEnum.PENDING_VERIFICATION.value
        payment.failure_message = ""
        payment.user_updated_object = user
        payment.save(update_fields=["status", "failure_message", "user_updated_object", "updated_at"])
        return receipt

    def approve_receipt(self, receipt, actor, dto):
        with transaction.atomic():
            receipt.status = PaymentReceiptStatusEnum.APPROVED.value
            receipt.admin_note = dto.admin_note.strip()
            receipt.reviewed_by = actor
            receipt.reviewed_at = now()
            receipt.user_updated_object = actor
            receipt.save()
            verification_result = {
                "is_success": True,
                "transaction_id": dto.transaction_id or receipt.tracking_code,
                "authority": dto.authority or receipt.payment.authority,
                "raw_response": {
                    "receipt_id": str(receipt.id),
                    "reviewed_by": str(actor.id),
                    "admin_note": receipt.admin_note,
                    "source": receipt.source,
                },
            }
            payment = self.mark_payment_succeeded(payment=receipt.payment, verification_result=verification_result, actor=actor)
        return receipt, payment

    @staticmethod
    def reject_receipt(receipt, actor, admin_note: str = ""):
        with transaction.atomic():
            receipt.status = PaymentReceiptStatusEnum.REJECTED.value
            receipt.admin_note = admin_note.strip()
            receipt.reviewed_by = actor
            receipt.reviewed_at = now()
            receipt.user_updated_object = actor
            receipt.save()
            payment = receipt.payment
            payment.status = PaymentStatusEnum.RECEIPT_REJECTED.value
            payment.failure_message = receipt.admin_note or BillingMessagesVO.RECEIPT_REJECTED
            payment.verified_at = now()
            payment.user_updated_object = actor
            payment.save(update_fields=["status", "failure_message", "verified_at", "user_updated_object", "updated_at"])
        return receipt, payment

    def mark_payment_succeeded(self, payment, verification_result: dict, actor):
        with transaction.atomic():
            payment.status = PaymentStatusEnum.SUCCEEDED.value
            payment.transaction_id = verification_result.get("transaction_id", payment.transaction_id)
            payment.authority = verification_result.get("authority", payment.authority)
            payment.response_payload = verification_result.get("raw_response", payment.response_payload)
            payment.failure_message = ""
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
