import os
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.exceptions import PermissionDenied, ValidationError

from backend.apps.billing.dtos import PaymentStartDTO
from backend.apps.billing.entities import PaymentGatewayRequestEntity
from backend.apps.billing.enums import PaymentProviderEnum, PaymentStatusEnum
from backend.apps.billing.repositories.adapters.payment_gateway_adapter import (
    CardToCardPaymentGatewayAdapter,
    ManualPaymentGatewayAdapter,
    PaymentGatewayFactory,
    SandboxPaymentGatewayAdapter,
)
from backend.apps.billing.repositories.logic import BillingLogicRepository
from backend.tests.mixins import IsolatedServiceTestMixin


class PaymentGatewayTests(SimpleTestCase):
    def setUp(self):
        self.request_entity = PaymentGatewayRequestEntity(
            payment_id=uuid4(),
            order_number="ORD-1",
            amount=Decimal("120000"),
            currency="irr",
            description="Course order",
        )

    def test_request_entity_serializes_decimal_and_uuid(self):
        payload = self.request_entity.as_payload()

        self.assertEqual(payload["amount"], "120000")
        self.assertEqual(payload["payment_id"], str(self.request_entity.payment_id))

    def test_card_to_card_start_returns_pending_receipt(self):
        result = CardToCardPaymentGatewayAdapter().start_payment(self.request_entity)

        self.assertTrue(result.authority.startswith("CARD-"))
        self.assertEqual(result.next_status, PaymentStatusEnum.PENDING_RECEIPT.value)

    def test_manual_adapter_uses_manual_authority(self):
        result = ManualPaymentGatewayAdapter().start_payment(self.request_entity)

        self.assertTrue(result.authority.startswith("MANUAL-"))
        self.assertEqual(result.raw_response["provider"], PaymentProviderEnum.MANUAL.value)

    def test_card_to_card_verification_requires_staff_actor(self):
        with self.assertRaises(PermissionDenied):
            CardToCardPaymentGatewayAdapter().verify_payment(
                payment=MagicMock(authority="AUTH"),
                actor=MagicMock(is_staff=False, is_superuser=False),
                payload={},
            )

    @patch.dict(os.environ, {"PAYMENT_SANDBOX_ENABLED": "false"}, clear=False)
    def test_sandbox_verification_is_disabled_by_default(self):
        with self.assertRaises(PermissionDenied):
            SandboxPaymentGatewayAdapter().verify_payment(MagicMock(), MagicMock(), {})

    def test_gateway_factory_rejects_unknown_provider(self):
        with self.assertRaises(ValidationError):
            PaymentGatewayFactory.build("unknown")


class BillingLogicRepositoryTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.logic = BillingLogicRepository()
        self.logic.postgres_adapter = MagicMock()

    def test_normalize_provider_keeps_valid_and_maps_manual(self):
        self.assertEqual(
            self.logic.normalize_provider(PaymentProviderEnum.MANUAL),
            PaymentProviderEnum.CARD_TO_CARD.value,
        )
        self.assertEqual(
            self.logic.normalize_provider(PaymentProviderEnum.PARDAKHTYAR),
            PaymentProviderEnum.PARDAKHTYAR.value,
        )

    @patch("backend.apps.billing.repositories.logic.PaymentGatewayFactory.build")
    def test_start_payment_skips_gateway_for_pending_verification(self, build_mock):
        order = MagicMock()
        payment = MagicMock(status=PaymentStatusEnum.PENDING_VERIFICATION.value)
        self.logic.postgres_adapter.get_order_for_user.return_value = order
        self.logic.postgres_adapter.get_or_create_pending_payment.return_value = payment

        result = self.logic.start_payment(object(), PaymentStartDTO(order_id=uuid4()))

        self.assertIs(result, payment)
        build_mock.assert_not_called()
