from pydantic import PositiveInt, Field

from dealio.apps.core_models.dtos.base_dto import BaseDTO


class PaginationDTO(BaseDTO):
    page: PositiveInt = Field(default=1)
    page_size: PositiveInt = Field(default=10)