from django.contrib import admin

from backend.apps.articles.models import Article, ArticleCategory, ArticleTag


class AuditAdminMixin:
    def save_model(self, request, obj, form, change):
        if not obj.user_created_object_id:
            obj.user_created_object = request.user
        obj.user_updated_object = request.user
        super().save_model(request, obj, form, change)


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("title", "slug", "position", "is_active")
    list_filter = ("is_active", "is_deleted")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("position", "title")


@admin.register(ArticleTag)
class ArticleTagAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("title", "slug", "is_active")
    list_filter = ("is_active", "is_deleted")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Article)
class ArticleAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "article_type",
        "status",
        "category",
        "author",
        "is_featured",
        "published_at",
        "view_count",
        "is_active",
    )
    list_filter = (
        "article_type",
        "status",
        "is_featured",
        "category",
        "published_at",
        "is_active",
        "is_deleted",
    )
    search_fields = (
        "title",
        "slug",
        "excerpt",
        "content",
        "author__username",
        "author__email",
        "category__title",
        "tags__title",
    )
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category",)
    raw_id_fields = ("author",)
    filter_horizontal = ("tags",)
    readonly_fields = ("view_count", "created_at", "updated_at")
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")
    fieldsets = (
        (
            "محتوا",
            {
                "fields": (
                    "article_type",
                    "title",
                    "slug",
                    "excerpt",
                    "content",
                    "cover_image",
                )
            },
        ),
        (
            "دسته‌بندی و نویسنده",
            {"fields": ("category", "tags", "author")},
        ),
        (
            "انتشار",
            {
                "fields": (
                    "status",
                    "is_featured",
                    "published_at",
                    "is_active",
                    "is_deleted",
                )
            },
        ),
        (
            "منبع خبر",
            {
                "fields": ("source_name", "source_url"),
                "classes": ("collapse",),
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "آمار و تاریخ‌ها",
            {
                "fields": ("view_count", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
