from __future__ import annotations

from enum import StrEnum


class SeoRobotsDirectiveEnum(StrEnum):
    INDEX = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
    NOINDEX = "noindex,nofollow,noarchive"
    NOINDEX_FOLLOW = "noindex,follow,noarchive"


class SeoOpenGraphTypeEnum(StrEnum):
    WEBSITE = "website"
    ARTICLE = "article"


class SeoSchemaTypeEnum(StrEnum):
    WEBSITE = "WebSite"
    EDUCATIONAL_ORGANIZATION = "EducationalOrganization"
    WEB_PAGE = "WebPage"
    COURSE = "Course"
    LEARNING_RESOURCE = "LearningResource"
    BLOG_POSTING = "BlogPosting"
    NEWS_ARTICLE = "NewsArticle"
    BREADCRUMB_LIST = "BreadcrumbList"
    SOFTWARE_APPLICATION = "SoftwareApplication"


class SeoChangeFrequencyEnum(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
