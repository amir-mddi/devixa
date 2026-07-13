from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence


@dataclass(frozen=True)
class BasketSummaryEntity:
    order: object | None
    items: Sequence[object]
    item_count: int
    subtotal_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    discount_code: str = ""
    is_locked: bool = False

    @property
    def is_empty(self) -> bool:
        return self.item_count == 0
