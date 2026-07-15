from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CoursePriceEntity:
    course_id: UUID
    amount: Decimal
    currency: str

    @property
    def is_free(self) -> bool:
        return self.amount <= Decimal("0.00")
