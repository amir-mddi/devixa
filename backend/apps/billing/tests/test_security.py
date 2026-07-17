import json
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from backend.apps.billing.entities import PaymentGatewayRequestEntity
from backend.apps.billing.enums import PaymentStatusEnum
from backend.apps.billing.repositories.adapters.payment_gateway_adapter import (
    PardakhtyarPaymentGatewayAdapter,
)
from backend.apps.billing.serializers import PaymentReceiptSerializer
from backend.tests.factories import PaymentFactory, PaymentReceiptFactory, UserFactory


class _FakeAsyncResponse:
    def __init__(self, payload, *, status_code=200, headers=None, encoding="utf-8"):
        self.status_code = status_code
        self.encoding = encoding
        self.headers = headers or {}
        self.closed = False
        self._body = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload).encode(encoding)
        )

    async def aiter_bytes(self, chunk_size=64 * 1024):
        for offset in range(0, len(self._body), chunk_size):
            yield self._body[offset : offset + chunk_size]


class _FakeStreamContext:
    def __init__(self, response: _FakeAsyncResponse):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        self.response.closed = True


class _FakeAsyncClient:
    def __init__(self, response: _FakeAsyncResponse):
        self.response = response
        self.stream_kwargs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def stream(self, *args, **kwargs):
        self.stream_kwargs = kwargs
        return _FakeStreamContext(self.response)


@override_settings(
    IS_PROD=False,
    PARDAKHTYAR_MERCHANT_ID="merchant-secret",
    PARDAKHTYAR_REQUEST_URL="https://gateway.example/request",
    PARDAKHTYAR_VERIFY_URL="https://gateway.example/verify",
    PARDAKHTYAR_START_PAY_BASE_URL="https://pay.example/start",
    PARDAKHTYAR_CALLBACK_URL="https://api.example/callback",
    PARDAKHTYAR_ALLOWED_HOSTS=("gateway.example",),
    PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS=("pay.example",),
    PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS=("api.example",),
)
class PardakhtyarGatewaySecurityTests(SimpleTestCase):
    def setUp(self):
        self.request_entity = PaymentGatewayRequestEntity(
            payment_id=uuid4(),
            order_number="ORD-SECURITY",
            amount=Decimal("120000"),
            currency="irr",
            description="Course order",
        )

    @patch(
        "backend.apps.billing.repositories.adapters.payment_gateway_adapter.httpx.AsyncClient"
    )
    def test_provider_secrets_are_redacted_from_persisted_response(
        self,
        client_mock,
    ):
        response = _FakeAsyncResponse(
            {
                "authority": "AUTH-123",
                "payment_url": "https://pay.example/start/AUTH-123",
                "token": "provider-secret-token",
                "nested": {"merchant_id": "merchant-secret"},
            }
        )
        client_mock.return_value = _FakeAsyncClient(response)

        result = PardakhtyarPaymentGatewayAdapter().start_payment(
            self.request_entity
        )

        self.assertEqual(result.authority, "AUTH-123")
        self.assertEqual(result.raw_response["token"], "***")
        self.assertEqual(result.raw_response["nested"]["merchant_id"], "***")
        self.assertTrue(response.closed)
        self.assertFalse(client_mock.call_args.kwargs["follow_redirects"])

    @override_settings(PARDAKHTYAR_CALLBACK_URL="http://127.0.0.1/internal")
    def test_private_or_insecure_callback_configuration_is_rejected(self):
        with self.assertRaises(ValidationError):
            PardakhtyarPaymentGatewayAdapter().start_payment(self.request_entity)

    @override_settings(PARDAKHTYAR_MAX_RESPONSE_BYTES=1024)
    @patch(
        "backend.apps.billing.repositories.adapters.payment_gateway_adapter.httpx.AsyncClient"
    )
    def test_oversized_provider_response_is_rejected_and_closed(
        self,
        client_mock,
    ):
        response = _FakeAsyncResponse(b"{" + b"x" * 2048 + b"}")
        client_mock.return_value = _FakeAsyncClient(response)

        with self.assertRaises(ValidationError):
            PardakhtyarPaymentGatewayAdapter().start_payment(self.request_entity)

        self.assertTrue(response.closed)


class PaymentSerializerSecurityTests(TestCase):
    def test_public_receipt_serializer_hides_moderation_fields(self):
        reviewer = UserFactory.create_admin()
        receipt = PaymentReceiptFactory.create(
            reviewed_by=reviewer,
            admin_note="Internal fraud-review note",
        )

        data = PaymentReceiptSerializer(receipt).data

        self.assertNotIn("admin_note", data)
        self.assertNotIn("reviewed_by", data)


class PaymentCallbackSecurityTests(APITestCase):
    def setUp(self):
        cache.clear()

    @patch("backend.apps.billing.views.BillingLogicRepository.confirm_gateway_callback")
    def test_public_callback_returns_minimal_data_and_disables_caching(
        self,
        confirm_mock,
    ):
        payment = PaymentFactory.create(
            status=PaymentStatusEnum.SUCCEEDED.value,
            payment_number="PAY-PRIVATE",
            authority="AUTH-PRIVATE",
            transaction_id="TX-PRIVATE",
        )
        confirm_mock.return_value = (payment, {"is_success": True})

        response = self.client.get(
            reverse("pardakhtyar-payment-callback"),
            {"payment_id": str(payment.id), "authority": payment.authority},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Cache-Control"], "no-store")
        serialized = json.dumps(response.data, default=str)
        self.assertNotIn(payment.payment_number, serialized)
        self.assertNotIn(payment.authority, serialized)
        self.assertNotIn(payment.transaction_id, serialized)

    @patch("backend.apps.billing.views.BillingLogicRepository.confirm_gateway_callback")
    def test_invalid_callback_returns_generic_bad_request(self, confirm_mock):
        confirm_mock.side_effect = ValidationError("provider-secret-error")

        response = self.client.get(reverse("pardakhtyar-payment-callback"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        serialized = json.dumps(response.data, default=str)
        self.assertIn("Invalid payment callback", serialized)
        self.assertNotIn("provider-secret-error", serialized)

    @override_settings(
        PARDAKHTYAR_FRONTEND_SUCCESS_URL="http://127.0.0.1/internal",
        PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS=(),
    )
    def test_unsafe_frontend_redirect_is_ignored(self):
        payment = MagicMock()
        payment.id = uuid4()
        payment.order.order_number = "ORD-1"
        payment.status = PaymentStatusEnum.SUCCEEDED.value

        from backend.apps.billing.views import PaymentGatewayCallbackAPIView

        self.assertEqual(
            PaymentGatewayCallbackAPIView._redirect_url(True, payment),
            "",
        )
