from __future__ import annotations

from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO
from backend.apps.common.web.seo.logic.metadata_logic import SeoMetadataLogic
from backend.apps.common.web.seo.value_objects.seo_vo import SeoContextKeyVO

SEO_REQUEST_ATTRIBUTE = "_project_seo_metadata"


class SeoContextMixin:
    seo_logic_class = SeoMetadataLogic

    def get_seo_override(self, context: dict) -> SeoMetadataOverrideDTO | None:
        return None

    def render_to_response(self, context, **response_kwargs):
        seo = self.seo_logic_class().build(
            request=self.request,
            project_mapping=get_request_project_context(self.request),
            override=self.get_seo_override(context),
        )
        setattr(self.request, SEO_REQUEST_ATTRIBUTE, seo)
        context[SeoContextKeyVO.SEO.value] = seo
        return super().render_to_response(context, **response_kwargs)
