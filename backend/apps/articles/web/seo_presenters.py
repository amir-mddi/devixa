from __future__ import annotations

from django.urls import reverse

from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO, SeoProjectDTO
from backend.apps.common.web.seo.enums.seo_enums import SeoOpenGraphTypeEnum
from backend.apps.common.web.seo.logic.structured_data_logic import SeoStructuredDataLogic
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoBreadcrumbLabelVO,
    SeoRouteNameVO,
    SeoStaticPathVO,
    SeoTitleTemplateVO,
)


class ArticleSeoPresenter:
    def __init__(self, structured_data_logic=None):
        self._structured_data_logic = structured_data_logic or SeoStructuredDataLogic()

    def detail(
        self,
        *,
        request,
        project_mapping: dict[str, str],
        article,
    ) -> SeoMetadataOverrideDTO:
        project = SeoProjectDTO.from_mapping(project_mapping)
        url_adapter = SeoRequestUrlAdapter.from_project(request, project)
        page_url = url_adapter.absolute_url(article.get_absolute_url())
        image_url = (
            url_adapter.absolute_url(article.cover_image.url)
            if getattr(article, "cover_image", None)
            else url_adapter.static_url(SeoStaticPathVO.OPEN_GRAPH_IMAGE.value)
        )
        author_name = (
            article.author.get_full_name()
            or article.author.username
            or project.display_name
        )
        list_route = (
            SeoRouteNameVO.NEWS_LIST.value
            if article.article_type == "news"
            else SeoRouteNameVO.BLOG_LIST.value
        )
        list_label = (
            SeoBreadcrumbLabelVO.NEWS.value
            if article.article_type == "news"
            else SeoBreadcrumbLabelVO.BLOG.value
        )

        return SeoMetadataOverrideDTO(
            title=SeoTitleTemplateVO.ARTICLE_DETAIL.value.format(
                title=article.seo_title,
                brand=project.display_name,
            ),
            description=article.seo_description[:300],
            canonical_path=article.get_absolute_url(),
            image_path_or_url=image_url,
            open_graph_type=SeoOpenGraphTypeEnum.ARTICLE.value,
            structured_data=(
                self._structured_data_logic.article(
                    article_type=article.article_type,
                    title=article.seo_title,
                    description=article.seo_description[:300],
                    url=page_url,
                    publisher_name=project.display_name,
                    publisher_logo_url=url_adapter.static_url(SeoStaticPathVO.LOGO.value),
                    published_at=article.published_at,
                    updated_at=article.updated_at,
                    image_url=image_url,
                    author_name=author_name,
                ),
                self._structured_data_logic.breadcrumb(
                    (
                        (
                            SeoBreadcrumbLabelVO.HOME.value,
                            url_adapter.absolute_url(reverse(SeoRouteNameVO.HOME.value)),
                        ),
                        (list_label, url_adapter.absolute_url(reverse(list_route))),
                        (article.title, page_url),
                    )
                ),
            ),
        )
