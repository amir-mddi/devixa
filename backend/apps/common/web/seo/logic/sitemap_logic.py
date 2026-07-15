from __future__ import annotations

from django.urls import reverse

from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.entities.seo_entities import SeoSitemapUrlEntity
from backend.apps.common.web.seo.enums.seo_enums import SeoChangeFrequencyEnum
from backend.apps.common.web.seo.repositories.adapters.django_content_repository import (
    DjangoSeoContentRepository,
)
from backend.apps.common.web.seo.value_objects.seo_vo import SeoRouteNameVO


class SeoSitemapLogic:
    _static_routes = (
        SeoRouteNameVO.HOME.value,
        SeoRouteNameVO.COURSE_LIST.value,
        SeoRouteNameVO.ROADMAP_LIST.value,
        SeoRouteNameVO.ARTICLE_LIST.value,
        SeoRouteNameVO.BLOG_LIST.value,
        SeoRouteNameVO.NEWS_LIST.value,
        SeoRouteNameVO.ANDROID_APP.value,
        SeoRouteNameVO.ABOUT_US.value,
        SeoRouteNameVO.CONTACT_US.value,
        SeoRouteNameVO.CHANNELS.value,
    )

    def __init__(self, repository=None):
        self._repository = repository or DjangoSeoContentRepository()

    def build(self, request, project_mapping) -> tuple[SeoSitemapUrlEntity, ...]:
        url_adapter = SeoRequestUrlAdapter.from_project(request, project_mapping)
        entries: list[SeoSitemapUrlEntity] = [
            SeoSitemapUrlEntity(
                location=url_adapter.absolute_url(reverse(route_name)),
                change_frequency=SeoChangeFrequencyEnum.WEEKLY.value,
                priority=1.0 if route_name == SeoRouteNameVO.HOME.value else 0.8,
            )
            for route_name in self._static_routes
        ]

        entries.extend(
            SeoSitemapUrlEntity(
                location=url_adapter.absolute_url(
                    reverse(
                        SeoRouteNameVO.COURSE_DETAIL.value,
                        kwargs={"slug": course.slug},
                    )
                ),
                last_modified=course.updated_at,
                change_frequency=SeoChangeFrequencyEnum.WEEKLY.value,
                priority=0.8,
            )
            for course in self._repository.list_public_courses()
        )
        entries.extend(
            SeoSitemapUrlEntity(
                location=url_adapter.absolute_url(
                    reverse(
                        SeoRouteNameVO.ROADMAP_DETAIL.value,
                        kwargs={"slug": roadmap.slug},
                    )
                ),
                change_frequency=SeoChangeFrequencyEnum.MONTHLY.value,
                priority=0.7,
            )
            for roadmap in self._repository.list_learning_roadmaps()
        )
        entries.extend(
            SeoSitemapUrlEntity(
                location=url_adapter.absolute_url(article.get_absolute_url()),
                last_modified=article.updated_at,
                change_frequency=SeoChangeFrequencyEnum.WEEKLY.value,
                priority=0.7,
            )
            for article in self._repository.list_public_articles()
        )

        unique_entries = {entry.location: entry for entry in entries}
        return tuple(unique_entries.values())
