from __future__ import annotations

from enum import StrEnum


class PublicPageCachePolicyVO(StrEnum):
    CACHE_CONTROL = "private, max-age=0, must-revalidate"


class PublicPagePathVO(StrEnum):
    HOME = "/"
    COURSES = "/courses/"
    ROADMAPS = "/roadmaps/"
    ARTICLES = "/articles/"
    BLOG = "/blog/"
    NEWS = "/news/"
    ANDROID = "/android/"
    ABOUT = "/about-us/"
    CONTACT = "/contact-us/"
    CHANNELS = "/channels/"
