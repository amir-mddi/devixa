from django.db import models

from backend.apps.core_models.entities.base.base import BaseModel
from backend.apps.core_models.enum.general_enum import ApiKeyStatusEnum
from backend.apps.shared.vo.project_config_vo import (
    ProjectConfigDefaultVO,
    ProjectConfigSingletonVO,
)


class ApiKeyManagerModel(BaseModel):
    api_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=255,
        choices=ApiKeyStatusEnum.choices(),
        default=ApiKeyStatusEnum.ACTIVE.value,
    )


class ProjectConfigModel(BaseModel):
    singleton_key = models.CharField(
        max_length=64,
        unique=True,
        default=ProjectConfigSingletonVO.DEFAULT_KEY.value,
    )
    name = models.CharField(max_length=120, default=ProjectConfigDefaultVO.NAME.value)
    display_name = models.CharField(
        max_length=120, default=ProjectConfigDefaultVO.DISPLAY_NAME.value
    )
    slug = models.SlugField(max_length=120, default=ProjectConfigDefaultVO.SLUG.value)
    description = models.TextField(blank=True, default="")
    tagline = models.CharField(
        max_length=255, blank=True, default=ProjectConfigDefaultVO.TAGLINE.value
    )
    email_domain = models.CharField(
        max_length=255, blank=True, default=ProjectConfigDefaultVO.EMAIL_DOMAIN.value
    )
    contact_email = models.EmailField(max_length=255, blank=True, default="")
    support_email = models.EmailField(max_length=255, blank=True, default="")
    sales_email = models.EmailField(max_length=255, blank=True, default="")
    partnership_email = models.EmailField(max_length=255, blank=True, default="")
    github_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    linkedin_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    telegram_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    instagram_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    telegram_bot_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    bale_bot_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    rubika_bot_url = models.URLField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.EMPTY_URL.value
    )
    phone = models.CharField(
        max_length=50, blank=True, default=ProjectConfigDefaultVO.PHONE.value
    )
    address = models.CharField(
        max_length=500, blank=True, default=ProjectConfigDefaultVO.ADDRESS.value
    )
    working_hours = models.CharField(
        max_length=255, blank=True, default=ProjectConfigDefaultVO.WORKING_HOURS.value
    )

    class Meta:
        verbose_name = "Project config"
        verbose_name_plural = "Project config"

    def __str__(self) -> str:
        return self.display_name
