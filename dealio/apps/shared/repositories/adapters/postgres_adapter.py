import logging
from pickle import FALSE

from django.db import transaction

from dealio.apps.core_models.enum.general_enum import ApiKeyStatusEnum
from dealio.apps.shared.models import ApiKeyManagerModel

logger = logging.getLogger("dealio")


class PostgresAdapter:
    @staticmethod
    def expire_an_api_key(expired_key):
        if expired_key:
            currently_expired_key = ApiKeyManagerModel.objects.get(api_key=expired_key)
            currently_expired_key.status = ApiKeyStatusEnum.EXPIRED.value
            currently_expired_key.save()

    @staticmethod
    def fetch_newest_api_key():
        newest_active_key = ApiKeyManagerModel.objects.filter(status=ApiKeyStatusEnum.ACTIVE.value).order_by(
            '-created_at').first()
        return newest_active_key
