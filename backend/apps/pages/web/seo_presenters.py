from __future__ import annotations

from django.urls import reverse

from backend.apps.common.web.seo.adapters.request_url_adapter import SeoRequestUrlAdapter
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO, SeoProjectDTO
from backend.apps.common.web.seo.logic.structured_data_logic import SeoStructuredDataLogic
from backend.apps.common.web.seo.value_objects.seo_vo import (
    SeoBreadcrumbLabelVO,
    SeoDescriptionTemplateVO,
    SeoSchemaNameTemplateVO,
    SeoStaticPathVO,
    SeoTitleTemplateVO,
)
from backend.apps.pages.vo.page_vo import PageAndroidAppVO, PageWebReverseNameVO


class PageSeoPresenter:
    def __init__(self, structured_data_logic=None):
        self._structured_data_logic = structured_data_logic or SeoStructuredDataLogic()

    def android_app(self, *, request, project_mapping: dict[str, str]) -> SeoMetadataOverrideDTO:
        project = SeoProjectDTO.from_mapping(project_mapping)
        url_adapter = SeoRequestUrlAdapter.from_project(request, project)
        page_url = url_adapter.absolute_url(reverse(PageWebReverseNameVO.ANDROID_APP.value))
        download_url = url_adapter.absolute_url(
            reverse(PageWebReverseNameVO.ANDROID_APP_DOWNLOAD.value)
        )
        image_url = url_adapter.static_url(SeoStaticPathVO.LOGO.value)
        title = SeoTitleTemplateVO.ANDROID_APP.value.format(brand=project.display_name)
        description = SeoDescriptionTemplateVO.ANDROID_APP.value.format(brand=project.display_name)

        return SeoMetadataOverrideDTO(
            title=title,
            description=description,
            canonical_path=reverse(PageWebReverseNameVO.ANDROID_APP.value),
            image_path_or_url=image_url,
            structured_data=(
                self._structured_data_logic.android_application(
                    name=SeoSchemaNameTemplateVO.ANDROID_APP.value.format(
                        brand=project.display_name
                    ),
                    description=description,
                    url=page_url,
                    download_url=download_url,
                    image_url=image_url,
                    version=PageAndroidAppVO.VERSION.value,
                ),
                self._structured_data_logic.breadcrumb(
                    (
                        (
                            SeoBreadcrumbLabelVO.HOME.value,
                            url_adapter.absolute_url(
                                reverse(PageWebReverseNameVO.HOME.value)
                            ),
                        ),
                        (SeoBreadcrumbLabelVO.ANDROID_APP.value, page_url),
                    )
                ),
            ),
        )
