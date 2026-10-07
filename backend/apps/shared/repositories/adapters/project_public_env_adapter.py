from __future__ import annotations

import os

from backend.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    normalize_public_https_url,
)
from backend.apps.shared.dtos.project_public_runtime_config_dto import (
    ProjectPublicRuntimeConfigDTO,
)
from backend.apps.shared.vo.project_config_vo import ProjectConfigEnvNameVO


class ProjectPublicEnvAdapter:
    """Read public company contact/channel configuration from process env.

    These values intentionally do not fall back to database fields. This makes
    the deployment environment the source of truth for public contact details,
    official channels and bot links.
    """

    @staticmethod
    def _read(name: ProjectConfigEnvNameVO) -> str:
        return str(os.environ.get(name.value) or "").strip()

    @classmethod
    def _read_public_url(cls, name: ProjectConfigEnvNameVO) -> str:
        raw_value = cls._read(name)
        if not raw_value:
            return ""
        try:
            return normalize_public_https_url(raw_value, resolve_dns=False)
        except UnsafeOutboundUrlError:
            return ""

    def read(self) -> ProjectPublicRuntimeConfigDTO:
        return ProjectPublicRuntimeConfigDTO(
            contact_email=self._read(ProjectConfigEnvNameVO.CONTACT_EMAIL),
            phone=self._read(ProjectConfigEnvNameVO.PHONE),
            telegram_url=self._read_public_url(ProjectConfigEnvNameVO.TELEGRAM_URL),
            bale_url=self._read_public_url(ProjectConfigEnvNameVO.BALE_URL),
            instagram_url=self._read_public_url(ProjectConfigEnvNameVO.INSTAGRAM_URL),
            telegram_bot_url=self._read_public_url(
                ProjectConfigEnvNameVO.TELEGRAM_BOT_URL
            ),
            bale_bot_url=self._read_public_url(ProjectConfigEnvNameVO.BALE_BOT_URL),
            rubika_bot_url=self._read_public_url(
                ProjectConfigEnvNameVO.RUBIKA_BOT_URL
            ),
        )
