from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError

from backend.apps.billing.entities import PaymentGatewayRequestEntity, PaymentGatewayResultEntity
from backend.apps.billing.enums import PaymentProviderEnum, PaymentStatusEnum
from backend.apps.billing.vo import BillingMessagesVO
from backend.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)
from backend.apps.common.utils.sensitive_data import sanitize_mapping


class PaymentGatewayAdapter(ABC):
    @abstractmethod
    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payment, actor, payload: dict) -> dict:
        raise NotImplementedError

    async def astart_payment(
        self,
        request: PaymentGatewayRequestEntity,
    ) -> PaymentGatewayResultEntity:
        return await sync_to_async(
            self.start_payment,
            thread_sensitive=True,
        )(request)

    async def averify_payment(self, payment, actor, payload: dict) -> dict:
        return await sync_to_async(
            self.verify_payment,
            thread_sensitive=True,
        )(payment, actor, payload)


class CardToCardPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Offline card-to-card payment adapter."""

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
                "card_number": os.environ.get("CARD_TO_CARD_CARD_NUMBER", "")
                or os.environ.get("CARD_TO_CARD_NUMBER", ""),
                "account_number": os.environ.get("CARD_TO_CARD_ACCOUNT_NUMBER", ""),
                "card_holder": os.environ.get("CARD_TO_CARD_ACCOUNT_OWNER", "")
                or os.environ.get("CARD_TO_CARD_HOLDER", ""),
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
            "raw_response": {
                "confirmed_by": str(actor.id),
                "payload": sanitize_mapping(payload),
            },
        }


class ManualPaymentGatewayAdapter(CardToCardPaymentGatewayAdapter):
    """Backward-compatible alias for deployments using provider=manual."""

    def start_payment(self, request: PaymentGatewayRequestEntity) -> PaymentGatewayResultEntity:
        result = super().start_payment(request)
        authority = result.authority.replace("CARD-", "MANUAL-", 1)
        raw_response = {
            **result.raw_response,
            "provider": PaymentProviderEnum.MANUAL.value,
            "authority": authority,
        }
        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=result.payment_url,
            next_status=result.next_status,
            raw_response=raw_response,
        )


class SandboxPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Development-only adapter for end-to-end checkout testing."""

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
        enabled = os.environ.get("PAYMENT_SANDBOX_ENABLED", "").strip().lower() in {"1", "true", "yes"}
        if not enabled or getattr(settings, "IS_PROD", False):
            raise PermissionDenied("Sandbox payment is disabled.")
        is_success = payload.get("status", "succeeded") in {"succeeded", "success", "ok"}
        return {
            "is_success": is_success,
            "transaction_id": payload.get("transaction_id") or f"SANDBOX-{uuid4().hex[:16].upper()}",
            "authority": payload.get("authority") or payment.authority,
            "failure_message": "Sandbox payment failed." if not is_success else "",
            "raw_response": {"payload": sanitize_mapping(payload)},
        }


class PardakhtyarPaymentGatewayAdapter(PaymentGatewayAdapter):
    """Bounded HTTPS adapter for Pardakhtyar-compatible gateways."""

    DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024

    def __init__(self):
        self.merchant_id = str(getattr(settings, "PARDAKHTYAR_MERCHANT_ID", "") or "").strip()
        self.request_url = str(getattr(settings, "PARDAKHTYAR_REQUEST_URL", "") or "").strip()
        self.verify_url = str(getattr(settings, "PARDAKHTYAR_VERIFY_URL", "") or "").strip()
        self.start_pay_base_url = str(getattr(settings, "PARDAKHTYAR_START_PAY_BASE_URL", "") or "").strip()
        self.callback_url = str(getattr(settings, "PARDAKHTYAR_CALLBACK_URL", "") or "").strip()
        self.timeout = self._bounded_float(
            getattr(settings, "PARDAKHTYAR_HTTP_TIMEOUT_SECONDS", 12),
            minimum=1.0,
            maximum=30.0,
        )
        self.max_response_bytes = self._bounded_int(
            getattr(settings, "PARDAKHTYAR_MAX_RESPONSE_BYTES", self.DEFAULT_MAX_RESPONSE_BYTES),
            minimum=1024,
            maximum=5 * 1024 * 1024,
        )
        self.provider_allowed_hosts = self._host_list(
            getattr(settings, "PARDAKHTYAR_ALLOWED_HOSTS", ())
        )
        self.payment_allowed_hosts = self._host_list(
            getattr(settings, "PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS", ())
        ) or self.provider_allowed_hosts
        self.callback_allowed_hosts = self._host_list(
            getattr(settings, "PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS", ())
        )
        raw_success_codes = getattr(
            settings,
            "PARDAKHTYAR_SUCCESS_CODES",
            "100,0,ok,success,succeeded,paid",
        )
        self.success_codes = {
            item.strip().lower()
            for item in str(raw_success_codes).split(",")
            if item.strip()
        }

    async def astart_payment(
        self,
        request: PaymentGatewayRequestEntity,
    ) -> PaymentGatewayResultEntity:
        self._ensure_configured(self.request_url, self.callback_url)
        await self._avalidate_provider_url(
            self.request_url,
            self.provider_allowed_hosts,
        )
        await self._avalidate_provider_url(
            self.callback_url,
            self.callback_allowed_hosts,
        )
        if self.start_pay_base_url:
            await self._avalidate_provider_url(
                self.start_pay_base_url,
                self.payment_allowed_hosts,
            )

        payload = {
            "merchant_id": self.merchant_id,
            "amount": self._amount_as_int(request.amount),
            "currency": request.currency,
            "description": request.description,
            "callback_url": self._callback_url(request),
            "order_id": request.order_number,
            "payment_id": str(request.payment_id),
        }
        response_payload = await self._apost_json(self.request_url, payload)
        authority = self._safe_identifier(
            self._extract_first(
                response_payload,
                "authority",
                "Authority",
                "token",
                "Token",
                "ref_id",
                "RefId",
                "track_id",
                "tracking_code",
            ),
            field_name="authority",
        )
        payment_url = self._extract_first(
            response_payload,
            "payment_url",
            "redirect_url",
            "url",
            "link",
            "gateway_url",
        )
        if not payment_url and authority and self.start_pay_base_url:
            payment_url = f"{self.start_pay_base_url.rstrip('/')}/{authority}"
        if not authority or not payment_url:
            raise ValidationError(
                {"pardakhtyar": "Payment gateway returned an invalid response."}
            )
        try:
            payment_url = await sync_to_async(
                validate_public_https_url,
                thread_sensitive=False,
            )(
                str(payment_url),
                allowed_hosts=self.payment_allowed_hosts,
                resolve_dns=bool(getattr(settings, "IS_PROD", False)),
            )
        except UnsafeOutboundUrlError as exc:
            raise ValidationError(
                {
                    "pardakhtyar": (
                        "Payment gateway returned an unsafe redirect URL."
                    )
                }
            ) from exc

        return PaymentGatewayResultEntity(
            authority=authority,
            payment_url=payment_url,
            next_status=PaymentStatusEnum.INITIATED.value,
            raw_response=sanitize_mapping(response_payload),
        )

    def start_payment(
        self,
        request: PaymentGatewayRequestEntity,
    ) -> PaymentGatewayResultEntity:
        return async_to_sync(self.astart_payment)(request)

    async def averify_payment(self, payment, actor, payload: dict) -> dict:
        self._ensure_configured(self.verify_url)
        await self._avalidate_provider_url(
            self.verify_url,
            self.provider_allowed_hosts,
        )
        authority = self._safe_identifier(
            payload.get("authority")
            or payload.get("Authority")
            or payment.authority,
            field_name="authority",
        )
        callback_status = str(
            payload.get("status") or payload.get("Status") or ""
        ).strip().lower()[:100]
        if callback_status and callback_status not in self.success_codes:
            return {
                "is_success": False,
                "authority": authority,
                "failure_message": (
                    "Payment gateway callback reported a failed payment."
                ),
                "raw_response": {
                    "callback_payload": sanitize_mapping(payload)
                },
            }

        request_payload = {
            "merchant_id": self.merchant_id,
            "authority": authority,
            "amount": self._amount_as_int(payment.amount),
            "order_id": payment.order.order_number,
            "payment_id": str(payment.id),
        }
        response_payload = await self._apost_json(
            self.verify_url,
            request_payload,
        )
        response_code = self._extract_first(
            response_payload,
            "code",
            "Code",
            "status",
            "Status",
            "result",
            "Result",
        )
        is_success = (
            str(response_code).strip().lower() in self.success_codes
            or response_payload.get("is_success") is True
        )
        transaction_id = self._safe_identifier(
            self._extract_first(
                response_payload,
                "transaction_id",
                "ref_id",
                "RefID",
                "refId",
                "track_id",
                "tracking_code",
            )
            or payload.get("transaction_id", ""),
            field_name="transaction_id",
            required=False,
        )
        return {
            "is_success": is_success,
            "transaction_id": transaction_id,
            "authority": authority,
            "failure_message": (
                "Pardakhtyar verification failed." if not is_success else ""
            ),
            "raw_response": {
                "verify_response": sanitize_mapping(response_payload),
                "callback_payload": sanitize_mapping(payload),
            },
        }

    def verify_payment(self, payment, actor, payload: dict) -> dict:
        return async_to_sync(self.averify_payment)(payment, actor, payload)

    def _callback_url(self, request: PaymentGatewayRequestEntity) -> str:
        query = urlencode(
            {
                "payment_id": str(request.payment_id),
                "order_number": request.order_number,
            }
        )
        separator = "&" if "?" in self.callback_url else "?"
        return f"{self.callback_url}{separator}{query}"

    def _ensure_configured(self, *required_urls: str) -> None:
        if not self.merchant_id:
            raise ValidationError("Pardakhtyar merchant configuration is incomplete.")
        if any(not url for url in required_urls):
            raise ValidationError("Pardakhtyar endpoint settings are incomplete.")

    async def _avalidate_provider_url(
        self,
        url: str,
        allowed_hosts: tuple[str, ...],
    ) -> None:
        try:
            await sync_to_async(
                validate_public_https_url,
                thread_sensitive=False,
            )(
                url,
                allowed_hosts=allowed_hosts,
                resolve_dns=bool(getattr(settings, "IS_PROD", False)),
            )
        except UnsafeOutboundUrlError as exc:
            raise ValidationError(
                "Pardakhtyar endpoint configuration is unsafe."
            ) from exc

    def _validate_provider_url(
        self,
        url: str,
        allowed_hosts: tuple[str, ...],
    ) -> None:
        async_to_sync(self._avalidate_provider_url)(url, allowed_hosts)

    async def _apost_json(self, url: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    if 300 <= response.status_code < 400:
                        raise ValidationError(
                            {
                                "pardakhtyar": (
                                    "Payment gateway redirects are not accepted."
                                )
                            }
                        )
                    if response.status_code >= 400:
                        raise ValidationError(
                            {
                                "pardakhtyar": (
                                    "Payment gateway returned an error."
                                ),
                                "status_code": response.status_code,
                            }
                        )
                    raw_body = await self._aread_bounded_response(response)
                    try:
                        body = json.loads(
                            raw_body.decode(response.encoding or "utf-8")
                        )
                    except (
                        LookupError,
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                    ) as exc:
                        raise ValidationError(
                            {
                                "pardakhtyar": (
                                    "Payment gateway returned invalid JSON."
                                )
                            }
                        ) from exc
                    if not isinstance(body, dict):
                        raise ValidationError(
                            {
                                "pardakhtyar": (
                                    "Payment gateway returned an invalid response."
                                )
                            }
                        )
                    return body
        except ValidationError:
            raise
        except httpx.HTTPError:
            raise ValidationError(
                {"pardakhtyar": "Payment gateway connection failed."}
            ) from None

    def _post_json(self, url: str, payload: dict) -> dict:
        return async_to_sync(self._apost_json)(url, payload)

    async def _aread_bounded_response(self, response: httpx.Response) -> bytes:
        raw_length = response.headers.get("Content-Length")
        if raw_length:
            try:
                if int(raw_length) > self.max_response_bytes:
                    raise ValidationError(
                        {
                            "pardakhtyar": (
                                "Payment gateway response is too large."
                            )
                        }
                    )
            except ValueError:
                pass

        body = bytearray()
        async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > self.max_response_bytes:
                raise ValidationError(
                    {
                        "pardakhtyar": (
                            "Payment gateway response is too large."
                        )
                    }
                )
        return bytes(body)

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
    def _deep_get(cls, data, key: str, depth: int = 0):
        if depth > 10:
            return ""
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for value in data.values():
                found = cls._deep_get(value, key, depth + 1)
                if found not in (None, ""):
                    return found
        if isinstance(data, list):
            for value in data[:100]:
                found = cls._deep_get(value, key, depth + 1)
                if found not in (None, ""):
                    return found
        return ""

    @staticmethod
    def _safe_identifier(value, *, field_name: str, required: bool = True) -> str:
        value = str(value or "").strip()
        if not value and not required:
            return ""
        if not value or len(value) > 255 or any(ord(character) < 32 for character in value):
            raise ValidationError({"pardakhtyar": f"Payment gateway returned an invalid {field_name}."})
        return value

    @staticmethod
    def _host_list(value) -> tuple[str, ...]:
        if isinstance(value, str):
            value = value.split(",")
        return tuple(str(item).strip().lower() for item in (value or ()) if str(item).strip())

    @staticmethod
    def _bounded_float(value, *, minimum: float, maximum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = minimum
        return max(minimum, min(parsed, maximum))

    @staticmethod
    def _bounded_int(value, *, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = minimum
        return max(minimum, min(parsed, maximum))


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
