from django.db import transaction

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
from dealio.apps.billing.enums import PaymentProviderEnum, PaymentStatusEnum
from dealio.apps.billing.repositories.adapters.payment_gateway_adapter import PaymentGatewayFactory
from dealio.apps.billing.repositories.adapters.postgres_adapter import BillingPostgresAdapter
from dealio.apps.common.helpers.metaclasses.singleton import Singleton


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
        payment = self.postgres_adapter.get_payment_for_user(payment_id=dto.payment_id, user=user)
        return self.postgres_adapter.upload_receipt(user=user, payment=payment, dto=dto)

    def review_receipt(self, actor, dto: PaymentReceiptReviewDTO):
        receipt = self.postgres_adapter.get_receipt_for_admin(dto.receipt_id)
        if dto.approve:
            return self.postgres_adapter.approve_receipt(receipt=receipt, actor=actor, dto=dto)
        return self.postgres_adapter.reject_receipt(receipt=receipt, actor=actor, admin_note=dto.admin_note)

    def confirm_gateway_callback(self, dto: PaymentGatewayCallbackDTO):
        provider = self.normalize_provider(dto.provider)
        payment = self.postgres_adapter.get_payment_for_gateway_callback(provider=provider, payload=dto.payload)
        gateway = PaymentGatewayFactory.build(provider)
        verification_result = gateway.verify_payment(payment=payment, actor=payment.user, payload=dto.payload)
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
    def normalize_provider(provider) -> str:
        value = provider.value if hasattr(provider, "value") else str(provider or "").strip().lower()
        if value == PaymentProviderEnum.MANUAL.value:
            return PaymentProviderEnum.CARD_TO_CARD.value
        valid_values = {item.value for item in PaymentProviderEnum}
        return value if value in valid_values else PaymentProviderEnum.CARD_TO_CARD.value
