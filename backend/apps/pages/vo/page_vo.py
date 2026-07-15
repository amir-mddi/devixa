from __future__ import annotations

from enum import IntEnum, StrEnum


class PageWebAppNameVO(StrEnum):
    NAMESPACE = "pages_web"


class PageWebTemplateVO(StrEnum):
    HOME = "web/pages/home.html"
    ABOUT_US = "web/pages/about_us.html"
    CONTACT_US = "web/pages/contact_us.html"
    CHANNELS = "web/pages/channels.html"


class PageWebPathVO(StrEnum):
    HOME = ""
    ABOUT_US = "about-us/"
    CONTACT_US = "contact-us/"
    CHANNELS = "channels/"
    ANDROID_APP_DOWNLOAD = "downloads/android/"


class PageWebRouteNameVO(StrEnum):
    HOME = "home"
    ABOUT_US = "about_us"
    CONTACT_US = "contact_us"
    CHANNELS = "channels"
    ANDROID_APP_DOWNLOAD = "download_android_app"


class PageWebReverseNameVO(StrEnum):
    HOME = "pages_web:home"
    ABOUT_US = "pages_web:about_us"
    CONTACT_US = "pages_web:contact_us"
    CHANNELS = "pages_web:channels"
    ANDROID_APP_DOWNLOAD = "pages_web:download_android_app"


class PageAndroidAppVO(StrEnum):
    VERSION = "1.0.0"
    APK_FILENAME = "Devixa-v1.0.0.apk"
    APK_STATIC_PATH = "app/downloads/Devixa-v1.0.0.apk"
    CHECKSUM_STATIC_PATH = "app/downloads/Devixa-v1.0.0.apk.sha256"


class PageWebFieldNameVO(StrEnum):
    FULL_NAME = "full_name"
    EMAIL = "email"
    TOPIC = "topic"
    MESSAGE = "message"


class PageWebFieldIdVO(StrEnum):
    FULL_NAME = "fullname"
    EMAIL = "email"
    TOPIC = "topic"
    MESSAGE = "message"


class PageWebFieldLimitVO(IntEnum):
    FULL_NAME_MAX_LENGTH = 120
    EMAIL_MAX_LENGTH = 254
    TOPIC_MAX_LENGTH = 160
    MESSAGE_MAX_LENGTH = 2000
    MESSAGE_MIN_LENGTH = 10


class PageWebWidgetAttrVO(StrEnum):
    ID = "id"
    CLASS = "class"
    PLACEHOLDER = "placeholder"
    ROWS = "rows"


class PageWebWidgetClassVO(StrEnum):
    INPUT = "contact-form__input"
    TEXTAREA = "contact-form__textarea"


class PageWebPlaceholderVO(StrEnum):
    FULL_NAME = "مثال: علی احمدی"
    EMAIL = "you@email.com"
    TOPIC = "مثال: سوال درباره دوره‌ها"
    MESSAGE = "پیام خود را کامل بنویسید..."


class PageWebValidationMessageVO(StrEnum):
    REQUIRED = "این فیلد الزامی است."
    INVALID_EMAIL = "ایمیل وارد شده معتبر نیست."
    MAX_LENGTH = "تعداد کاراکترهای این فیلد نباید بیشتر از %(limit_value)d باشد."
    MESSAGE_TOO_SHORT = "متن پیام باید حداقل %(limit_value)d کاراکتر باشد."
    CONTACT_MESSAGE_SENT = "پیام شما با موفقیت ارسال شد. به زودی پاسخ می‌دهیم."
    CONTACT_EMAIL_NOT_CONFIGURED = "ایمیل دریافت پیام‌های تماس با ما تنظیم نشده است."
    CONTACT_MESSAGE_FAILED = "ارسال پیام با مشکل مواجه شد. لطفا دوباره تلاش کنید."


class PageWebFormErrorKeyVO(StrEnum):
    REQUIRED = "required"
    INVALID = "invalid"
    MAX_LENGTH = "max_length"
    MIN_LENGTH = "min_length"


class PageEmailTemplateVO(StrEnum):
    CONTACT_MESSAGE = "emails/fa_contact_message.html"


class PageEmailSubjectVO(StrEnum):
    CONTACT_MESSAGE = "پیام جدید از فرم تماس با ما"


class PageEmailContextKeyVO(StrEnum):
    FULL_NAME = "full_name"
    EMAIL = "email"
    TOPIC = "topic"
    MESSAGE = "message"
    APP_NAME = "app_name"


class PageErrorCodeVO(StrEnum):
    EMAIL_NOT_CONFIGURED = "email_not_configured"
    MESSAGE_FAILED = "message_failed"


class PageSettingNameVO(StrEnum):
    CONTACT_US_RECIPIENT_EMAIL = "CONTACT_US_RECIPIENT_EMAIL"
    DEFAULT_FROM_EMAIL = "DEFAULT_FROM_EMAIL"
    EMAIL_HOST_USER = "EMAIL_HOST_USER"


class PageWebContextKeyVO(StrEnum):
    FEATURED_COURSES = "featured_courses"
    FEATURED_ROADMAPS = "featured_roadmaps"
    TESTIMONIALS = "testimonials"
    FREQUENTLY_ASKED_QUESTIONS = "frequently_asked_questions"
    CHANNEL_LINKS = "channel_links"


class PageWebMessageVO(StrEnum):
    EMPTY_FEATURED_COURSES = "هنوز دوره ویژه‌ای منتشر نشده است."
