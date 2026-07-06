import json
from dealio.apps.common.utils.common_utils import CommonUtils
import uuid
from datetime import datetime
from typing import Dict, Any

from django.conf import settings
from django.db import models
from django.utils.timezone import now

logger = CommonUtils.get_project_logger(__name__)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(default=now)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    user_created_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_user_created",
    )
    user_updated_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(app_label)s_%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = now()
        self.updated_at = now()
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.exception(
                "Failed to save %s(id=%s): %s",
                self.__class__.__name__,
                str(self.id),
                str(e),
            )
            raise

    def delete(self, using=None, keep_parents=False, soft=True):
        try:
            if soft:
                self.deleted_at = now()
                self.is_deleted = True
                self.save()
            else:
                logger.warning(
                    "Hard delete requested. Proceeding with permanent deletion."
                )
                super().delete(using=using, keep_parents=keep_parents)
        except Exception as e:
            logger.exception(
                "Failed to delete %s(id=%s): %s",
                self.__class__.__name__,
                str(self.id),
                str(e),
            )
            raise

    @classmethod
    def bulk_create_instances(cls, instances: list):
        if not all(isinstance(obj, cls) for obj in instances):
            raise TypeError(f"All items must be instances of {cls.__name__}.")
        try:
            cls.objects.bulk_create(instances)
        except Exception as e:
            logger.exception("Bulk create failed for %s: %s", cls.__name__, str(e))
            raise

    def update_fields(self, request, data: Dict[str, Any]):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()
        self.user_updated_object = request.user
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        data = {}
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            if isinstance(value, uuid.UUID):
                value = str(value)
            data[field.name] = value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
