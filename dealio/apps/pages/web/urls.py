from __future__ import annotations

from django.urls import path

from dealio.apps.pages.vo.page_vo import PageWebAppNameVO, PageWebPathVO, PageWebRouteNameVO
from dealio.apps.pages.web.views import AboutUsPageView, ChannelsPageView, ContactUsPageView, HomePageView

app_name = PageWebAppNameVO.NAMESPACE.value

urlpatterns = [
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
