from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.timezone import now

from backend.apps.billing.enums import (
    CurrencyEnum,
    OrderStatusEnum,
    PaymentProviderEnum,
    PaymentReceiptSourceEnum,
    PaymentReceiptStatusEnum,
    PaymentStatusEnum,
    DiscountTypeEnum,
)
from backend.apps.core_models.entities.base.base import BaseModel


def _number(prefix: str) -> str:
    return f"{prefix}-{now().strftime('%Y%m%d')}-{uuid4().hex[:12].upper()}"


def payment_receipt_upload_to(instance, filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"billing/receipts/{now().strftime('%Y/%m/%d')}/{instance.payment_id}/{uuid4().hex}.{extension}"


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
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
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
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])

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


class DiscountCode(BaseModel):
    code = models.CharField(max_length=60, unique=True, db_index=True)
    title = models.CharField(max_length=160, blank=True, default="")
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountTypeEnum.choices(),
        default=DiscountTypeEnum.PERCENT.value,
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    minimum_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    applies_to_all_courses = models.BooleanField(default=True)
    courses = models.ManyToManyField("courses.Course", related_name="discount_codes", blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code", "is_active", "is_deleted"], name="discount_code_active_idx"),
        ]

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class DiscountRedemption(BaseModel):
    discount = models.ForeignKey(DiscountCode, related_name="redemptions", on_delete=models.PROTECT)
    order = models.ForeignKey(Order, related_name="discount_redemptions", on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="discount_redemptions", on_delete=models.PROTECT)
    code = models.CharField(max_length=60, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["discount", "order"], name="unique_discount_order_redemption"),
        ]
        indexes = [
            models.Index(fields=["user", "code"], name="discount_user_code_idx"),
        ]

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} -> {self.order_id}"


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
        default=PaymentProviderEnum.CARD_TO_CARD.value,
    )
    status = models.CharField(
        max_length=30,
        choices=PaymentStatusEnum.choices(),
        default=PaymentStatusEnum.INITIATED.value,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
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
            models.Index(fields=["provider", "authority"], name="payment_provider_auth_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = _number("PAY")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number


class PaymentReceipt(BaseModel):
    payment = models.ForeignKey(Payment, related_name="receipts", on_delete=models.PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="payment_receipts",
        on_delete=models.PROTECT,
    )
    receipt_file = models.FileField(upload_to=payment_receipt_upload_to, blank=True, default="")
    receipt_file_url = models.URLField(blank=True, default="")
    tracking_code = models.CharField(max_length=120, blank=True, default="")
    payer_card_last4 = models.CharField(max_length=4, blank=True, default="")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    paid_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=30,
        choices=PaymentReceiptStatusEnum.choices(),
        default=PaymentReceiptStatusEnum.PENDING.value,
        db_index=True,
    )
    source = models.CharField(
        max_length=30,
        choices=PaymentReceiptSourceEnum.choices(),
        default=PaymentReceiptSourceEnum.WEB.value,
    )
    admin_note = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="billing_payment_receipts_reviewed",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["payment", "status"], name="receipt_payment_status_idx"),
            models.Index(fields=["user", "status"], name="receipt_user_status_idx"),
        ]

    def __str__(self):
        return f"{self.payment.payment_number} - {self.status}"
