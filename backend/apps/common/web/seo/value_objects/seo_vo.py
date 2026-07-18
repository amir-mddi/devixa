from __future__ import annotations

from enum import StrEnum


class SeoContextKeyVO(StrEnum):
    SEO = "seo"


class SeoStaticPathVO(StrEnum):
    FAVICON = "app/assets/images/brand/devixa-favicon.svg"
    LOGO = "app/assets/images/brand/devixa-logo-512.png"
    OPEN_GRAPH_IMAGE = "app/assets/images/brand/devixa-open-graph.png"


class SeoRouteNameVO(StrEnum):
    HOME = "pages_web:home"
    ABOUT_US = "pages_web:about_us"
    CONTACT_US = "pages_web:contact_us"
    CHANNELS = "pages_web:channels"
    ANDROID_APP = "pages_web:android_app"
    COURSE_LIST = "courses_web:course_list"
    COURSE_DETAIL = "courses_web:course_detail"
    ROADMAP_LIST = "courses_web:roadmap_list"
    ROADMAP_DETAIL = "courses_web:roadmap_detail"
    ARTICLE_LIST = "articles_web:article_list"
    BLOG_LIST = "articles_web:blog_list"
    NEWS_LIST = "articles_web:news_list"
    ARTICLE_DETAIL = "articles_web:article_detail"


class SeoTitleTemplateVO(StrEnum):
    HOME = "{brand} | آموزش برنامه‌نویسی پروژه‌محور"
    ABOUT_US = "درباره آکادمی {brand}"
    CONTACT_US = "تماس با {brand} | مشاوره و پشتیبانی"
    CHANNELS = "کانال‌ها و ربات‌های رسمی {brand}"
    ANDROID_APP = "دانلود اپلیکیشن اندروید {brand}"
    COURSE_LIST = "دوره‌های برنامه‌نویسی پروژه‌محور | {brand}"
    COURSE_DETAIL = "{title} | دوره برنامه‌نویسی {brand}"
    ROADMAP_LIST = "نقشه راه‌های یادگیری برنامه‌نویسی | {brand}"
    ROADMAP_DETAIL = "{title} | نقشه راه {brand}"
    ARTICLE_LIST = "مجله، اخبار و وبلاگ برنامه‌نویسی | {brand}"
    BLOG_LIST = "وبلاگ آموزش برنامه‌نویسی | {brand}"
    NEWS_LIST = "اخبار فناوری و برنامه‌نویسی | {brand}"
    ARTICLE_DETAIL = "{title} | {brand}"


class SeoDescriptionTemplateVO(StrEnum):
    HOME = (
        "آموزش برنامه‌نویسی پروژه‌محور با مسیرهای مرحله‌ای، دوره‌های تخصصی، "
        "تمرین عملی و پروژه‌های قابل ارائه در {brand}."
    )
    ABOUT_US = (
        "با داستان، رویکرد آموزشی و مسیر پروژه‌محور آکادمی {brand} برای "
        "یادگیری مهارت‌های کاربردی برنامه‌نویسی آشنا شوید."
    )
    CONTACT_US = (
        "برای مشاوره انتخاب دوره، پشتیبانی مسیر یادگیری و ارتباط با تیم "
        "{brand} از این صفحه استفاده کنید."
    )
    CHANNELS = (
        "لینک کانال‌ها، ربات‌ها و شبکه‌های اجتماعی رسمی {brand} را مشاهده کنید."
    )
    ANDROID_APP = (
        "اپلیکیشن اندروید {brand} را دانلود کنید و به دوره‌ها، مسیرهای یادگیری "
        "و محتوای آموزشی سریع‌تر دسترسی داشته باشید."
    )
    COURSE_LIST = (
        "دوره‌های تخصصی Python، Django، Backend و Frontend را بر اساس سطح "
        "و مسیر شغلی در {brand} پیدا کنید."
    )
    ROADMAP_LIST = (
        "نقشه راه‌های مرحله‌ای برنامه‌نویسی برای Frontend، Backend، Full Stack، "
        "Python و ورود هدفمند به بازار کار."
    )
    ARTICLE_LIST = (
        "جدیدترین مقاله‌های آموزشی، اخبار فناوری و مطالب تخصصی برنامه‌نویسی "
        "را در مجله {brand} بخوانید."
    )
    BLOG_LIST = (
        "مقاله‌ها و آموزش‌های کاربردی برنامه‌نویسی، معماری نرم‌افزار، Python، "
        "Django و توسعه وب در وبلاگ {brand}."
    )
    NEWS_LIST = (
        "تازه‌ترین اخبار فناوری، برنامه‌نویسی و توسعه نرم‌افزار را در بخش "
        "اخبار {brand} دنبال کنید."
    )


class SeoBreadcrumbLabelVO(StrEnum):
    HOME = "خانه"
    COURSES = "دوره‌ها"
    ROADMAPS = "نقشه راه‌ها"
    BLOG = "وبلاگ"
    NEWS = "اخبار"
    ANDROID_APP = "دانلود اپلیکیشن"


class SeoSchemaNameTemplateVO(StrEnum):
    ANDROID_APP = "اپلیکیشن {brand}"


class SeoTemplateVO(StrEnum):
    SITEMAP = "web/seo/sitemap.xml"


class SeoPathVO(StrEnum):
    SITEMAP = "sitemap.xml"
    ROBOTS = "robots.txt"


class SeoRouteVO(StrEnum):
    SITEMAP = "seo_sitemap"
    ROBOTS = "seo_robots"


class SeoNoIndexPathVO(StrEnum):
    ADMIN = "/admin/"
    MANAGEMENT = "/management/"
    API = "/api/"
    PROFILE = "/profile/"
    BASKET = "/basket/"
    CHECKOUT = "/checkout/"
    LOGIN = "/login/"
    REGISTER = "/register/"
    LOGOUT = "/logout/"
    FORGOT_PASSWORD = "/forgot-password/"
    RECOVER_PASSWORD = "/recover-password/"
    OAUTH = "/oauth/"
    METRICS = "/metrics/"
    HEALTH = "/health/"
    SCHEMA = "/schema/"


class SeoRobotsDisallowPathVO(StrEnum):
    ADMIN = "/admin/"
    MANAGEMENT = "/management/"
    API = "/api/"
    METRICS = "/metrics/"
    HEALTH = "/health/"
    SCHEMA = "/schema/"


class SeoSchemaTextVO(StrEnum):
    COURSE_PROVIDER_DESCRIPTION = (
        "آموزش برنامه‌نویسی پروژه‌محور و مهارت‌های کاربردی بازار کار"
    )
    ANDROID_CATEGORY = "EducationalApplication"
    ANDROID_OPERATING_SYSTEM = "Android"
