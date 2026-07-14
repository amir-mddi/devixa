from django.urls import path

from dealio.apps.articles.views import (
    PublicArticleDetailAPIView,
    PublicArticleListAPIView,
)

app_name = "articles_api"

urlpatterns = [
    path("", PublicArticleListAPIView.as_view(), name="article-list"),
    path(
        "<str:article_id_or_slug>/",
        PublicArticleDetailAPIView.as_view(),
        name="article-detail",
    ),
]
