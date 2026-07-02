from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dealio.apps.billing.enums import PaymentProviderEnum, PaymentReceiptSourceEnum
from dealio.apps.core_models.dtos.base_dto import BaseDTO


class CheckoutDTO(BaseDTO):
    course_id: UUID


class PaymentStartDTO(BaseDTO):
    order_id: UUID
    provider: PaymentProviderEnum = PaymentProviderEnum.CARD_TO_CARD


class PaymentConfirmDTO(BaseDTO):
    payment_id: UUID
    transaction_id: str = ""
    authority: str = ""
    status: str = "succeeded"


class PaymentReceiptUploadDTO(BaseDTO):
    payment_id: UUID
    receipt_file: object | None = None
    receipt_file_url: str = ""
    tracking_code: str = ""
    payer_card_last4: str = ""
    paid_amount: Decimal | None = None
    paid_at: datetime | None = None
    note: str = ""
    source: PaymentReceiptSourceEnum = PaymentReceiptSourceEnum.WEB


class PaymentReceiptReviewDTO(BaseDTO):
    receipt_id: UUID
    approve: bool
    transaction_id: str = ""
    authority: str = ""
    admin_note: str = ""


class PaymentGatewayCallbackDTO(BaseDTO):
    provider: PaymentProviderEnum
    payload: dict
