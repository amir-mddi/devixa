from __future__ import annotations

import math
import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now

from backend.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum
from backend.apps.core_models.entities.base.base import BaseModel


class ArticleCategory(BaseModel):
    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True, allow_unicode=True, blank=True)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "title"]
        verbose_name = "Article category"
        verbose_name_plural = "Article categories"
        indexes = [
            models.Index(
                fields=["is_active", "is_deleted", "position"],
                name="article_category_public_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            normalized = slugify(self.title, allow_unicode=True) or "category"
            self.slug = f"{normalized}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class ArticleTag(BaseModel):
    title = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, blank=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Article tag"
        verbose_name_plural = "Article tags"

    def save(self, *args, **kwargs):
        if not self.slug:
            normalized = slugify(self.title, allow_unicode=True) or "tag"
            self.slug = f"{normalized}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Article(BaseModel):
    category = models.ForeignKey(
        ArticleCategory,
        related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        ArticleTag,
        related_name="articles",
        blank=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="authored_articles",
        on_delete=models.PROTECT,
    )
    article_type = models.CharField(
        max_length=20,
        choices=ArticleTypeEnum.choices(),
        default=ArticleTypeEnum.BLOG.value,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ArticleStatusEnum.choices(),
        default=ArticleStatusEnum.DRAFT.value,
        db_index=True,
    )
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True, blank=True)
    excerpt = models.CharField(max_length=420, blank=True, default="")
    content = models.TextField()
    cover_image = models.ImageField(
        upload_to="articles/covers/%Y/%m/",
        null=True,
        blank=True,
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    view_count = models.PositiveBigIntegerField(default=0, editable=False)

    source_name = models.CharField(max_length=150, blank=True, default="")
    source_url = models.URLField(blank=True, default="")

    meta_title = models.CharField(max_length=220, blank=True, default="")
    meta_description = models.CharField(max_length=320, blank=True, default="")

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(
                fields=[
                    "status",
                    "article_type",
                    "is_active",
                    "is_deleted",
                    "published_at",
                ],
                name="article_public_list_idx",
            ),
            models.Index(
                fields=["is_featured", "status", "published_at"],
                name="article_featured_idx",
            ),
            models.Index(fields=["slug"], name="article_slug_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(view_count__gte=0),
                name="article_view_count_gte_zero",
            ),
        ]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    @property
    def is_published(self) -> bool:
        return bool(
            self.status == ArticleStatusEnum.PUBLISHED.value
            and self.is_active
            and not self.is_deleted
            and self.published_at
            and self.published_at <= now()
        )

    @property
    def estimated_reading_minutes(self) -> int:
        plain_text = re.sub(r"<[^>]+>", " ", self.content or "")
        word_count = len(plain_text.split())
        return max(1, math.ceil(word_count / 200))

    @property
    def seo_title(self) -> str:
        return self.meta_title or self.title

    @property
    def seo_description(self) -> str:
        return self.meta_description or self.excerpt or self.title

    def get_absolute_url(self) -> str:
        return reverse("articles_web:article_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            normalized = slugify(self.title, allow_unicode=True) or "article"
            self.slug = f"{normalized}-{str(self.id)[:12]}"
        if self.status == ArticleStatusEnum.PUBLISHED.value and not self.published_at:
            self.published_at = now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
