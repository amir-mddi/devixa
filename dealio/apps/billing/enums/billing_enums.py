from dealio.apps.core_models.enum.base import BaseEnum


class CurrencyEnum(BaseEnum):
    IRR = "irr"
    USD = "usd"
    EUR = "eur"


class OrderStatusEnum(BaseEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class PaymentStatusEnum(BaseEnum):
    INITIATED = "initiated"
    PENDING_RECEIPT = "pending_receipt"
    PENDING_VERIFICATION = "pending_verification"
    RECEIPT_REJECTED = "receipt_rejected"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProviderEnum(BaseEnum):
    MANUAL = "manual"
    CARD_TO_CARD = "card_to_card"
    PARDAKHTYAR = "pardakhtyar"
    SANDBOX = "sandbox"


class PaymentReceiptStatusEnum(BaseEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PaymentReceiptSourceEnum(BaseEnum):
    WEB = "web"
    TELEGRAM = "telegram"
    BALE = "bale"
    RUBIKA = "rubika"
