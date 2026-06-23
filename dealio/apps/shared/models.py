from django.db import models

from dealio.apps.core_models.entities.base.base import BaseModel
from dealio.apps.core_models.enum.general_enum import ApiKeyStatusEnum


class ApiKeyManagerModel(BaseModel):
    api_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=255, choices=ApiKeyStatusEnum.choices(), default=ApiKeyStatusEnum.ACTIVE.value)