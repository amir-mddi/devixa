from __future__ import annotations

from dataclasses import replace

from django.core.exceptions import ValidationError
from django.utils.text import slugify

from backend.apps.articles.adapters import ArticlePostgresAdapter
from backend.apps.articles.dtos.article_management_dtos import (
    ArticleAdminFilterDTO,
    ArticleCreateDTO,
    ArticleUpdateDTO,
)
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.articles.repositories import ArticleRepository
from backend.apps.articles.value_objects import ArticleMessageVO


class ArticleManagementLogic:
    EDITABLE_TEXT_FIELDS = {
        "title",
        "excerpt",
        "content",
        "source_name",
        "source_url",
        "meta_title",
        "meta_description",
    }

    def __init__(self, repository: ArticleRepository | None = None):
        self.repository = repository or ArticlePostgresAdapter()

    def list_articles(self, filters: dict | ArticleAdminFilterDTO | None = None):
        dto = (
            filters
            if isinstance(filters, ArticleAdminFilterDTO)
            else ArticleAdminFilterDTO.from_mapping(filters or {})
        )
        return self.repository.list_admin_articles(dto)

    def paginate_articles(
        self,
        filters: dict | ArticleAdminFilterDTO | None = None,
        *,
        page: object = 1,
        page_size: int = 20,
    ):
        dto = (
            filters
            if isinstance(filters, ArticleAdminFilterDTO)
            else ArticleAdminFilterDTO.from_mapping(filters or {})
        )
        return self.repository.paginate_admin_articles(
            dto,
            page=page,
            page_size=page_size,
        )

    def get_article(self, article_id_or_slug: object):
        return self.repository.get_admin_article(article_id_or_slug)

    def list_categories(self):
        return self.repository.list_admin_categories()

    def list_tags(self):
        return self.repository.list_admin_tags()

    def list_article_tag_ids(self, article_id: object):
        return self.repository.list_admin_article_tag_ids(article_id)

    def create_article(self, *, actor, dto: ArticleCreateDTO):
        normalized = self._normalize_create(dto)
        return self.repository.create_article(actor=actor, dto=normalized)

    def update_article(self, *, actor, dto: ArticleUpdateDTO):
        normalized = self._normalize_update(dto)
        return self.repository.update_article(actor=actor, dto=normalized)

    def update_type(self, *, actor, article_id: object, article_type: str):
        article = self.get_article(article_id)
        return self.update_article(
            actor=actor,
            dto=self._dto_from_article(article, article_type=article_type),
        )

    def update_status(self, *, actor, article_id: object, status: str):
        article = self.get_article(article_id)
        return self.update_article(
            actor=actor,
            dto=self._dto_from_article(article, status=status),
        )

    def toggle_featured(self, *, actor, article_id: object):
        article = self.get_article(article_id)
        return self.update_article(
            actor=actor,
            dto=self._dto_from_article(article, is_featured=not article.is_featured),
        )

    def update_text_field(
        self,
        *,
        actor,
        article_id: object,
        field: str,
        value: str,
    ):
        if field not in self.EDITABLE_TEXT_FIELDS:
            raise ValidationError(ArticleMessageVO.FIELD_NOT_EDITABLE.value)
        article = self.get_article(article_id)
        return self.update_article(
            actor=actor,
            dto=self._dto_from_article(article, **{field: value}),
        )

    def delete_article(self, *, actor, article_id: object):
        return self.repository.soft_delete_article(actor=actor, article_id=article_id)

    def _normalize_create(self, dto: ArticleCreateDTO) -> ArticleCreateDTO:
        self._validate_common(dto)
        return replace(
            dto,
            title=dto.title.strip(),
            slug=self._normalize_slug(dto.slug),
            excerpt=dto.excerpt.strip(),
            content=dto.content.strip(),
            source_name=dto.source_name.strip(),
            source_url=dto.source_url.strip(),
            meta_title=dto.meta_title.strip(),
            meta_description=dto.meta_description.strip(),
            tag_ids=tuple(dto.tag_ids),
        )

    def _normalize_update(self, dto: ArticleUpdateDTO) -> ArticleUpdateDTO:
        self._validate_common(dto)
        return replace(
            dto,
            title=dto.title.strip(),
            slug=self._normalize_slug(dto.slug),
            excerpt=dto.excerpt.strip(),
            content=dto.content.strip(),
            source_name=dto.source_name.strip(),
            source_url=dto.source_url.strip(),
            meta_title=dto.meta_title.strip(),
            meta_description=dto.meta_description.strip(),
            tag_ids=tuple(dto.tag_ids),
        )

    @staticmethod
    def _validate_common(dto: ArticleCreateDTO | ArticleUpdateDTO) -> None:
        errors: dict[str, list[str]] = {}
        if not dto.title.strip():
            errors["title"] = [ArticleMessageVO.TITLE_REQUIRED.value]
        if not dto.content.strip():
            errors["content"] = [ArticleMessageVO.CONTENT_REQUIRED.value]
        if dto.article_type not in ArticleTypeEnum.values():
            errors["article_type"] = [ArticleMessageVO.TYPE_INVALID.value]
        if dto.status not in ArticleStatusEnum.values():
            errors["status"] = [ArticleMessageVO.STATUS_INVALID.value]
        if errors:
            raise ValidationError(errors)

    @staticmethod
    def _normalize_slug(value: str) -> str:
        value = (value or "").strip()
        return slugify(value, allow_unicode=True) if value else ""

    def _dto_from_article(self, article, **changes) -> ArticleUpdateDTO:
        values = {
            "article_id": article.id,
            "title": article.title,
            "content": article.content,
            "article_type": article.article_type,
            "status": article.status,
            "slug": article.slug,
            "excerpt": article.excerpt,
            "category_id": article.category_id,
            "tag_ids": tuple(self.repository.list_admin_article_tag_ids(article.id)),
            "cover_image": None,
            "is_featured": article.is_featured,
            "published_at": article.published_at,
            "source_name": article.source_name,
            "source_url": article.source_url,
            "meta_title": article.meta_title,
            "meta_description": article.meta_description,
        }
        values.update(changes)
        return ArticleUpdateDTO(**values)
