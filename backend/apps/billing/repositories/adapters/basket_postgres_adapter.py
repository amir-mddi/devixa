from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import NotFound, ValidationError

from backend.apps.billing.entities import BasketSummaryEntity
from backend.apps.billing.enums import OrderStatusEnum, PaymentStatusEnum
from backend.apps.billing.models import Order, OrderItem, Payment
from backend.apps.billing.vo import BasketMetadataVO, BasketWebMessageVO
from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.courses.enums import CourseStatusEnum
from backend.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter
from backend.apps.courses.vo import CourseMessagesVO


class BasketPostgresAdapter(metaclass=Singleton):
    """Persistence adapter for a user's active web basket.

    A basket is represented by a pending Order marked with metadata.kind=basket.
    Paid/cancelled orders remain immutable billing history.
    """

    MODIFIABLE_PAYMENT_STATUSES = {
        PaymentStatusEnum.INITIATED.value,
        PaymentStatusEnum.PENDING_RECEIPT.value,
        PaymentStatusEnum.RECEIPT_REJECTED.value,
        PaymentStatusEnum.FAILED.value,
        PaymentStatusEnum.CANCELLED.value,
    }

    def __init__(self):
        self.course_adapter = CoursePostgresAdapter()

    @staticmethod
    def _basket_queryset(user, *, lock: bool = False):
        queryset = (
            Order.objects.filter(
                user=user,
                status=OrderStatusEnum.PENDING.value,
                metadata__kind=BasketMetadataVO.KIND_VALUE.value,
                is_deleted=False,
            )
            .prefetch_related(
                "items",
                "items__course",
                "items__course__category",
                "items__course__instructor",
                "payments",
                "payments__receipts",
            )
            .order_by("-created_at")
        )
        return queryset.select_for_update() if lock else queryset

    def get_basket(self, user, *, lock: bool = False):
        return self._basket_queryset(user, lock=lock).first()

    def count_items(self, user) -> int:
        basket = self.get_basket(user)
        if not basket:
            return 0
        return self.active_items(basket).count()

    def get_or_create_basket(self, user):
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=user.pk)
            basket = self.get_basket(user, lock=True)
            if basket:
                return basket, False
            basket = Order.objects.create(
                user=user,
                subtotal_amount=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                total_amount=Decimal("0.00"),
                expires_at=now() + timedelta(days=7),
                metadata={BasketMetadataVO.KIND_KEY.value: BasketMetadataVO.KIND_VALUE.value},
                user_created_object=user,
                user_updated_object=user,
            )
            return basket, True

    def get_basket_for_user(self, order_id, user, *, lock: bool = False):
        queryset = self._basket_queryset(user, lock=lock).filter(id=order_id)
        basket = queryset.first()
        if not basket:
            raise NotFound(BasketWebMessageVO.ORDER_NOT_FOUND.value)
        return basket

    @staticmethod
    def active_items(order):
        return order.items.filter(is_deleted=False).select_related(
            "course", "course__category", "course__instructor"
        ).order_by("created_at")

    @staticmethod
    def basket_is_locked(order) -> bool:
        return Payment.objects.filter(
            order=order,
            is_deleted=False,
            status=PaymentStatusEnum.PENDING_VERIFICATION.value,
        ).exists()

    def add_course(self, *, user, course_id):
        course = self.course_adapter.get_course(course_id)
        if (
            course.status != CourseStatusEnum.PUBLISHED.value
            or course.is_deleted
            or not course.is_active
        ):
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        if self.course_adapter.user_has_active_enrollment(user, course):
            raise ValidationError(BasketWebMessageVO.ALREADY_ENROLLED.value)

        with transaction.atomic():
            basket, _ = self.get_or_create_basket(user)
            basket = self.get_basket_for_user(basket.id, user, lock=True)
            if self.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            active_items = self.active_items(basket)
            had_items = active_items.exists()
            if active_items.filter(course=course).exists():
                return basket, False
            if had_items and basket.currency != course.currency:
                raise ValidationError(BasketWebMessageVO.MIXED_CURRENCY.value)
            OrderItem.objects.create(
                order=basket,
                course=course,
                course_title=course.title,
                unit_price=course.price,
                quantity=1,
                total_price=course.price,
                user_created_object=user,
                user_updated_object=user,
            )
            if not had_items:
                basket.currency = course.currency
            basket.expires_at = now() + timedelta(days=7)
            basket.user_updated_object = user
            basket.save(update_fields=["currency", "expires_at", "user_updated_object", "updated_at"])
            return basket, True

    def remove_item(self, *, user, item_id):
        with transaction.atomic():
            basket = self.get_basket(user, lock=True)
            if not basket:
                raise NotFound(BasketWebMessageVO.EMPTY.value)
            if self.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            item = self.active_items(basket).filter(id=item_id).first()
            if not item:
                raise NotFound(BasketWebMessageVO.INVALID_ACTION.value)
            item.delete(soft=False)
            basket.user_updated_object = user
            basket.save(update_fields=["user_updated_object", "updated_at"])
            return basket

    def clear(self, *, user):
        with transaction.atomic():
            basket = self.get_basket(user, lock=True)
            if not basket:
                return None
            if self.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            self.active_items(basket).delete()
            basket.user_updated_object = user
            basket.save(update_fields=["user_updated_object", "updated_at"])
            return basket

    def synchronize_item_prices(self, *, order, user, validate_courses: bool = True):
        """Refresh item snapshots and optionally enforce checkout eligibility."""
        for item in self.active_items(order):
            course = item.course
            if validate_courses and not course.is_published:
                raise ValidationError(BasketWebMessageVO.COURSE_UNAVAILABLE.value)
            if validate_courses and self.course_adapter.user_has_active_enrollment(user, course):
                raise ValidationError(BasketWebMessageVO.ALREADY_ENROLLED.value)
            changed_fields = []
            if item.course_title != course.title:
                item.course_title = course.title
                changed_fields.append("course_title")
            if item.unit_price != course.price:
                item.unit_price = course.price
                changed_fields.append("unit_price")
            expected_total = course.price * item.quantity
            if item.total_price != expected_total:
                item.total_price = expected_total
                changed_fields.append("total_price")
            if changed_fields:
                item.user_updated_object = user
                changed_fields.extend(["user_updated_object", "updated_at"])
                item.save(update_fields=changed_fields)
        return order

    def update_totals(self, *, order, user):
        subtotal = sum(
            (item.total_price for item in self.active_items(order)),
            Decimal("0.00"),
        )
        order.subtotal_amount = subtotal
        order.discount_amount = min(order.discount_amount, subtotal)
        order.total_amount = max(Decimal("0.00"), subtotal - order.discount_amount)
        order.user_updated_object = user
        order.save(
            update_fields=[
                "subtotal_amount",
                "discount_amount",
                "total_amount",
                "user_updated_object",
                "updated_at",
            ]
        )
        return order

    def summary(self, order) -> BasketSummaryEntity:
        if not order:
            return BasketSummaryEntity(
                order=None,
                items=(),
                item_count=0,
                subtotal_amount=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                total_amount=Decimal("0.00"),
                currency="irr",
            )
        items = tuple(self.active_items(order))
        metadata = order.metadata or {}
        return BasketSummaryEntity(
            order=order,
            items=items,
            item_count=len(items),
            subtotal_amount=order.subtotal_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            currency=order.currency,
            discount_code=str(metadata.get(BasketMetadataVO.DISCOUNT_CODE_KEY.value, "") or ""),
            is_locked=self.basket_is_locked(order),
        )
