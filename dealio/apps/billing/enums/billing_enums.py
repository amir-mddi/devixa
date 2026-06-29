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
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentProviderEnum(BaseEnum):
    MANUAL = "manual"
    SANDBOX = "sandbox"
