from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence
from uuid import UUID

from dealio.apps.articles.enums import ArticleStatusEnum, ArticleTypeEnum


@dataclass(frozen=True, slots=True)
class ArticleAdminFilterDTO:
    search: str = ""
    article_type: str = ""
    status: str = ""
    category_id: str = ""

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "ArticleAdminFilterDTO":
        article_type = str(values.get("article_type", "") or "").strip().lower()
        status = str(values.get("status", "") or "").strip().lower()
        if article_type not in {"", *ArticleTypeEnum.values()}:
            article_type = ""
        if status not in {"", *ArticleStatusEnum.values()}:
            status = ""
        category_id = str(values.get("category_id", "") or "").strip()
        if category_id:
            try:
                UUID(category_id)
            except (TypeError, ValueError):
                category_id = ""
        return cls(
            search=str(values.get("search", "") or "").strip()[:200],
            article_type=article_type,
            status=status,
            category_id=category_id,
        )


@dataclass(frozen=True, slots=True)
class ArticleCreateDTO:
    title: str
    content: str
    article_type: str
    status: str
    slug: str = ""
    excerpt: str = ""
    category_id: object | None = None
    tag_ids: Sequence[object] = field(default_factory=tuple)
    cover_image: object | None = None
    is_featured: bool = False
    published_at: object | None = None
    source_name: str = ""
    source_url: str = ""
    meta_title: str = ""
    meta_description: str = ""


@dataclass(frozen=True, slots=True)
class ArticleUpdateDTO:
    article_id: object
    title: str
    content: str
    article_type: str
    status: str
    slug: str = ""
    excerpt: str = ""
    category_id: object | None = None
    tag_ids: Sequence[object] = field(default_factory=tuple)
    cover_image: object | None = None
    is_featured: bool = False
    published_at: object | None = None
    source_name: str = ""
    source_url: str = ""
    meta_title: str = ""
    meta_description: str = ""
