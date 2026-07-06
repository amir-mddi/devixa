from __future__ import annotations

from django.db import OperationalError, ProgrammingError

from dealio.apps.shared.dtos.project_config_dto import ProjectConfigDTO
from dealio.apps.shared.initial_data.initial_data.project_config_initial import build_project_config_initial_data
from dealio.apps.shared.repositories.logic import SharedApplicationLogic
from dealio.apps.shared.vo.project_config_vo import ProjectConfigFieldNameVO


def _fallback_project_config() -> ProjectConfigDTO:
    data = build_project_config_initial_data()
    return ProjectConfigDTO(
        name=data[ProjectConfigFieldNameVO.NAME.value],
        display_name=data[ProjectConfigFieldNameVO.DISPLAY_NAME.value],
        slug=data[ProjectConfigFieldNameVO.SLUG.value],
        description=data[ProjectConfigFieldNameVO.DESCRIPTION.value],
        tagline=data[ProjectConfigFieldNameVO.TAGLINE.value],
        email_domain=data[ProjectConfigFieldNameVO.EMAIL_DOMAIN.value],
        contact_email=data[ProjectConfigFieldNameVO.CONTACT_EMAIL.value],
        support_email=data[ProjectConfigFieldNameVO.SUPPORT_EMAIL.value],
        sales_email=data[ProjectConfigFieldNameVO.SALES_EMAIL.value],
        partnership_email=data[ProjectConfigFieldNameVO.PARTNERSHIP_EMAIL.value],
        github_url=data[ProjectConfigFieldNameVO.GITHUB_URL.value],
        linkedin_url=data[ProjectConfigFieldNameVO.LINKEDIN_URL.value],
        telegram_url=data[ProjectConfigFieldNameVO.TELEGRAM_URL.value],
        instagram_url=data[ProjectConfigFieldNameVO.INSTAGRAM_URL.value],
        telegram_bot_url=data[ProjectConfigFieldNameVO.TELEGRAM_BOT_URL.value],
        bale_bot_url=data[ProjectConfigFieldNameVO.BALE_BOT_URL.value],
        phone=data[ProjectConfigFieldNameVO.PHONE.value],
        address=data[ProjectConfigFieldNameVO.ADDRESS.value],
        working_hours=data[ProjectConfigFieldNameVO.WORKING_HOURS.value],
    )


def get_project_public_config() -> ProjectConfigDTO:
    try:
        config = SharedApplicationLogic().get_project_config()
    except (OperationalError, ProgrammingError):
        config = None

    return config or _fallback_project_config()


def get_project_name() -> str:
    return get_project_public_config().display_name


def get_project_slug() -> str:
    return get_project_public_config().slug


def get_project_logger_name() -> str:
    return get_project_slug()


def get_project_context() -> dict[str, str]:
    return get_project_public_config().as_context()
