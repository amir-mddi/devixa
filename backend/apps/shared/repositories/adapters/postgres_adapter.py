from backend.apps.common.utils.common_utils import CommonUtils
from django.db import transaction

from backend.apps.core_models.enum.general_enum import ApiKeyStatusEnum
from backend.apps.shared.models import ApiKeyManagerModel, ProjectConfigModel
from backend.apps.shared.vo.project_config_vo import ProjectConfigSingletonVO

logger = CommonUtils.get_project_logger(__name__)


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

    @staticmethod
    def fetch_project_config():
        return (
            ProjectConfigModel.objects.filter(
                singleton_key=ProjectConfigSingletonVO.DEFAULT_KEY.value,
                is_deleted=False,
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def change_project_config(data: dict, user=None):
        obj, _ = ProjectConfigModel.objects.get_or_create(
            singleton_key=ProjectConfigSingletonVO.DEFAULT_KEY.value,
            defaults=data,
        )

        for field_name, value in data.items():
            if hasattr(obj, field_name):
                setattr(obj, field_name, value)

        if user and getattr(user, "is_authenticated", False):
            obj.user_updated_object = user

        obj.save()
        return obj
