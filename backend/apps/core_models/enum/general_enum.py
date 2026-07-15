from enum import Enum

from backend.apps.core_models.enum.base import BaseEnum


class RequestMethod(Enum):
    GET = 0
    POST = 1
    PUT = 2
    DELETE = 3


class ApiKeyStatusEnum(BaseEnum):
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
