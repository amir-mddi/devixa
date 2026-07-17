from __future__ import annotations

from backend.apps.common.web.async_view import AsyncWebViewMixin

from django.http import Http404
from django.views.generic import TemplateView
from rest_framework.exceptions import NotFound

from backend.apps.articles.enums import ArticleTypeEnum
from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.web.seo.mixins import SeoContextMixin
from backend.apps.articles.logic import ArticleLogic
from backend.apps.articles.web.seo_presenters import ArticleSeoPresenter
from backend.apps.articles.value_objects import (
    ArticleMessageVO,
    ArticleQueryParamVO,
    ArticleWebContextKeyVO,
    ArticleWebTemplateVO,
)


class ArticlePageMixin(SeoContextMixin):
    logic_class = ArticleLogic
    forced_type: str | None = None
    seo_presenter_class = ArticleSeoPresenter

    @staticmethod
    def _query_suffix(request) -> str:
        query_params = request.GET.copy()
        query_params.pop(ArticleQueryParamVO.PAGE.value, None)
        return query_params.urlencode()


class ArticleListPageView(AsyncWebViewMixin, ArticlePageMixin, TemplateView):
    template_name = ArticleWebTemplateVO.LIST.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logic = self.logic_class()
        context.update(
            {
                ArticleWebContextKeyVO.CATALOG.value: logic.build_catalog(
                    self.request.GET,
                    forced_type=self.forced_type,
                ),
                ArticleWebContextKeyVO.TYPE_FILTERS.value: logic.type_filters(),
                ArticleWebContextKeyVO.EMPTY_MESSAGE.value: ArticleMessageVO.EMPTY_LIST.value,
                ArticleWebContextKeyVO.QUERY_SUFFIX.value: self._query_suffix(self.request),
            }
        )
        return context


class BlogListPageView(ArticleListPageView):
    forced_type = ArticleTypeEnum.BLOG.value


class NewsListPageView(ArticleListPageView):
    forced_type = ArticleTypeEnum.NEWS.value


class ArticleDetailPageView(AsyncWebViewMixin, ArticlePageMixin, TemplateView):
    template_name = ArticleWebTemplateVO.DETAIL.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            detail = self.logic_class().get_detail(kwargs.get("slug"))
        except NotFound as exc:
            raise Http404(ArticleMessageVO.NOT_FOUND.value) from exc

        context.update(
            {
                ArticleWebContextKeyVO.DETAIL.value: detail,
                ArticleWebContextKeyVO.ARTICLE.value: detail.article,
                ArticleWebContextKeyVO.RELATED_ARTICLES.value: detail.related_articles,
                ArticleWebContextKeyVO.RELATED_EMPTY_MESSAGE.value: (
                    ArticleMessageVO.RELATED_EMPTY.value
                ),
            }
        )
        return context

    def get_seo_override(self, context):
        return self.seo_presenter_class().detail(
            request=self.request,
            project_mapping=get_request_project_context(self.request),
            article=context[ArticleWebContextKeyVO.ARTICLE.value],
        )

