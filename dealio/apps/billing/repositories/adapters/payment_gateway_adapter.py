from __future__ import annotations

import os
from abc import ABC, abstractmethod
from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4

import requests
from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError

from dealio.apps.billing.entities import PaymentGatewayRequestEntity, PaymentGatewayResultEntity
from dealio.apps.billing.enums import PaymentProviderEnum, PaymentStatusEnum
from dealio.apps.billing.vo import BillingMessagesVO


class PaymentGatewayAdapter(ABC):
    @abstractmethod
    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payment, actor, payload: dict) -> dict:
        raise NotImplementedError


class CardToCardPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Offline card-to-card payment adapter.

    It does not mark payments as paid. It only exposes bank-card instructions and
    waits for a receipt upload, then an admin manually approves/rejects it.
    """

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        authority = f"CARD-{uuid4().hex[:16].upper()}"
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url="",
            next_status=PaymentStatusEnum.PENDING_RECEIPT.value,
            raw_response={
                "provider": PaymentProviderEnum.CARD_TO_CARD.value,
                "authority": authority,
                "message": os.environ.get(
                    "CARD_TO_CARD_PAYMENT_MESSAGE",
                    "Card-to-card payment created. Upload receipt for admin verification.",
                ),
                "card_number": os.environ.get("CARD_TO_CARD_CARD_NUMBER", "") or os.environ.get("CARD_TO_CARD_NUMBER", ""),
                "account_number": os.environ.get("CARD_TO_CARD_ACCOUNT_NUMBER", ""),
                "card_holder": os.environ.get("CARD_TO_CARD_ACCOUNT_OWNER", "") or os.environ.get("CARD_TO_CARD_HOLDER", ""),
                "bank_name": os.environ.get("CARD_TO_CARD_BANK_NAME", ""),
                "iban": os.environ.get("CARD_TO_CARD_IBAN", ""),
            },
        )

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        if not getattr(actor, "is_staff", False) and not getattr(actor, "is_superuser", False):
            raise PermissionDenied(BillingMessagesVO.PAYMENT_CONFIRM_FORBIDDEN)
        return {
            "is_success": True,
            "transaction_id": payload.get("transaction_id") or f"CARD-{uuid4().hex[:16].upper()}",
            "authority": payload.get("authority") or payment.authority,
            "raw_response": {"confirmed_by": str(actor.id), "payload": payload},
        }


class ManualPaymentGatewayAdapter(CardToCardPaymentGatewayAdapter):
    """Backward compatible alias for older deployments using provider=manual."""

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        result = super().start_payment(request)
        authority = result.authority.replace("CARD-", "MANUAL-", 1)
        raw_response = {**result.raw_response, "provider": PaymentProviderEnum.MANUAL.value, "authority": authority}
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=result.payment_url,
            next_status=result.next_status,
            raw_response=raw_response,
        )


class SandboxPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Development adapter for end-to-end checkout testing.

    Enable it with PAYMENT_SANDBOX_ENABLED=true. Do not enable this provider in production.
    """

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        authority = f"SANDBOX-{uuid4().hex[:16].upper()}"
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=f"sandbox://payments/{request.payment_id}",
            next_status=PaymentStatusEnum.INITIATED.value,
            raw_response={
                "provider": PaymentProviderEnum.SANDBOX.value,
                "authority": authority,
                "message": "Sandbox payment created.",
            },
        )

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        if os.environ.get("PAYMENT_SANDBOX_ENABLED", "").strip().lower() not in {"1", "true", "yes"}:
            raise PermissionDenied("Sandbox payment is disabled.")
        is_success = payload.get("status", "succeeded") in {"succeeded", "success", "ok"}
        return {
            "is_success": is_success,
            "transaction_id": payload.get("transaction_id") or f"SANDBOX-{uuid4().hex[:16].upper()}",
            "authority": payload.get("authority") or payment.authority,
            "failure_message": "Sandbox payment failed." if not is_success else "",
            "raw_response": {"payload": payload},
        }


class PardakhtyarPaymentGatewayAdapter(PaymentGatewayAdapter):
    """HTTP adapter for Pardakhtyar-like gateways.

    Keep the exact Pardakhtyar endpoints and success codes in environment vars so
    you can plug real merchant data later without changing domain code.
    """

    def __init__(self):
        self.merchant_id = (os.environ.get("PARDAKHTYAR_MERCHANT_ID") or "").strip()
        self.request_url = (os.environ.get("PARDAKHTYAR_REQUEST_URL") or "").strip()
        self.verify_url = (os.environ.get("PARDAKHTYAR_VERIFY_URL") or "").strip()
        self.start_pay_base_url = (os.environ.get("PARDAKHTYAR_START_PAY_BASE_URL") or "").strip()
        self.callback_url = (os.environ.get("PARDAKHTYAR_CALLBACK_URL") or "").strip()
        self.timeout = float(os.environ.get("PARDAKHTYAR_HTTP_TIMEOUT_SECONDS", "12"))
        self.success_codes = {
            item.strip().lower()
            for item in os.environ.get("PARDAKHTYAR_SUCCESS_CODES", "100,0,ok,success,succeeded,paid").split(",")
            if item.strip()
        }

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        self._ensure_configured(self.request_url, self.callback_url)
        payload = {
            "merchant_id": self.merchant_id,
            "amount": self._amount_as_int(request.amount),
            "currency": request.currency,
            "description": request.description,
            "callback_url": self._callback_url(request),
            "order_id": request.order_number,
            "payment_id": str(request.payment_id),
        }
        response_payload = self._post_json(self.request_url, payload)
        authority = self._extract_first(
            response_payload,
            "authority",
            "Authority",
            "token",
            "Token",
            "ref_id",
            "RefId",
            "track_id",
            "tracking_code",
        )
        payment_url = self._extract_first(response_payload, "payment_url", "redirect_url", "url", "link", "gateway_url")
        if not payment_url and authority and self.start_pay_base_url:
            payment_url = f"{self.start_pay_base_url.rstrip('/')}/{authority}"
        if not authority or not payment_url:
            raise ValidationError({"pardakhtyar": "Could not extract authority/payment_url from gateway response.", "response": response_payload})
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=payment_url,
            next_status=PaymentStatusEnum.INITIATED.value,
            raw_response=response_payload,
        )

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        self._ensure_configured(self.verify_url)
        authority = payload.get("authority") or payload.get("Authority") or payment.authority
        callback_status = str(payload.get("status") or payload.get("Status") or "").lower()
        if callback_status and callback_status not in self.success_codes:
            return {
                "is_success": False,
                "authority": authority,
                "failure_message": f"Gateway callback status was {callback_status}.",
                "raw_response": {"callback_payload": payload},
            }

        request_payload = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": self._amount_as_int(payment.amount),
            "order_id": payment.order.order_number,
            "payment_id": str(payment.id),
        }
        response_payload = self._post_json(self.verify_url, request_payload)
        response_code = self._extract_first(response_payload, "code", "Code", "status", "Status", "result", "Result")
        is_success = str(response_code).strip().lower() in self.success_codes or bool(response_payload.get("is_success"))
        transaction_id = self._extract_first(
            response_payload,
            "transaction_id",
            "ref_id",
            "RefID",
            "refId",
            "track_id",
            "tracking_code",
        )
        return {
            "is_success": is_success,
            "transaction_id": transaction_id or payload.get("transaction_id", ""),
            "authority": authority,
            "failure_message": "Pardakhtyar verification failed." if not is_success else "",
            "raw_response": {
                "verify_request": request_payload,
                "verify_response": response_payload,
                "callback_payload": payload,
            },
        }

    def _callback_url(self, request: PaymentGatewayRequestEntity) -> str:
        query = urlencode({"payment_id": str(request.payment_id), "order_number": request.order_number})
        separator = "&" if "?" in self.callback_url else "?"
        return f"{self.callback_url}{separator}{query}"

    def _ensure_configured(self, *required_urls: str) -> None:
        if not self.merchant_id:
            raise ValidationError("PARDAKHTYAR_MERCHANT_ID is required for Pardakhtyar payments.")
        if any(not url for url in required_urls):
            raise ValidationError("Pardakhtyar endpoint settings are incomplete.")

    def _post_json(self, url: str, payload: dict) -> dict:
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self.timeout,
            )
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text}
            if response.status_code >= 400:
                raise ValidationError({"pardakhtyar": "Gateway HTTP error.", "status_code": response.status_code, "response": body})
            return body
        except requests.RequestException as exc:
            raise ValidationError({"pardakhtyar": f"Gateway connection failed: {exc}"}) from exc

    @staticmethod
    def _amount_as_int(amount: Decimal) -> int:
        return int(Decimal(amount).quantize(Decimal("1")))

    @classmethod
    def _extract_first(cls, data: dict, *keys: str):
        for key in keys:
            value = cls._deep_get(data, key)
            if value not in (None, ""):
                return value
        return ""

    @classmethod
    def _deep_get(cls, data, key: str):
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for value in data.values():
                found = cls._deep_get(value, key)
                if found not in (None, ""):
                    return found
        if isinstance(data, list):
            for value in data:
                found = cls._deep_get(value, key)
                if found not in (None, ""):
                    return found
        return ""


class PaymentGatewayFactory:
    @staticmethod
    def build(provider: str) -> PaymentGatewayAdapter:
        value = provider.value if hasattr(provider, "value") else str(provider or "").strip().lower()
        if value == PaymentProviderEnum.MANUAL.value:
            return ManualPaymentGatewayAdapter()
        if value == PaymentProviderEnum.CARD_TO_CARD.value:
            return CardToCardPaymentGatewayAdapter()
        if value == PaymentProviderEnum.PARDAKHTYAR.value:
            return PardakhtyarPaymentGatewayAdapter()
        if value == PaymentProviderEnum.SANDBOX.value:
            return SandboxPaymentGatewayAdapter()
        raise ValidationError("Unsupported payment provider.")
