from __future__ import annotations

from django.urls import path

from backend.apps.pages.vo.page_vo import PageWebAppNameVO, PageWebPathVO, PageWebRouteNameVO
from backend.apps.pages.web.views import (
    AboutUsPageView,
    AndroidAppDownloadView,
    AndroidAppPageView,
    ChannelsPageView,
    ContactUsPageView,
    HomePageView,
)

app_name = PageWebAppNameVO.NAMESPACE.value

urlpatterns = [
    path(
        PageWebPathVO.ANDROID_APP.value,
        AndroidAppPageView.as_view(),
        name=PageWebRouteNameVO.ANDROID_APP.value,
    ),
    path(
        PageWebPathVO.ANDROID_APP_DOWNLOAD.value,
        AndroidAppDownloadView.as_view(),
        name=PageWebRouteNameVO.ANDROID_APP_DOWNLOAD.value,
    ),
    path(
        PageWebPathVO.HOME.value,
        HomePageView.as_view(),
        name=PageWebRouteNameVO.HOME.value,
    ),
    path(
        PageWebPathVO.ABOUT_US.value,
        AboutUsPageView.as_view(),
        name=PageWebRouteNameVO.ABOUT_US.value,
    ),
    path(
        PageWebPathVO.CONTACT_US.value,
        ContactUsPageView.as_view(),
        name=PageWebRouteNameVO.CONTACT_US.value,
    ),
    path(
        PageWebPathVO.CHANNELS.value,
        ChannelsPageView.as_view(),
        name=PageWebRouteNameVO.CHANNELS.value,
    ),
]
