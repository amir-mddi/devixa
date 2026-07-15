from __future__ import annotations

from backend.apps.articles.adapters.article_postgres_adapter import ArticlePostgresAdapter
from backend.apps.courses.entities.roadmap_entities import CourseRoadmapCatalogEntity
from backend.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter


class DjangoSeoContentRepository:
    """Read-only SEO inventory repository. All database access stays in repositories."""

    def list_public_courses(self):
        return (
            CoursePostgresAdapter.published_courses_queryset()
            .only("slug", "updated_at", "published_at")
            .order_by("-updated_at")
        )

    def list_public_articles(self):
        return (
            ArticlePostgresAdapter()
            .list_public_queryset()
            .only("slug", "updated_at", "published_at")
            .order_by("-updated_at")
        )

    def list_learning_roadmaps(self):
        return CourseRoadmapCatalogEntity.all()
