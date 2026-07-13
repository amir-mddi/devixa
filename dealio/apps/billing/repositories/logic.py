from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from dealio.apps.billing.dtos import (
    CheckoutDTO,
    DiscountCreateDTO,
    PaymentConfirmDTO,
    PaymentGatewayCallbackDTO,
    PaymentReceiptReviewDTO,
    PaymentReceiptUploadDTO,
    PaymentStartDTO,
)
from dealio.apps.billing.entities import PaymentGatewayRequestEntity
from dealio.apps.billing.enums import OrderStatusEnum, PaymentProviderEnum, PaymentStatusEnum
from dealio.apps.billing.repositories.adapters.payment_gateway_adapter import PaymentGatewayFactory
from dealio.apps.billing.repositories.adapters.postgres_adapter import BillingPostgresAdapter
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.helpers.validators.security_validators import (
    validate_payment_receipt_file,
    validate_safe_https_url,
)


class BillingLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = BillingPostgresAdapter()

    def list_user_orders(self, user):
        return self.postgres_adapter.list_user_orders(user)

    def list_user_payments(self, user):
        return self.postgres_adapter.list_user_payments(user)

    def get_order_for_user(self, order_id, user):
        return self.postgres_adapter.get_order_for_user(order_id, user)

    def get_payment_for_user(self, payment_id, user):
        return self.postgres_adapter.get_payment_for_user(payment_id, user)

    def create_checkout_order(self, user, dto: CheckoutDTO):
        return self.postgres_adapter.get_or_create_checkout_order(user=user, course_id=dto.course_id, discount_code=getattr(dto, "discount_code", ""))

    def start_payment(self, user, dto: PaymentStartDTO):
        with transaction.atomic():
            order = self.postgres_adapter.get_order_for_user(order_id=dto.order_id, user=user)
            provider = self.normalize_provider(dto.provider)
            payment = self.postgres_adapter.get_or_create_pending_payment(user=user, order=order, provider=provider)
            if payment.status == PaymentStatusEnum.PENDING_VERIFICATION.value:
                return payment
            gateway = PaymentGatewayFactory.build(provider)
            gateway_request = PaymentGatewayRequestEntity(
                payment_id=payment.id,
                order_number=order.order_number,
                amount=order.total_amount,
                currency=order.currency,
                description=f"Course order {order.order_number}",
            )
            gateway_result = gateway.start_payment(gateway_request)
            payment = self.postgres_adapter.update_payment_gateway_result(
                payment=payment,
                gateway_request=gateway_request,
                gateway_result=gateway_result,
                actor=user,
            )
        return payment

    def confirm_payment(self, actor, dto: PaymentConfirmDTO):
        payment = self.postgres_adapter.get_payment_for_user(payment_id=dto.payment_id, user=actor)
        gateway = PaymentGatewayFactory.build(payment.provider)
        verification_result = gateway.verify_payment(
            payment=payment,
            actor=actor,
            payload={
                "transaction_id": dto.transaction_id,
                "authority": dto.authority,
                "status": dto.status,
            },
        )
        if verification_result.get("is_success"):
            return self.postgres_adapter.mark_payment_succeeded(
                payment=payment,
                verification_result=verification_result,
                actor=actor,
            )
        return self.postgres_adapter.mark_payment_failed(
            payment=payment,
            verification_result=verification_result,
            actor=actor,
        )

    def upload_receipt(self, user, dto: PaymentReceiptUploadDTO):
        self._validate_receipt_upload(dto)
        payment = self.postgres_adapter.get_payment_for_user(payment_id=dto.payment_id, user=user)
        return self.postgres_adapter.upload_receipt(user=user, payment=payment, dto=dto)

    @staticmethod
    def can_upload_receipt(payment) -> bool:
        return bool(
            payment
            and payment.provider in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}
            and payment.order.status != OrderStatusEnum.PAID.value
            and payment.status != PaymentStatusEnum.PENDING_VERIFICATION.value
        )

    def review_receipt(self, actor, dto: PaymentReceiptReviewDTO):
        receipt = self.postgres_adapter.get_receipt_for_admin(dto.receipt_id)
        if dto.approve:
            return self.postgres_adapter.approve_receipt(receipt=receipt, actor=actor, dto=dto)
        return self.postgres_adapter.reject_receipt(receipt=receipt, actor=actor, admin_note=dto.admin_note)

    def confirm_gateway_callback(self, dto: PaymentGatewayCallbackDTO):
        provider = self.normalize_provider(dto.provider)
        payload = self._normalize_callback_payload(dto.payload)
        with transaction.atomic():
            payment = self.postgres_adapter.get_payment_for_gateway_callback(
                provider=provider,
                payload=payload,
                lock=True,
            )
            if payment.status == PaymentStatusEnum.SUCCEEDED.value:
                return payment, {
                    "is_success": True,
                    "transaction_id": payment.transaction_id,
                    "authority": payment.authority,
                    "idempotent": True,
                }
            gateway = PaymentGatewayFactory.build(provider)
            verification_result = gateway.verify_payment(
                payment=payment,
                actor=payment.user,
                payload=payload,
            )
            if verification_result.get("is_success"):
                payment = self.postgres_adapter.mark_payment_succeeded(
                    payment=payment,
                    verification_result=verification_result,
                    actor=payment.user,
                )
            else:
                payment = self.postgres_adapter.mark_payment_failed(
                    payment=payment,
                    verification_result=verification_result,
                    actor=payment.user,
                )
        return payment, verification_result


    @staticmethod
    def _normalize_callback_payload(payload: dict) -> dict:
        allowed_keys = {
            "payment_id", "PaymentId", "paymentId",
            "authority", "Authority", "token",
            "ref_id", "RefId", "refId",
            "order_number", "order_id", "OrderId",
            "status", "Status",
            "transaction_id", "track_id", "tracking_code",
            "code", "Code",
        }
        if not isinstance(payload, dict):
            raise ValidationError("Invalid payment callback payload.")

        normalized: dict[str, str] = {}
        for key, value in payload.items():
            if key not in allowed_keys or value in (None, ""):
                continue
            if isinstance(value, (dict, list, tuple, set)):
                raise ValidationError("Invalid payment callback payload.")
            text = str(value).strip()
            if len(text) > 500 or any(ord(character) < 32 for character in text):
                raise ValidationError("Invalid payment callback payload.")
            normalized[key] = text

        if not any(
            normalized.get(key)
            for key in (
                "payment_id", "PaymentId", "paymentId",
                "authority", "Authority", "token", "ref_id",
                "order_number", "order_id", "OrderId",
            )
        ):
            raise ValidationError("Payment callback identifier is required.")
        return normalized


    def list_discount_codes_for_admin(self):
        return self.postgres_adapter.list_discount_codes_for_admin()

    def create_discount_code(self, actor, dto: DiscountCreateDTO):
        return self.postgres_adapter.create_discount_code(actor=actor, dto=dto)

    def delete_discount_code(self, actor, discount_id):
        return self.postgres_adapter.delete_discount_code(actor=actor, discount_id=discount_id)

    def list_orders_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_orders_for_admin(status=status)

    def list_payments_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_payments_for_admin(status=status)

    def list_receipts_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_receipts_for_admin(status=status)

    @staticmethod
    def _validate_receipt_upload(dto: PaymentReceiptUploadDTO) -> None:
        if dto.receipt_file:
            validate_payment_receipt_file(dto.receipt_file)
        if dto.receipt_file_url:
            validate_safe_https_url(dto.receipt_file_url)

        tracking_code = str(dto.tracking_code or "").strip()
        if len(tracking_code) > 120 or any(
            not (character.isalnum() or character in "-_/.")
            for character in tracking_code
        ):
            raise ValidationError("Tracking code contains unsupported characters.")

        last4 = str(dto.payer_card_last4 or "").strip()
        if last4 and (len(last4) != 4 or not last4.isdigit()):
            raise ValidationError("Payer card last four digits must contain exactly four digits.")

        note = str(dto.note or "").strip()
        if len(note) > 1000:
            raise ValidationError("Receipt note must be at most 1000 characters.")

        if dto.paid_amount is not None and Decimal(str(dto.paid_amount)) <= 0:
            raise ValidationError("Paid amount must be greater than zero.")

        if not dto.receipt_file and not dto.receipt_file_url and not tracking_code:
            raise ValidationError("Upload a receipt file, receipt URL, or tracking code.")

    @staticmethod
    def normalize_provider(provider) -> str:
        value = provider.value if hasattr(provider, "value") else str(provider or "").strip().lower()
        if value == PaymentProviderEnum.MANUAL.value:
            return PaymentProviderEnum.CARD_TO_CARD.value
        valid_values = {item.value for item in PaymentProviderEnum}
        if value not in valid_values:
            raise ValidationError("Unsupported payment provider.")
        return value
