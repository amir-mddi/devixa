from datetime import datetime
from decimal import Decimal
from uuid import UUID

from dealio.apps.billing.enums import PaymentProviderEnum, PaymentReceiptSourceEnum
from dealio.apps.core_models.dtos.base_dto import BaseDTO


class CheckoutDTO(BaseDTO):
    course_id: UUID
    discount_code: str = ""


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


class DiscountCreateDTO(BaseDTO):
    code: str
    discount_type: str
    value: Decimal
    title: str = ""
    course_id: UUID | None = None
    usage_limit: int | None = None
    per_user_limit: int = 1
    max_discount_amount: Decimal | None = None
    minimum_order_amount: Decimal = Decimal("0.00")
    valid_until: datetime | None = None


class DiscountApplyDTO(BaseDTO):
    order_id: UUID
    code: str
