from __future__ import annotations

import os
from abc import ABC, abstractmethod
from uuid import uuid4

from rest_framework.exceptions import PermissionDenied, ValidationError

from dealio.apps.billing.entities import PaymentGatewayRequestEntity, PaymentGatewayResultEntity
from dealio.apps.billing.enums import PaymentProviderEnum
from dealio.apps.billing.vo import BillingMessagesVO


class PaymentGatewayAdapter(ABC):
    @abstractmethod
    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payment, actor, payload: dict) -> dict:
        raise NotImplementedError


class ManualPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Offline/manual payment adapter.

    This adapter creates an auditable payment record. For security, manual payments
    can only be confirmed by staff/admin users.
    """

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        authority = f"MANUAL-{uuid4().hex[:16].upper()}"
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url="",
            raw_response={
                "provider": PaymentProviderEnum.MANUAL.value,
                "authority": authority,
                "message": "Manual payment created. Admin confirmation is required.",
            },
        )

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        if not getattr(actor, "is_staff", False) and not getattr(actor, "is_superuser", False):
            raise PermissionDenied(BillingMessagesVO.PAYMENT_CONFIRM_FORBIDDEN)
        return {
            "is_success": True,
            "transaction_id": payload.get("transaction_id") or f"MANUAL-{uuid4().hex[:16].upper()}",
            "authority": payload.get("authority") or payment.authority,
            "raw_response": {"confirmed_by": str(actor.id), "payload": payload},
        }


class SandboxPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Development adapter for end-to-end checkout testing.

    Enable it with PAYMENT_SANDBOX_ENABLED=true. Do not enable this provider in production.
    """

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        authority = f"SANDBOX-{uuid4().hex[:16].upper()}"
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=f"sandbox://payments/{request.payment_id}",
            raw_response={
                "provider": PaymentProviderEnum.SANDBOX.value,
                "authority": authority,
                "message": "Sandbox payment initiated.",
            },
        )

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        sandbox_enabled = os.environ.get("PAYMENT_SANDBOX_ENABLED")
        if sandbox_enabled is None:
            raise RuntimeError("PAYMENT_SANDBOX_ENABLED is required.")
        if sandbox_enabled.lower() not in {"1", "true", "yes"}:
            raise ValidationError("Sandbox payments are disabled.")
        status = payload.get("status", "succeeded")
        if status != "succeeded":
            return {
                "is_success": False,
                "transaction_id": payload.get("transaction_id", ""),
                "authority": payload.get("authority") or payment.authority,
                "raw_response": {"payload": payload},
                "failure_message": "Sandbox payment was not successful.",
            }
        return {
            "is_success": True,
            "transaction_id": payload.get("transaction_id") or f"SANDBOX-{uuid4().hex[:16].upper()}",
            "authority": payload.get("authority") or payment.authority,
            "raw_response": {"payload": payload},
        }


class PaymentGatewayFactory:
    @staticmethod
    def build(provider: str) -> PaymentGatewayAdapter:
        if provider == PaymentProviderEnum.MANUAL.value:
            return ManualPaymentGatewayAdapter()
        if provider == PaymentProviderEnum.SANDBOX.value:
            return SandboxPaymentGatewayAdapter()
        raise ValidationError("Unsupported payment provider.")
