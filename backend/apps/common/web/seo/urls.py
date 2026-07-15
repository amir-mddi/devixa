from __future__ import annotations

from django.urls import path

from backend.apps.common.web.seo.value_objects.seo_vo import SeoPathVO, SeoRouteVO
from backend.apps.common.web.seo.views import RobotsTxtView, SeoSitemapView

urlpatterns = [
    path(SeoPathVO.SITEMAP.value, SeoSitemapView.as_view(), name=SeoRouteVO.SITEMAP.value),
    path(SeoPathVO.ROBOTS.value, RobotsTxtView.as_view(), name=SeoRouteVO.ROBOTS.value),
]
