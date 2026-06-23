from typing import Any

from dealio.apps.core_models.dtos.base_dto import BaseDTO


class DataDto(BaseDTO):
    data: list | None | dict[str, Any]