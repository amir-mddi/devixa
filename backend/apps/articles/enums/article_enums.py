from backend.apps.core_models.enum.base import BaseEnum


class ArticleTypeEnum(BaseEnum):
    BLOG = "blog"
    NEWS = "news"

    @classmethod
    def choices(cls):
        return [
            (cls.BLOG.value, "وبلاگ"),
            (cls.NEWS.value, "اخبار"),
        ]


class ArticleStatusEnum(BaseEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @classmethod
    def choices(cls):
        return [
            (cls.DRAFT.value, "پیش‌نویس"),
            (cls.PUBLISHED.value, "منتشرشده"),
            (cls.ARCHIVED.value, "بایگانی‌شده"),
        ]
