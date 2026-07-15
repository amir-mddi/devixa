from __future__ import annotations

from enum import IntEnum, StrEnum


class ArticleWebAppNameVO(StrEnum):
    NAMESPACE = "articles_web"


class ArticleWebTemplateVO(StrEnum):
    LIST = "web/articles/articles.html"
    DETAIL = "web/articles/article_detail.html"


class ArticleWebPathVO(StrEnum):
    ALL = "articles/"
    BLOG = "blog/"
    NEWS = "news/"
    DETAIL = "articles/<str:slug>/"


class ArticleWebRouteNameVO(StrEnum):
    LIST = "article_list"
    BLOG_LIST = "blog_list"
    NEWS_LIST = "news_list"
    DETAIL = "article_detail"


class ArticleWebReverseNameVO(StrEnum):
    LIST = "articles_web:article_list"
    BLOG_LIST = "articles_web:blog_list"
    NEWS_LIST = "articles_web:news_list"
    DETAIL = "articles_web:article_detail"


class ArticleWebContextKeyVO(StrEnum):
    CATALOG = "catalog"
    ARTICLE = "article"
    DETAIL = "detail"
    RELATED_ARTICLES = "related_articles"
    TYPE_FILTERS = "type_filters"
    EMPTY_MESSAGE = "empty_message"
    RELATED_EMPTY_MESSAGE = "related_empty_message"
    QUERY_SUFFIX = "query_suffix"


class ArticleQueryParamVO(StrEnum):
    TYPE = "type"
    CATEGORY = "category"
    SEARCH = "search"
    PAGE = "page"


class ArticleCategoryFilterVO(StrEnum):
    ALL_VALUE = "all"
    ALL_LABEL = "همه دسته‌ها"


class ArticleTypeFilterVO(StrEnum):
    ALL_VALUE = "all"
    ALL_LABEL = "همه مطالب"
    BLOG_LABEL = "وبلاگ"
    NEWS_LABEL = "اخبار"


class ArticleMessageVO(StrEnum):
    NOT_FOUND = "مطلب مورد نظر پیدا نشد."
    EMPTY_LIST = "هنوز مطلبی با این فیلتر منتشر نشده است."
    RELATED_EMPTY = "هنوز مطلب مرتبط دیگری منتشر نشده است."
    CATEGORY_NOT_FOUND = "دسته‌بندی مطلب پیدا نشد."
    TAGS_NOT_FOUND = "یک یا چند برچسب مطلب پیدا نشد."
    FIELD_NOT_EDITABLE = "فیلد انتخاب‌شده قابل ویرایش نیست."
    TITLE_REQUIRED = "عنوان مطلب الزامی است."
    CONTENT_REQUIRED = "محتوای مطلب الزامی است."
    TYPE_INVALID = "نوع مطلب معتبر نیست."
    STATUS_INVALID = "وضعیت مطلب معتبر نیست."


class ArticleLimitVO(IntEnum):
    PAGE_SIZE = 9
    FEATURED = 3
    RELATED = 3


class ArticleApiTagVO(StrEnum):
    PUBLIC = "Articles"
