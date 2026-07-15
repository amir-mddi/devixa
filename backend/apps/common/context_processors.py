from __future__ import annotations

from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.vo.project_vo import ProjectContextKeyVO
from backend.apps.common.web.seo.logic.metadata_logic import SeoMetadataLogic
from backend.apps.common.web.seo.mixins import SEO_REQUEST_ATTRIBUTE
from backend.apps.common.web.seo.value_objects.seo_vo import SeoContextKeyVO


def project_context(request):
    project = get_request_project_context(request)
    seo = getattr(request, SEO_REQUEST_ATTRIBUTE, None)
    if seo is None:
        seo = SeoMetadataLogic().build(
            request=request,
            project_mapping=project,
        )

    return {
        ProjectContextKeyVO.PROJECT.value: project,
        SeoContextKeyVO.SEO.value: seo,
    }
