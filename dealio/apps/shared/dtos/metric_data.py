from dealio.apps.core_models.dtos.base_dto import BaseDTO


class MetricDataDto(BaseDTO):
    metric_name: str
    metric_type: str
    label_values: dict = {}
    value: float
    labels: list[str] = []
    tag: str = "dealio"
