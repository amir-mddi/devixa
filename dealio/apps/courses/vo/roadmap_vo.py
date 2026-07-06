from __future__ import annotations

from enum import IntEnum, StrEnum


class CourseWebAppNameVO(StrEnum):
    NAMESPACE = "courses_web"


class CourseWebTemplateVO(StrEnum):
    COURSE_LIST = "web/courses/courses.html"
    COURSE_DETAIL = "web/courses/course_detail.html"
    ROADMAP_LIST = "web/courses/roadmaps.html"
    ROADMAP_DETAIL = "web/courses/roadmap_detail.html"


class CourseWebPathVO(StrEnum):
    COURSES = "courses/"
    COURSE_DETAIL = "courses/<slug:slug>/"
    ROADMAPS = "roadmaps/"
    ROADMAP_DETAIL = "roadmaps/<slug:slug>/"


class CourseWebRouteNameVO(StrEnum):
    COURSE_LIST = "course_list"
    COURSE_DETAIL = "course_detail"
    ROADMAP_LIST = "roadmap_list"
    ROADMAP_DETAIL = "roadmap_detail"


class CourseWebReverseNameVO(StrEnum):
    COURSE_LIST = "courses_web:course_list"
    COURSE_DETAIL = "courses_web:course_detail"
    ROADMAP_LIST = "courses_web:roadmap_list"
    ROADMAP_DETAIL = "courses_web:roadmap_detail"


class CourseWebFilterKeyVO(StrEnum):
    VALUE = "value"
    LABEL = "label"


class CourseWebContextKeyVO(StrEnum):
    CATALOG = "catalog"
    FEATURED_COURSES = "featured_courses"
    FEATURED_ROADMAPS = "featured_roadmaps"
    COURSE_DETAIL = "course_detail"
    COURSE = "course"
    RELATED_COURSES = "related_courses"
    REVIEWS = "reviews"
    LEVEL_FILTERS = "level_filters"
    REVIEWS_EMPTY_MESSAGE = "reviews_empty_message"
    CATEGORY_FILTERS = "category_filters"
    EMPTY_MESSAGE = "empty_message"
    DETAIL = "detail"
    ROADMAP = "roadmap"
    RELATED_COURSES_EMPTY_MESSAGE = "related_courses_empty_message"


class CourseWebUrlKwargVO(StrEnum):
    SLUG = "slug"


class CourseRoadmapQueryParamVO(StrEnum):
    CATEGORY = "category"
    SEARCH = "search"


class CourseQueryParamVO(StrEnum):
    CATEGORY = "category"
    LEVEL = "level"
    SEARCH = "search"
    FEATURED = "featured"


class CourseRoadmapCategoryVO(StrEnum):
    ALL = "all"
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    AI = "ai"
    FREELANCER = "freelancer"


class CourseRoadmapCategoryLabelVO(StrEnum):
    ALL = "همه نقشه‌ها"
    FRONTEND = "فرانت‌اند"
    BACKEND = "بک‌اند"
    FULLSTACK = "فول‌استک"
    AI = "هوش مصنوعی"
    FREELANCER = "فریلنسری"


class CourseRoadmapPageTitleVO(StrEnum):
    LIST = "نقشه راه دوره‌ها"
    DETAIL = "نقشه راه یادگیری"


class CourseRoadmapMessageVO(StrEnum):
    NOT_FOUND = "نقشه راه مورد نظر پیدا نشد."
    EMPTY_LIST = "هیچ نقشه راهی با این فیلتر پیدا نشد."
    RELATED_COURSES_EMPTY = "هنوز دوره مرتبطی برای این مسیر منتشر نشده است."


class CourseWebMessageVO(StrEnum):
    EMPTY_LIST = "هنوز دوره‌ای با این فیلتر منتشر نشده است."
    EMPTY_FEATURED_LIST = "هنوز دوره ویژه‌ای منتشر نشده است."
    RELATED_COURSES_EMPTY = "هنوز دوره مرتبط دیگری منتشر نشده است."
    REVIEWS_EMPTY = "هنوز نظری برای این دوره ثبت نشده است."
    COURSE_NOT_FOUND = "دوره مورد نظر پیدا نشد."


class CourseWebCategoryFilterVO(StrEnum):
    ALL_VALUE = "all"
    ALL_LABEL = "همه دوره‌ها"


class CourseWebLevelFilterVO(StrEnum):
    ALL_VALUE = "all"
    ALL_LABEL = "همه سطح‌ها"


class CourseWebLevelLabelVO(StrEnum):
    BEGINNER = "مبتدی"
    INTERMEDIATE = "متوسط"
    ADVANCED = "پیشرفته"
    ALL_LEVELS = "همه سطوح"
    DEFAULT_INSTRUCTOR = "مدرس"


class CourseWebPriceLabelVO(StrEnum):
    FREE = "رایگان"
    PAID = "{amount} {currency}"


class CourseWebCurrencyLabelVO(StrEnum):
    IRR = "تومان"


class CourseWebTimeLabelVO(IntEnum):
    MINUTES_IN_HOUR = 60


class CourseWebTimeTextVO(StrEnum):
    NO_DURATION = "زمان آزاد"
    HOUR_AND_MINUTE = "{hours} ساعت و {minutes} دقیقه"
    HOUR = "{hours} ساعت"
    MINUTE = "{minutes} دقیقه"


class CourseWebLimitVO(IntEnum):
    HOME_FEATURED_COURSES = 6
    HOME_FEATURED_ROADMAPS = 4
    COURSE_RELATED_COURSES = 3
    COURSE_DETAIL_REVIEWS = 6


class CourseRoadmapLimitVO(IntEnum):
    RELATED_COURSES_LIMIT = 3
