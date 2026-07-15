from typing import Optional

from backend.apps.core_models.dtos.base_dto import BaseDTO


class AdapterOutputDto(BaseDTO):
    data: Optional[dict | list | str] = None
    status_code: int = 200
    error_data: Optional[dict] = None
    response_header: Optional[dict] = None
