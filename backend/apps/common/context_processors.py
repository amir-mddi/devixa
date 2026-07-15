from __future__ import annotations

from backend.apps.common.project_config import get_project_context
from backend.apps.common.vo.project_vo import ProjectContextKeyVO


def project_context(request):
    return {ProjectContextKeyVO.PROJECT.value: get_project_context()}
