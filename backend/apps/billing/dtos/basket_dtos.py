from uuid import UUID

from backend.apps.core_models.dtos.base_dto import BaseDTO


class BasketAddItemDTO(BaseDTO):
    course_id: UUID


class BasketRemoveItemDTO(BaseDTO):
    item_id: UUID


class BasketApplyDiscountDTO(BaseDTO):
    code: str


class BasketCheckoutDTO(BaseDTO):
    order_id: UUID
