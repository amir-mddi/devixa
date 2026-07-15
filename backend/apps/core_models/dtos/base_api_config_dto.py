from dataclasses import dataclass
from typing import Type


@dataclass
class BaseAPIConfig:
    view: object
    request: object
    model_clz: Type
    serializer_class: Type
