from __future__ import annotations

import os
import re

from django.db import OperationalError, ProgrammingError, transaction

from backend.apps.shared.models import ProjectConfigModel
from backend.apps.common.utils.network_security import UnsafeOutboundUrlError, validate_public_https_url
from backend.apps.shared.vo.project_config_vo import (
    ProjectConfigDefaultVO,
    ProjectConfigEnvNameVO,
    ProjectConfigFieldNameVO,
    ProjectConfigSingletonVO,
)


def _clean(value: str | None, fallback: str = "") -> str:
    normalized = str(value or "").strip()
    return normalized or fallback


def _env(name: ProjectConfigEnvNameVO, fallback: str = "") -> str:
    return _clean(os.environ.get(name.value), fallback)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or ProjectConfigDefaultVO.SLUG.value


def _email(local_part: ProjectConfigDefaultVO, env_name: ProjectConfigEnvNameVO, domain: str) -> str:
    return _env(env_name, f"{local_part.value}@{domain}")


def _public_url(value: str) -> str:
    value = _clean(value)
    if not value:
        return ""
    try:
        return validate_public_https_url(value, resolve_dns=False)
    except UnsafeOutboundUrlError:
        return ""


def build_project_config_initial_data() -> dict[str, str]:
    name = _env(ProjectConfigEnvNameVO.NAME, ProjectConfigDefaultVO.NAME.value)
    display_name = _env(ProjectConfigEnvNameVO.DISPLAY_NAME, name)
    slug = _env(ProjectConfigEnvNameVO.SLUG, _slugify(display_name))
    email_domain = _env(ProjectConfigEnvNameVO.EMAIL_DOMAIN, ProjectConfigDefaultVO.EMAIL_DOMAIN.value)
    description = _env(
        ProjectConfigEnvNameVO.DESCRIPTION,
        ProjectConfigDefaultVO.DESCRIPTION_TEMPLATE.value.format(project_name=display_name),
    )

    return {
        ProjectConfigFieldNameVO.SINGLETON_KEY.value: ProjectConfigSingletonVO.DEFAULT_KEY.value,
        ProjectConfigFieldNameVO.NAME.value: name,
        ProjectConfigFieldNameVO.DISPLAY_NAME.value: display_name,
        ProjectConfigFieldNameVO.SLUG.value: slug,
        ProjectConfigFieldNameVO.DESCRIPTION.value: description,
        ProjectConfigFieldNameVO.TAGLINE.value: _env(ProjectConfigEnvNameVO.TAGLINE, ProjectConfigDefaultVO.TAGLINE.value),
        ProjectConfigFieldNameVO.EMAIL_DOMAIN.value: email_domain,
        ProjectConfigFieldNameVO.CONTACT_EMAIL.value: _email(
            ProjectConfigDefaultVO.CONTACT_EMAIL_LOCAL_PART,
            ProjectConfigEnvNameVO.CONTACT_EMAIL,
            email_domain,
        ),
        ProjectConfigFieldNameVO.SUPPORT_EMAIL.value: _email(
            ProjectConfigDefaultVO.SUPPORT_EMAIL_LOCAL_PART,
            ProjectConfigEnvNameVO.SUPPORT_EMAIL,
            email_domain,
        ),
        ProjectConfigFieldNameVO.SALES_EMAIL.value: _email(
            ProjectConfigDefaultVO.SALES_EMAIL_LOCAL_PART,
            ProjectConfigEnvNameVO.SALES_EMAIL,
            email_domain,
        ),
        ProjectConfigFieldNameVO.PARTNERSHIP_EMAIL.value: _email(
            ProjectConfigDefaultVO.PARTNERSHIP_EMAIL_LOCAL_PART,
            ProjectConfigEnvNameVO.PARTNERSHIP_EMAIL,
            email_domain,
        ),
        ProjectConfigFieldNameVO.GITHUB_URL.value: _public_url(_env(ProjectConfigEnvNameVO.GITHUB_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.LINKEDIN_URL.value: _public_url(_env(ProjectConfigEnvNameVO.LINKEDIN_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.TELEGRAM_URL.value: _public_url(_env(ProjectConfigEnvNameVO.TELEGRAM_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.INSTAGRAM_URL.value: _public_url(_env(ProjectConfigEnvNameVO.INSTAGRAM_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.TELEGRAM_BOT_URL.value: _public_url(_env(ProjectConfigEnvNameVO.TELEGRAM_BOT_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.BALE_BOT_URL.value: _public_url(_env(ProjectConfigEnvNameVO.BALE_BOT_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.RUBIKA_BOT_URL.value: _public_url(_env(ProjectConfigEnvNameVO.RUBIKA_BOT_URL, ProjectConfigDefaultVO.EMPTY_URL.value)),
        ProjectConfigFieldNameVO.PHONE.value: _env(ProjectConfigEnvNameVO.PHONE, ProjectConfigDefaultVO.PHONE.value),
        ProjectConfigFieldNameVO.ADDRESS.value: _env(ProjectConfigEnvNameVO.ADDRESS, ProjectConfigDefaultVO.ADDRESS.value),
        ProjectConfigFieldNameVO.WORKING_HOURS.value: _env(
            ProjectConfigEnvNameVO.WORKING_HOURS,
            ProjectConfigDefaultVO.WORKING_HOURS.value,
        ),
    }


@transaction.atomic
def initialize_project_config() -> tuple[ProjectConfigModel | None, bool]:
    try:
        defaults = build_project_config_initial_data()
        defaults.pop(ProjectConfigFieldNameVO.SINGLETON_KEY.value, None)
        obj, created = ProjectConfigModel.objects.get_or_create(
            singleton_key=ProjectConfigSingletonVO.DEFAULT_KEY.value,
            defaults=defaults,
        )
        return obj, created
    except (OperationalError, ProgrammingError):
        return None, False
