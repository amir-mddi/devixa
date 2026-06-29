from uuid import UUID

from dealio.apps.billing.enums import PaymentProviderEnum
from dealio.apps.core_models.dtos.base_dto import BaseDTO


class CheckoutDTO(BaseDTO):
    course_id: UUID


class PaymentStartDTO(BaseDTO):
    order_id: UUID
    provider: PaymentProviderEnum = PaymentProviderEnum.MANUAL


class PaymentConfirmDTO(BaseDTO):
    payment_id: UUID
    transaction_id: str = ""
    authority: str = ""
    status: str = "succeeded"
