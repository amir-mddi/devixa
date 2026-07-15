from __future__ import annotations

from backend.apps.articles.adapters import ArticlePostgresAdapter
from backend.apps.articles.dtos import (
    ArticleCatalogDTO,
    ArticleCatalogFilterDTO,
    ArticleCategoryFilterDTO,
    ArticleDetailDTO,
)
from backend.apps.articles.entities import ArticleTypeFilterEntity
from backend.apps.articles.enums import ArticleTypeEnum
from backend.apps.articles.repositories import ArticleRepository
from backend.apps.articles.value_objects import (
    ArticleCategoryFilterVO,
    ArticleLimitVO,
    ArticleTypeFilterVO,
    ArticleWebReverseNameVO,
)


class ArticleLogic:
    def __init__(self, repository: ArticleRepository | None = None):
        self.repository = repository or ArticlePostgresAdapter()

    @staticmethod
    def type_filters() -> tuple[ArticleTypeFilterEntity, ...]:
        return (
            ArticleTypeFilterEntity(
                value=ArticleTypeFilterVO.ALL_VALUE.value,
                label=ArticleTypeFilterVO.ALL_LABEL.value,
                icon="fa-layer-group",
                reverse_name=ArticleWebReverseNameVO.LIST.value,
            ),
            ArticleTypeFilterEntity(
                value=ArticleTypeEnum.BLOG.value,
                label=ArticleTypeFilterVO.BLOG_LABEL.value,
                icon="fa-pen-nib",
                reverse_name=ArticleWebReverseNameVO.BLOG_LIST.value,
            ),
            ArticleTypeFilterEntity(
                value=ArticleTypeEnum.NEWS.value,
                label=ArticleTypeFilterVO.NEWS_LABEL.value,
                icon="fa-newspaper",
                reverse_name=ArticleWebReverseNameVO.NEWS_LIST.value,
            ),
        )

    @staticmethod
    def _should_show_featured(filters: ArticleCatalogFilterDTO) -> bool:
        return bool(
            filters.page == 1
            and filters.category == ArticleCategoryFilterVO.ALL_VALUE.value
            and not filters.search
        )

    def build_catalog(
        self,
        query_params,
        *,
        forced_type: str | None = None,
    ) -> ArticleCatalogDTO:
        filters = ArticleCatalogFilterDTO.from_mapping(
            query_params,
            forced_type=forced_type,
        )

        featured_articles = ()
        if self._should_show_featured(filters):
            featured_articles = self.repository.list_featured_articles(
                article_type=filters.article_type,
                limit=ArticleLimitVO.FEATURED.value,
            )

        page = self.repository.paginate_public_articles(
            filters,
            page_size=ArticleLimitVO.PAGE_SIZE.value,
            excluded_ids=tuple(article.id for article in featured_articles),
        )
        if featured_articles and page.paginator.count == 0:
            featured_articles = ()
            page = self.repository.paginate_public_articles(
                filters,
                page_size=ArticleLimitVO.PAGE_SIZE.value,
            )

        categories = (
            ArticleCategoryFilterDTO(
                value=ArticleCategoryFilterVO.ALL_VALUE.value,
                label=ArticleCategoryFilterVO.ALL_LABEL.value,
                count=page.paginator.count + len(featured_articles),
            ),
            *tuple(
                ArticleCategoryFilterDTO(
                    value=category.slug,
                    label=category.title,
                    count=int(category.public_articles_count),
                )
                for category in self.repository.list_public_categories(
                    article_type=filters.article_type
                )
            ),
        )

        return ArticleCatalogDTO(
            page=page,
            categories=categories,
            featured_articles=featured_articles,
            selected_type=filters.article_type,
            selected_category=filters.category,
            search=filters.search,
        )

    def paginate_public_for_bot(
        self,
        *,
        article_type: str = "all",
        page: int = 1,
        page_size: int = 5,
    ):
        filters = ArticleCatalogFilterDTO(
            article_type=article_type,
            category=ArticleCategoryFilterVO.ALL_VALUE.value,
            search="",
            page=max(1, page),
        )
        return self.repository.paginate_public_articles(
            filters,
            page_size=max(1, min(page_size, 10)),
        )

    def get_detail(self, article_id_or_slug: object) -> ArticleDetailDTO:
        article = self.repository.get_public_article(article_id_or_slug)
        related = self.repository.list_related_articles(
            article,
            limit=ArticleLimitVO.RELATED.value,
        )
        self.repository.increment_view_count(article.id)
        article.view_count += 1
        return ArticleDetailDTO(article=article, related_articles=related)

    def list_public_articles(self, filters: dict | None = None):
        return self.repository.list_public_queryset(filters=filters)

    def get_public_article(self, article_id_or_slug: object):
        return self.repository.get_public_article(article_id_or_slug)
