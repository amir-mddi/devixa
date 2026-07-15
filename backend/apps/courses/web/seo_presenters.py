from __future__ import annotations

from django.urls import reverse

from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO, SeoProjectDTO
from backend.apps.common.web.seo.logic.structured_data_logic import SeoStructuredDataLogic
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoBreadcrumbLabelVO,
    SeoDescriptionTemplateVO,
    SeoRouteNameVO,
    SeoStaticPathVO,
    SeoTitleTemplateVO,
)


class CourseSeoPresenter:
    def __init__(self, structured_data_logic=None):
        self._structured_data_logic = structured_data_logic or SeoStructuredDataLogic()

    def course_detail(
        self,
        *,
        request,
        project_mapping: dict[str, str],
        course,
    ) -> SeoMetadataOverrideDTO:
        project = SeoProjectDTO.from_mapping(project_mapping)
        url_adapter = SeoRequestUrlAdapter.from_project(request, project)
        page_path = reverse(
            SeoRouteNameVO.COURSE_DETAIL.value,
            kwargs={"slug": course.slug},
        )
        page_url = url_adapter.absolute_url(page_path)
        description = (
            course.short_description
            or course.description
            or SeoDescriptionTemplateVO.COURSE_LIST.value.format(
                brand=project.display_name
            )
        ).strip()
        image_url = (
            url_adapter.absolute_url(course.thumbnail.url)
            if getattr(course, "thumbnail", None)
            else url_adapter.static_url(SeoStaticPathVO.OPEN_GRAPH_IMAGE.value)
        )

        return SeoMetadataOverrideDTO(
            title=SeoTitleTemplateVO.COURSE_DETAIL.value.format(
                title=course.title,
                brand=project.display_name,
            ),
            description=description[:300],
            canonical_path=page_path,
            image_path_or_url=image_url,
            structured_data=(
                self._structured_data_logic.course(
                    title=course.title,
                    description=description[:300],
                    url=page_url,
                    provider_name=project.display_name,
                    provider_url=url_adapter.origin + "/",
                    image_url=image_url,
                ),
                self._structured_data_logic.breadcrumb(
                    (
                        (
                            SeoBreadcrumbLabelVO.HOME.value,
                            url_adapter.absolute_url(reverse(SeoRouteNameVO.HOME.value)),
                        ),
                        (
                            SeoBreadcrumbLabelVO.COURSES.value,
                            url_adapter.absolute_url(
                                reverse(SeoRouteNameVO.COURSE_LIST.value)
                            ),
                        ),
                        (course.title, page_url),
                    )
                ),
            ),
        )

    def roadmap_detail(
        self,
        *,
        request,
        project_mapping: dict[str, str],
        roadmap,
    ) -> SeoMetadataOverrideDTO:
        project = SeoProjectDTO.from_mapping(project_mapping)
        url_adapter = SeoRequestUrlAdapter.from_project(request, project)
        page_path = reverse(
            SeoRouteNameVO.ROADMAP_DETAIL.value,
            kwargs={"slug": roadmap.slug},
        )
        page_url = url_adapter.absolute_url(page_path)
        description = (
            roadmap.description or SeoDescriptionTemplateVO.ROADMAP_LIST.value
        ).strip()

        return SeoMetadataOverrideDTO(
            title=SeoTitleTemplateVO.ROADMAP_DETAIL.value.format(
                title=roadmap.title,
                brand=project.display_name,
            ),
            description=description[:300],
            canonical_path=page_path,
            structured_data=(
                self._structured_data_logic.learning_resource(
                    title=roadmap.title,
                    description=description[:300],
                    url=page_url,
                    provider_name=project.display_name,
                    provider_url=url_adapter.origin + "/",
                ),
                self._structured_data_logic.breadcrumb(
                    (
                        (
                            SeoBreadcrumbLabelVO.HOME.value,
                            url_adapter.absolute_url(reverse(SeoRouteNameVO.HOME.value)),
                        ),
                        (
                            SeoBreadcrumbLabelVO.ROADMAPS.value,
                            url_adapter.absolute_url(
                                reverse(SeoRouteNameVO.ROADMAP_LIST.value)
                            ),
                        ),
                        (roadmap.title, page_url),
                    )
                ),
            ),
        )
