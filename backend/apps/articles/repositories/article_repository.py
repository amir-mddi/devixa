from __future__ import annotations

from typing import Protocol, Sequence

from backend.apps.articles.dtos import ArticleCatalogFilterDTO
from backend.apps.articles.dtos.article_management_dtos import (
    ArticleAdminFilterDTO,
    ArticleCreateDTO,
    ArticleUpdateDTO,
)


class ArticleRepository(Protocol):
    def paginate_public_articles(
        self,
        filters: ArticleCatalogFilterDTO,
        *,
        page_size: int,
        excluded_ids: Sequence[object] = (),
    ) -> object: ...

    def list_public_categories(
        self,
        *,
        article_type: str | None = None,
    ) -> Sequence[object]: ...

    def list_featured_articles(
        self,
        *,
        article_type: str | None,
        limit: int,
    ) -> Sequence[object]: ...

    def get_public_article(self, article_id_or_slug: object) -> object: ...

    def list_related_articles(self, article: object, *, limit: int) -> Sequence[object]: ...

    def increment_view_count(self, article_id: object) -> None: ...

    def list_public_queryset(self, filters: dict | None = None) -> object: ...

    def list_admin_articles(self, filters: ArticleAdminFilterDTO) -> object: ...

    def paginate_admin_articles(
        self,
        filters: ArticleAdminFilterDTO,
        *,
        page: object,
        page_size: int,
    ) -> object: ...

    def get_admin_article(self, article_id_or_slug: object) -> object: ...

    def list_admin_categories(self) -> Sequence[object]: ...

    def list_admin_tags(self) -> Sequence[object]: ...

    def list_admin_article_tag_ids(self, article_id: object) -> Sequence[object]: ...

    def create_article(self, *, actor: object, dto: ArticleCreateDTO) -> object: ...

    def update_article(self, *, actor: object, dto: ArticleUpdateDTO) -> object: ...

    def soft_delete_article(self, *, actor: object, article_id: object) -> object: ...
