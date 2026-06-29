from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from dealio.apps.billing.enums import CurrencyEnum, OrderStatusEnum, PaymentProviderEnum, PaymentStatusEnum
from dealio.apps.core_models.entities.base.base import BaseModel


def _number(prefix: str) -> str:
    return f"{prefix}-{now().strftime('%Y%m%d')}-{uuid4().hex[:12].upper()}"


class Order(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.PROTECT,
    )
    order_number = models.CharField(max_length=60, unique=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=OrderStatusEnum.choices(),
        default=OrderStatusEnum.PENDING.value,
        db_index=True,
    )
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(
        max_length=10,
        choices=CurrencyEnum.choices(),
        default=CurrencyEnum.IRR.value,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="order_user_status_idx"),
            models.Index(fields=["order_number"], name="order_number_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = _number("ORD")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    course = models.ForeignKey(
        "courses.Course",
        related_name="order_items",
        on_delete=models.PROTECT,
    )
    course_title = models.CharField(max_length=180)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "course"], name="unique_order_course_item"),
        ]

    def save(self, *args, **kwargs):
        self.course_title = self.course_title or self.course.title
        self.unit_price = self.unit_price if self.unit_price is not None else self.course.price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number} - {self.course_title}"


class Payment(BaseModel):
    order = models.ForeignKey(Order, related_name="payments", on_delete=models.PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="payments",
        on_delete=models.PROTECT,
    )
    payment_number = models.CharField(max_length=60, unique=True, blank=True)
    provider = models.CharField(
        max_length=40,
        choices=PaymentProviderEnum.choices(),
        default=PaymentProviderEnum.MANUAL.value,
    )
    status = models.CharField(
        max_length=30,
        choices=PaymentStatusEnum.choices(),
        default=PaymentStatusEnum.INITIATED.value,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(
        max_length=10,
        choices=CurrencyEnum.choices(),
        default=CurrencyEnum.IRR.value,
    )
    authority = models.CharField(max_length=255, blank=True, default="")
    transaction_id = models.CharField(max_length=255, blank=True, default="")
    payment_url = models.URLField(blank=True, default="")
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    failure_message = models.TextField(blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="payment_user_status_idx"),
            models.Index(fields=["payment_number"], name="payment_number_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = _number("PAY")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number
