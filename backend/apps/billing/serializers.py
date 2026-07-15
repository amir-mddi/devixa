from decimal import Decimal

from rest_framework import serializers

from backend.apps.billing.enums import PaymentProviderEnum, PaymentReceiptStatusEnum
from backend.apps.billing.models import Order, OrderItem, Payment, PaymentReceipt
from backend.apps.courses.serializers import CourseListSerializer
from backend.apps.common.helpers.validators.security_validators import (
    validate_payment_receipt_file,
    validate_safe_https_url,
)


class OrderItemSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "course", "course_title", "unit_price", "quantity", "total_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "subtotal_amount",
            "discount_amount",
            "total_amount",
            "currency",
            "paid_at",
            "expires_at",
            "metadata",
            "items",
            "created_at",
        ]


class PaymentReceiptSerializer(serializers.ModelSerializer):
    receipt_file = serializers.FileField(read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = [
            "id",
            "payment",
            "status",
            "source",
            "receipt_file",
            "tracking_code",
            "payer_card_last4",
            "paid_amount",
            "paid_at",
            "note",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    receipts = PaymentReceiptSerializer(many=True, read_only=True)
    card_to_card_info = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "payment_number",
            "order",
            "provider",
            "status",
            "amount",
            "currency",
            "authority",
            "transaction_id",
            "payment_url",
            "card_to_card_info",
            "failure_message",
            "paid_at",
            "verified_at",
            "receipts",
            "created_at",
        ]

    def get_card_to_card_info(self, obj):
        if obj.provider not in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}:
            return None
        return {
            "card_number": obj.response_payload.get("card_number", ""),
            "account_number": obj.response_payload.get("account_number", ""),
            "card_holder": obj.response_payload.get("card_holder", ""),
            "bank_name": obj.response_payload.get("bank_name", ""),
            "iban": obj.response_payload.get("iban", ""),
            "message": obj.response_payload.get("message", ""),
        }


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class PaymentStartSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(
        choices=[provider.value for provider in PaymentProviderEnum],
        default=PaymentProviderEnum.CARD_TO_CARD.value,
        required=False,
    )


class PaymentConfirmSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    authority = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True, default="succeeded")


class PaymentReceiptUploadSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    receipt_file = serializers.FileField(
        required=False,
        allow_empty_file=False,
        validators=[validate_payment_receipt_file],
    )
    receipt_file_url = serializers.URLField(required=False, allow_blank=True)
    tracking_code = serializers.CharField(required=False, allow_blank=True, max_length=120)
    payer_card_last4 = serializers.RegexField(regex=r"^\d{0,4}$", required=False, allow_blank=True)
    paid_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        min_value=Decimal("0.01"),
    )
    paid_at = serializers.DateTimeField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_receipt_file_url(self, value):
        return validate_safe_https_url(value)

    def validate_tracking_code(self, value):
        value = str(value or "").strip()
        if value and not all(character.isalnum() or character in "-_/." for character in value):
            raise serializers.ValidationError("Tracking code contains unsupported characters.")
        return value

    def validate_note(self, value):
        return str(value or "").strip()

    def validate(self, attrs):
        if not attrs.get("receipt_file") and not attrs.get("receipt_file_url") and not attrs.get("tracking_code"):
            raise serializers.ValidationError("Upload a receipt file, receipt URL, or tracking code.")
        return attrs


class PaymentReceiptReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    authority = serializers.CharField(required=False, allow_blank=True)
    admin_note = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AdminPaymentReceiptSerializer(PaymentReceiptSerializer):
    payment = PaymentSerializer(read_only=True)
    reviewed_by = serializers.StringRelatedField(read_only=True)

    class Meta(PaymentReceiptSerializer.Meta):
        fields = [
            "id",
            "payment",
            "status",
            "source",
            "receipt_file",
            "receipt_file_url",
            "tracking_code",
            "payer_card_last4",
            "paid_amount",
            "paid_at",
            "note",
            "admin_note",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = fields
