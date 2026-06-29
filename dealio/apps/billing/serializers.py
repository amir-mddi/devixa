from rest_framework import serializers

from dealio.apps.billing.enums import PaymentProviderEnum
from dealio.apps.billing.models import Order, OrderItem, Payment
from dealio.apps.courses.serializers import CourseListSerializer


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


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)

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
            "failure_message",
            "paid_at",
            "verified_at",
            "created_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class PaymentStartSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(
        choices=[provider.value for provider in PaymentProviderEnum],
        default=PaymentProviderEnum.MANUAL.value,
        required=False,
    )


class PaymentConfirmSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField()
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    authority = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True, default="succeeded")
