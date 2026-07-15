from __future__ import annotations

from backend.apps.common.web.seo.entities.seo_entities import SeoPageDefinitionEntity
from backend.apps.common.web.seo.enums.seo_enums import SeoOpenGraphTypeEnum
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoDescriptionTemplateVO,
    SeoRouteNameVO,
    SeoTitleTemplateVO,
)


class StaticSeoPageDefinitionRepository:
    _definitions = {
        SeoRouteNameVO.HOME.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.HOME.value,
            title_template=SeoTitleTemplateVO.HOME.value,
            description_template=SeoDescriptionTemplateVO.HOME.value,
        ),
        SeoRouteNameVO.ABOUT_US.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ABOUT_US.value,
            title_template=SeoTitleTemplateVO.ABOUT_US.value,
            description_template=SeoDescriptionTemplateVO.ABOUT_US.value,
        ),
        SeoRouteNameVO.CONTACT_US.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.CONTACT_US.value,
            title_template=SeoTitleTemplateVO.CONTACT_US.value,
            description_template=SeoDescriptionTemplateVO.CONTACT_US.value,
        ),
        SeoRouteNameVO.CHANNELS.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.CHANNELS.value,
            title_template=SeoTitleTemplateVO.CHANNELS.value,
            description_template=SeoDescriptionTemplateVO.CHANNELS.value,
        ),
        SeoRouteNameVO.ANDROID_APP.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ANDROID_APP.value,
            title_template=SeoTitleTemplateVO.ANDROID_APP.value,
            description_template=SeoDescriptionTemplateVO.ANDROID_APP.value,
        ),
        SeoRouteNameVO.COURSE_LIST.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.COURSE_LIST.value,
            title_template=SeoTitleTemplateVO.COURSE_LIST.value,
            description_template=SeoDescriptionTemplateVO.COURSE_LIST.value,
        ),
        SeoRouteNameVO.COURSE_DETAIL.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.COURSE_DETAIL.value,
            title_template=SeoTitleTemplateVO.COURSE_DETAIL.value,
            description_template=SeoDescriptionTemplateVO.COURSE_LIST.value,
        ),
        SeoRouteNameVO.ROADMAP_LIST.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ROADMAP_LIST.value,
            title_template=SeoTitleTemplateVO.ROADMAP_LIST.value,
            description_template=SeoDescriptionTemplateVO.ROADMAP_LIST.value,
        ),
        SeoRouteNameVO.ROADMAP_DETAIL.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ROADMAP_DETAIL.value,
            title_template=SeoTitleTemplateVO.ROADMAP_DETAIL.value,
            description_template=SeoDescriptionTemplateVO.ROADMAP_LIST.value,
        ),
        SeoRouteNameVO.ARTICLE_LIST.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ARTICLE_LIST.value,
            title_template=SeoTitleTemplateVO.ARTICLE_LIST.value,
            description_template=SeoDescriptionTemplateVO.ARTICLE_LIST.value,
        ),
        SeoRouteNameVO.BLOG_LIST.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.BLOG_LIST.value,
            title_template=SeoTitleTemplateVO.BLOG_LIST.value,
            description_template=SeoDescriptionTemplateVO.BLOG_LIST.value,
        ),
        SeoRouteNameVO.NEWS_LIST.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.NEWS_LIST.value,
            title_template=SeoTitleTemplateVO.NEWS_LIST.value,
            description_template=SeoDescriptionTemplateVO.NEWS_LIST.value,
        ),
        SeoRouteNameVO.ARTICLE_DETAIL.value: SeoPageDefinitionEntity(
            route_name=SeoRouteNameVO.ARTICLE_DETAIL.value,
            title_template=SeoTitleTemplateVO.ARTICLE_DETAIL.value,
            description_template=SeoDescriptionTemplateVO.ARTICLE_LIST.value,
            open_graph_type=SeoOpenGraphTypeEnum.ARTICLE.value,
        ),
    }

    def get_by_route_name(self, route_name: str | None) -> SeoPageDefinitionEntity | None:
        if not route_name:
            return None
        return self._definitions.get(route_name)
