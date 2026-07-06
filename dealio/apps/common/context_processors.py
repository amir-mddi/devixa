from __future__ import annotations

from dealio.apps.common.project_config import get_project_context
from dealio.apps.common.vo.project_vo import ProjectContextKeyVO


def project_context(request):
    return {ProjectContextKeyVO.PROJECT.value: get_project_context()}
