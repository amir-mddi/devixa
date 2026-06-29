from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PaymentGatewayRequestEntity:
    payment_id: UUID
    order_number: str
    amount: Decimal
    currency: str
    description: str


@dataclass(frozen=True)
class PaymentGatewayResultEntity:
    authority: str
    payment_url: str
    raw_response: dict
