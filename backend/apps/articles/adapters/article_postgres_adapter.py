from __future__ import annotations

from typing import Sequence
from uuid import UUID

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.utils.timezone import now
from rest_framework.exceptions import NotFound

from backend.apps.articles.dtos import ArticleCatalogFilterDTO
from backend.apps.articles.dtos.article_management_dtos import (
    ArticleAdminFilterDTO,
    ArticleCreateDTO,
    ArticleUpdateDTO,
)
from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.articles.models import Article, ArticleCategory, ArticleTag
from backend.apps.articles.value_objects.article_vo import (
    ArticleCategoryFilterVO,
    ArticleMessageVO,
    ArticleQueryParamVO,
)
from backend.apps.common.helpers.metaclasses.singleton import Singleton


class ArticlePostgresAdapter(metaclass=Singleton):
    @staticmethod
    def _public_articles():
        return (
            Article.objects.select_related("category", "author")
            .prefetch_related(
                Prefetch(
                    "tags",
                    queryset=ArticleTag.objects.filter(
                        is_active=True,
                        is_deleted=False,
                    ).order_by("title"),
                )
            )
            .filter(
                status=ArticleStatusEnum.PUBLISHED.value,
                is_active=True,
                is_deleted=False,
                published_at__isnull=False,
                published_at__lte=now(),
            )
        )

    @staticmethod
    def _normalize_public_type(value: str | None) -> str | None:
        normalized = str(value or "").strip().lower()
        return normalized if normalized in ArticleTypeEnum.values() else None

    def _apply_public_filters(self, queryset, filters: ArticleCatalogFilterDTO):
        article_type = self._normalize_public_type(filters.article_type)
        if article_type:
            queryset = queryset.filter(article_type=article_type)

        if filters.category and filters.category != ArticleCategoryFilterVO.ALL_VALUE.value:
            queryset = queryset.filter(category__slug=filters.category)

        if filters.search:
            search = filters.search
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(excerpt__icontains=search)
                | Q(content__icontains=search)
                | Q(category__title__icontains=search)
                | Q(tags__title__icontains=search)
            ).distinct()

        return queryset.order_by("-published_at", "-created_at")

    def paginate_public_articles(
        self,
        filters: ArticleCatalogFilterDTO,
        *,
        page_size: int,
        excluded_ids: Sequence[object] = (),
    ):
        queryset = self._apply_public_filters(self._public_articles(), filters)
        if excluded_ids:
            queryset = queryset.exclude(id__in=tuple(excluded_ids))
        return Paginator(queryset, page_size).get_page(filters.page)

    def list_public_categories(self, *, article_type: str | None = None):
        article_filter = Q(
            articles__status=ArticleStatusEnum.PUBLISHED.value,
            articles__is_active=True,
            articles__is_deleted=False,
            articles__published_at__isnull=False,
            articles__published_at__lte=now(),
        )
        normalized_type = self._normalize_public_type(article_type)
        if normalized_type:
            article_filter &= Q(articles__article_type=normalized_type)

        return tuple(
            ArticleCategory.objects.filter(is_active=True, is_deleted=False)
            .annotate(public_articles_count=Count("articles", filter=article_filter, distinct=True))
            .filter(public_articles_count__gt=0)
            .order_by("position", "title")
        )

    def list_featured_articles(
        self,
        *,
        article_type: str | None,
        limit: int,
    ):
        queryset = self._public_articles().filter(is_featured=True)
        normalized_type = self._normalize_public_type(article_type)
        if normalized_type:
            queryset = queryset.filter(article_type=normalized_type)
        return tuple(queryset.order_by("-published_at")[:limit])

    def get_public_article(self, article_id_or_slug: object):
        lookup_value = str(article_id_or_slug or "").strip()
        try:
            UUID(lookup_value)
            lookup = Q(id=lookup_value)
        except (TypeError, ValueError):
            lookup = Q(slug=lookup_value)

        article = self._public_articles().filter(lookup).first()
        if article is None:
            raise NotFound(ArticleMessageVO.NOT_FOUND.value)
        return article

    def list_related_articles(self, article: Article, *, limit: int):
        queryset = self._public_articles().exclude(id=article.id)
        if article.category_id:
            queryset = queryset.filter(category_id=article.category_id)
        else:
            queryset = queryset.filter(article_type=article.article_type)
        return tuple(queryset.order_by("-published_at")[:limit])

    @staticmethod
    def increment_view_count(article_id: object) -> None:
        Article.objects.filter(id=article_id).update(view_count=F("view_count") + 1)


    async def get_public_article_async(self, article_id_or_slug: object):
        lookup_value = str(article_id_or_slug or "").strip()
        try:
            UUID(lookup_value)
            lookup = Q(id=lookup_value)
        except (TypeError, ValueError):
            lookup = Q(slug=lookup_value)

        article = await self._public_articles().filter(lookup).afirst()
        if article is None:
            raise NotFound(ArticleMessageVO.NOT_FOUND.value)
        return article

    async def list_related_articles_async(self, article: Article, *, limit: int):
        queryset = self._public_articles().exclude(id=article.id)
        if article.category_id:
            queryset = queryset.filter(category_id=article.category_id)
        else:
            queryset = queryset.filter(article_type=article.article_type)
        return tuple([item async for item in queryset.order_by("-published_at")[:limit]])

    @staticmethod
    async def increment_view_count_async(article_id: object) -> None:
        await Article.objects.filter(id=article_id).aupdate(
            view_count=F("view_count") + 1
        )

    def list_public_queryset(self, filters: dict | None = None):
        filters = filters or {}
        dto = ArticleCatalogFilterDTO.from_mapping(
            {
                ArticleQueryParamVO.TYPE.value: filters.get(ArticleQueryParamVO.TYPE.value),
                ArticleQueryParamVO.CATEGORY.value: filters.get(ArticleQueryParamVO.CATEGORY.value),
                ArticleQueryParamVO.SEARCH.value: filters.get(ArticleQueryParamVO.SEARCH.value),
            }
        )
        return self._apply_public_filters(self._public_articles(), dto)

    @staticmethod
    def _admin_articles():
        return (
            Article.objects.select_related("category", "author")
            .prefetch_related("tags")
            .filter(is_deleted=False)
        )

    def list_admin_articles(self, filters: ArticleAdminFilterDTO):
        queryset = self._admin_articles()
        if filters.article_type:
            queryset = queryset.filter(article_type=filters.article_type)
        if filters.status:
            queryset = queryset.filter(status=filters.status)
        if filters.category_id:
            queryset = queryset.filter(category_id=filters.category_id)
        if filters.search:
            search = filters.search
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(slug__icontains=search)
                | Q(excerpt__icontains=search)
                | Q(content__icontains=search)
                | Q(author__username__icontains=search)
                | Q(author__email__icontains=search)
                | Q(category__title__icontains=search)
                | Q(tags__title__icontains=search)
            ).distinct()
        return queryset.order_by("-published_at", "-created_at")

    def paginate_admin_articles(
        self,
        filters: ArticleAdminFilterDTO,
        *,
        page: object,
        page_size: int,
    ):
        return Paginator(self.list_admin_articles(filters), page_size).get_page(page)

    def get_admin_article(self, article_id_or_slug: object):
        lookup_value = str(article_id_or_slug or "").strip()
        try:
            UUID(lookup_value)
            lookup = Q(id=lookup_value)
        except (TypeError, ValueError):
            lookup = Q(slug=lookup_value)
        article = self._admin_articles().filter(lookup).first()
        if article is None:
            raise NotFound(ArticleMessageVO.NOT_FOUND.value)
        return article

    @staticmethod
    def list_admin_categories():
        return tuple(
            ArticleCategory.objects.filter(is_deleted=False)
            .order_by("position", "title")
        )

    @staticmethod
    def list_admin_tags():
        return tuple(ArticleTag.objects.filter(is_deleted=False).order_by("title"))

    @staticmethod
    def list_admin_article_tag_ids(article_id: object):
        return tuple(
            ArticleTag.objects.filter(
                articles__id=article_id,
                is_deleted=False,
            ).values_list("id", flat=True)
        )

    @staticmethod
    def _category(category_id):
        if not category_id:
            return None
        category = ArticleCategory.objects.filter(id=category_id, is_deleted=False).first()
        if category is None:
            raise NotFound(ArticleMessageVO.CATEGORY_NOT_FOUND.value)
        return category

    @staticmethod
    def _tags(tag_ids):
        normalized_ids = tuple(tag_ids or ())
        if not normalized_ids:
            return ()
        tags = tuple(
            ArticleTag.objects.filter(id__in=normalized_ids, is_deleted=False)
            .order_by("title")
        )
        if len(tags) != len(set(normalized_ids)):
            raise NotFound(ArticleMessageVO.TAGS_NOT_FOUND.value)
        return tags

    @transaction.atomic
    def create_article(self, *, actor, dto: ArticleCreateDTO):
        article = Article(
            category=self._category(dto.category_id),
            author=actor,
            article_type=dto.article_type,
            status=dto.status,
            title=dto.title,
            slug=dto.slug,
            excerpt=dto.excerpt,
            content=dto.content,
            cover_image=dto.cover_image,
            is_featured=dto.is_featured,
            published_at=dto.published_at,
            source_name=dto.source_name,
            source_url=dto.source_url,
            meta_title=dto.meta_title,
            meta_description=dto.meta_description,
            user_created_object=actor,
            user_updated_object=actor,
        )
        article.full_clean(exclude=("cover_image",))
        article.save()
        article.tags.set(self._tags(dto.tag_ids))
        return self.get_admin_article(article.id)

    @transaction.atomic
    def update_article(self, *, actor, dto: ArticleUpdateDTO):
        article = self.get_admin_article(dto.article_id)
        article.category = self._category(dto.category_id)
        article.article_type = dto.article_type
        article.status = dto.status
        article.title = dto.title
        article.slug = dto.slug
        article.excerpt = dto.excerpt
        article.content = dto.content
        if dto.cover_image is not None:
            article.cover_image = dto.cover_image
        article.is_featured = dto.is_featured
        article.published_at = dto.published_at
        article.source_name = dto.source_name
        article.source_url = dto.source_url
        article.meta_title = dto.meta_title
        article.meta_description = dto.meta_description
        article.user_updated_object = actor
        article.full_clean(exclude=("cover_image",))
        article.save()
        article.tags.set(self._tags(dto.tag_ids))
        return self.get_admin_article(article.id)

    @transaction.atomic
    def soft_delete_article(self, *, actor, article_id: object):
        article = self.get_admin_article(article_id)
        article.user_updated_object = actor
        article.save(update_fields=["user_updated_object", "updated_at"])
        article.delete()
        return article

