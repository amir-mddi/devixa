from __future__ import annotations

from django.urls import path

from backend.apps.articles.value_objects import (
    ArticleWebAppNameVO,
    ArticleWebPathVO,
    ArticleWebRouteNameVO,
)
from backend.apps.articles.web.views import (
    ArticleDetailPageView,
    ArticleListPageView,
    BlogListPageView,
    NewsListPageView,
)

app_name = ArticleWebAppNameVO.NAMESPACE.value

urlpatterns = [
    path(
        ArticleWebPathVO.ALL.value,
        ArticleListPageView.as_view(),
        name=ArticleWebRouteNameVO.LIST.value,
    ),
    path(
        ArticleWebPathVO.BLOG.value,
        BlogListPageView.as_view(),
        name=ArticleWebRouteNameVO.BLOG_LIST.value,
    ),
    path(
        ArticleWebPathVO.NEWS.value,
        NewsListPageView.as_view(),
        name=ArticleWebRouteNameVO.NEWS_LIST.value,
    ),
    path(
        ArticleWebPathVO.DETAIL.value,
        ArticleDetailPageView.as_view(),
        name=ArticleWebRouteNameVO.DETAIL.value,
    ),
]
