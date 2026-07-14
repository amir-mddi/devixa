from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from dealio.apps.articles.enums import ArticleTypeEnum
from dealio.apps.articles.value_objects.article_vo import ArticleQueryParamVO


@dataclass(frozen=True)
class ArticleCatalogFilterDTO:
    article_type: str = "all"
    category: str = "all"
    search: str = ""
    page: int = 1

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, object],
        *,
        forced_type: str | None = None,
    ) -> "ArticleCatalogFilterDTO":
        raw_page = str(values.get(ArticleQueryParamVO.PAGE.value, "1") or "1")
        try:
            page = max(1, int(raw_page))
        except (TypeError, ValueError):
            page = 1

        article_type = (
            forced_type
            or str(values.get(ArticleQueryParamVO.TYPE.value, "all") or "all")
        ).strip().lower()
        if article_type not in {"all", *ArticleTypeEnum.values()}:
            article_type = "all"

        return cls(
            article_type=article_type,
            category=str(
                values.get(ArticleQueryParamVO.CATEGORY.value, "all") or "all"
            ).strip().lower(),
            search=str(values.get(ArticleQueryParamVO.SEARCH.value, "") or "").strip()[:200],
            page=page,
        )


@dataclass(frozen=True)
class ArticleCategoryFilterDTO:
    value: str
    label: str
    count: int = 0


@dataclass(frozen=True)
class ArticleCatalogDTO:
    page: object
    categories: Sequence[ArticleCategoryFilterDTO]
    featured_articles: Sequence[object] = field(default_factory=tuple)
    selected_type: str = "all"
    selected_category: str = "all"
    search: str = ""

    @property
    def total_count(self) -> int:
        return int(self.page.paginator.count) + len(self.featured_articles)


@dataclass(frozen=True)
class ArticleDetailDTO:
    article: object
    related_articles: Sequence[object] = field(default_factory=tuple)
