from __future__ import annotations

import json
from typing import Any, Mapping

from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.dtos.seo_dtos import (
    SeoMetadataDTO,
    SeoMetadataOverrideDTO,
    SeoProjectDTO,
)
from backend.apps.common.web.seo.enums.seo_enums import (
    SeoOpenGraphTypeEnum,
    SeoRobotsDirectiveEnum,
)
from backend.apps.common.web.seo.logic.structured_data_logic import SeoStructuredDataLogic
from backend.apps.common.web.seo.repositories.adapters.static_page_repository import (
    StaticSeoPageDefinitionRepository,
)
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoRouteNameVO,
    SeoStaticPathVO,
)


class SeoMetadataLogic:
    def __init__(
        self,
        *,
        page_repository=None,
        structured_data_logic=None,
    ):
        self._page_repository = page_repository or StaticSeoPageDefinitionRepository()
        self._structured_data_logic = structured_data_logic or SeoStructuredDataLogic()

    @staticmethod
    def _route_name(request) -> str | None:
        resolver_match = getattr(request, "resolver_match", None)
        return getattr(resolver_match, "view_name", None)

    @staticmethod
    def _render_template(value: str, project: SeoProjectDTO) -> str:
        return value.format(brand=project.display_name, title=project.display_name)

    @staticmethod
    def _json_dumps(payload: Mapping[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    def build(
        self,
        *,
        request,
        project_mapping: Mapping[str, Any],
        override: SeoMetadataOverrideDTO | None = None,
    ) -> SeoMetadataDTO:
        project = SeoProjectDTO.from_mapping(project_mapping)
        url_adapter = SeoRequestUrlAdapter.from_project(request, project)
        definition = self._page_repository.get_by_route_name(self._route_name(request))
        override = override or SeoMetadataOverrideDTO()

        if definition:
            default_title = self._render_template(definition.title_template, project)
            default_description = self._render_template(definition.description_template, project)
            indexable = definition.indexable
            default_og_type = definition.open_graph_type
        else:
            default_title = project.display_name
            default_description = project.description or project.tagline
            indexable = False
            default_og_type = SeoOpenGraphTypeEnum.WEBSITE.value

        canonical_url = url_adapter.canonical_url(override.canonical_path)
        image_url = (
            url_adapter.absolute_url(override.image_path_or_url)
            if override.image_path_or_url
            else url_adapter.static_url(SeoStaticPathVO.OPEN_GRAPH_IMAGE.value)
        )
        if override.robots:
            robots = override.robots
        elif not indexable:
            robots = SeoRobotsDirectiveEnum.NOINDEX.value
        elif request.GET:
            robots = SeoRobotsDirectiveEnum.NOINDEX_FOLLOW.value
        else:
            robots = SeoRobotsDirectiveEnum.INDEX.value

        structured_data = list(override.structured_data)
        if self._route_name(request) == SeoRouteNameVO.HOME.value:
            structured_data.insert(
                0,
                self._structured_data_logic.organization(
                    project=project,
                    origin=url_adapter.origin,
                    logo_url=url_adapter.static_url(SeoStaticPathVO.LOGO.value),
                ),
            )
            structured_data.insert(
                0,
                self._structured_data_logic.website(project=project, origin=url_adapter.origin),
            )

        return SeoMetadataDTO(
            title=(override.title or default_title).strip(),
            description=(override.description or default_description).strip(),
            canonical_url=canonical_url,
            robots=robots,
            site_name=project.display_name,
            locale="fa_IR",
            open_graph_type=override.open_graph_type or default_og_type,
            image_url=image_url,
            twitter_card="summary_large_image",
            structured_data_json=tuple(self._json_dumps(item) for item in structured_data),
        )
