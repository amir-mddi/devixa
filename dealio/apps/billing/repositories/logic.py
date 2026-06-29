from django.db import transaction

from dealio.apps.billing.dtos import CheckoutDTO, PaymentConfirmDTO, PaymentStartDTO
from dealio.apps.billing.entities import PaymentGatewayRequestEntity
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

    def create_checkout_order(self, user, dto: CheckoutDTO):
        return self.postgres_adapter.get_or_create_checkout_order(user=user, course_id=dto.course_id)

    def start_payment(self, user, dto: PaymentStartDTO):
        with transaction.atomic():
            order = self.postgres_adapter.get_order_for_user(order_id=dto.order_id, user=user)
            provider = dto.provider.value if hasattr(dto.provider, "value") else dto.provider
            gateway = PaymentGatewayFactory.build(provider)
            gateway_request = PaymentGatewayRequestEntity(
                payment_id=order.id,
                order_number=order.order_number,
                amount=order.total_amount,
                currency=order.currency,
                description=f"Course order {order.order_number}",
            )
            gateway_result = gateway.start_payment(gateway_request)
            payment = self.postgres_adapter.create_payment(
                user=user,
                order=order,
                provider=provider,
                gateway_result=gateway_result,
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

    def list_orders_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_orders_for_admin(status=status)

    def list_payments_for_admin(self, status: str | None = None):
        return self.postgres_adapter.list_payments_for_admin(status=status)
