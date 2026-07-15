from __future__ import annotations

from rest_framework import serializers

from backend.apps.articles.models import Article, ArticleCategory, ArticleTag


class ArticleCategoryPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ["id", "title", "slug"]


class ArticleTagPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleTag
        fields = ["id", "title", "slug"]


class ArticleListSerializer(serializers.ModelSerializer):
    category = ArticleCategoryPublicSerializer(read_only=True)
    tags = ArticleTagPublicSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    type_label = serializers.CharField(source="get_article_type_display", read_only=True)
    reading_time_minutes = serializers.IntegerField(
        source="estimated_reading_minutes",
        read_only=True,
    )
    url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "article_type",
            "type_label",
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "is_featured",
            "published_at",
            "view_count",
            "reading_time_minutes",
            "category",
            "tags",
            "author",
            "url",
        ]

    @staticmethod
    def get_author(obj: Article) -> dict[str, str]:
        full_name = obj.author.get_full_name().strip()
        return {
            "id": str(obj.author_id),
            "username": obj.author.username,
            "display_name": full_name or obj.author.username,
        }


class ArticleDetailSerializer(ArticleListSerializer):
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + [
            "content",
            "source_name",
            "source_url",
            "meta_title",
            "meta_description",
        ]
