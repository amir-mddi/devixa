from __future__ import annotations

from django.http import Http404
from django.views.generic import TemplateView
from rest_framework.exceptions import NotFound

from backend.apps.articles.enums import ArticleTypeEnum
from backend.apps.articles.logic import ArticleLogic
from backend.apps.articles.value_objects import (
    ArticleMessageVO,
    ArticleQueryParamVO,
    ArticleWebContextKeyVO,
    ArticleWebTemplateVO,
)


class ArticlePageMixin:
    logic_class = ArticleLogic
    forced_type: str | None = None

    @staticmethod
    def _query_suffix(request) -> str:
        query_params = request.GET.copy()
        query_params.pop(ArticleQueryParamVO.PAGE.value, None)
        return query_params.urlencode()


class ArticleListPageView(ArticlePageMixin, TemplateView):
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


class ArticleDetailPageView(ArticlePageMixin, TemplateView):
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
                ArticleWebContextKeyVO.RELATED_EMPTY_MESSAGE.value: ArticleMessageVO.RELATED_EMPTY.value,
            }
        )
        return context
