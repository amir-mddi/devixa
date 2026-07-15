from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class PaymentGatewayRequestEntity:
    payment_id: UUID
    order_number: str
    amount: Decimal
    currency: str
    description: str

    def as_payload(self) -> dict:
        return {
            "payment_id": str(self.payment_id),
            "order_number": self.order_number,
            "amount": str(self.amount),
            "currency": self.currency,
            "description": self.description,
        }


@dataclass(frozen=True)
class PaymentGatewayResultEntity:
    authority: str
    payment_url: str
    raw_response: dict
    next_status: str = ""


@dataclass(frozen=True)
class PaymentGatewayVerificationEntity:
    is_success: bool
    transaction_id: str = ""
    authority: str = ""
    failure_message: str = ""
    raw_response: dict = field(default_factory=dict)
