from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import ValidationError

from dealio.apps.billing.dtos import (
    BasketAddItemDTO,
    BasketApplyDiscountDTO,
    BasketCheckoutDTO,
    BasketRemoveItemDTO,
)
from dealio.apps.billing.repositories.adapters.basket_postgres_adapter import (
    BasketPostgresAdapter,
)
from dealio.apps.billing.repositories.adapters.postgres_adapter import BillingPostgresAdapter
from dealio.apps.billing.vo import BasketWebMessageVO
from dealio.apps.common.helpers.metaclasses.singleton import Singleton


class BasketLogic(metaclass=Singleton):
    """Application use cases for the web basket, independent from HTTP/Telegram."""

    def __init__(self):
        self.basket_adapter = BasketPostgresAdapter()
        self.billing_adapter = BillingPostgresAdapter()

    def get_summary(self, user):
        basket = self.basket_adapter.get_basket(user)
        if not basket:
            return self.basket_adapter.summary(None)
        self._refresh_order(basket, user=user, preserve_invalid_discount=False, validate_courses=False)
        return self.basket_adapter.summary(basket)

    def add_item(self, user, dto: BasketAddItemDTO):
        with transaction.atomic():
            basket, created = self.basket_adapter.add_course(
                user=user,
                course_id=dto.course_id,
            )
            self._refresh_order(basket, user=user, preserve_invalid_discount=False, validate_courses=False)
        return self.basket_adapter.summary(basket), created

    def remove_item(self, user, dto: BasketRemoveItemDTO):
        with transaction.atomic():
            basket = self.basket_adapter.remove_item(user=user, item_id=dto.item_id)
            self._refresh_order(basket, user=user, preserve_invalid_discount=False, validate_courses=False)
        return self.basket_adapter.summary(basket)

    def clear(self, user):
        with transaction.atomic():
            basket = self.basket_adapter.clear(user=user)
            if basket:
                self.billing_adapter.remove_discount_from_order(order=basket, user=user)
                self.basket_adapter.update_totals(order=basket, user=user)
        return self.basket_adapter.summary(basket)

    def apply_discount(self, user, dto: BasketApplyDiscountDTO):
        with transaction.atomic():
            basket = self.basket_adapter.get_basket(user, lock=True)
            if not basket or not self.basket_adapter.active_items(basket).exists():
                raise ValidationError(BasketWebMessageVO.EMPTY.value)
            if self.basket_adapter.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            self.basket_adapter.synchronize_item_prices(order=basket, user=user, validate_courses=True)
            self.basket_adapter.update_totals(order=basket, user=user)
            self.billing_adapter.apply_discount_to_order(
                order=basket,
                code=dto.code,
                user=user,
            )
        return self.basket_adapter.summary(basket)

    def remove_discount(self, user):
        with transaction.atomic():
            basket = self.basket_adapter.get_basket(user, lock=True)
            if not basket:
                raise ValidationError(BasketWebMessageVO.EMPTY.value)
            if self.basket_adapter.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            self.billing_adapter.remove_discount_from_order(order=basket, user=user)
            self.basket_adapter.update_totals(order=basket, user=user)
        return self.basket_adapter.summary(basket)

    def prepare_checkout(self, user, dto: BasketCheckoutDTO):
        with transaction.atomic():
            basket = self.basket_adapter.get_basket_for_user(
                dto.order_id,
                user,
                lock=True,
            )
            if self.basket_adapter.basket_is_locked(basket):
                raise ValidationError(BasketWebMessageVO.BASKET_LOCKED.value)
            self._refresh_order(basket, user=user, preserve_invalid_discount=True, validate_courses=True)
            summary = self.basket_adapter.summary(basket)
            if summary.is_empty:
                raise ValidationError(BasketWebMessageVO.EMPTY.value)
            if summary.total_amount <= 0:
                self.billing_adapter.mark_order_paid(
                    order=basket,
                    payment=None,
                    actor=user,
                )
                return summary, True
        return summary, False

    def get_checkout_summary(self, user):
        summary = self.get_summary(user)
        if summary.is_empty:
            raise ValidationError(BasketWebMessageVO.EMPTY.value)
        return summary

    def _refresh_order(self, order, *, user, preserve_invalid_discount: bool, validate_courses: bool):
        self.basket_adapter.synchronize_item_prices(order=order, user=user, validate_courses=validate_courses)
        self.basket_adapter.update_totals(order=order, user=user)
        discount_code = str((order.metadata or {}).get("discount_code", "") or "")
        if not discount_code:
            return order
        try:
            self.billing_adapter.apply_discount_to_order(
                order=order,
                code=discount_code,
                user=user,
            )
        except ValidationError:
            if preserve_invalid_discount:
                raise
            self.billing_adapter.remove_discount_from_order(order=order, user=user)
        return order
