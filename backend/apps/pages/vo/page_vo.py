from __future__ import annotations

from enum import IntEnum, StrEnum


class PageWebAppNameVO(StrEnum):
    NAMESPACE = "pages_web"


class PageWebTemplateVO(StrEnum):
    HOME = "web/pages/home.html"
    ABOUT_US = "web/pages/about_us.html"
    CONTACT_US = "web/pages/contact_us.html"
    CHANNELS = "web/pages/channels.html"
    ANDROID_APP = "web/pages/android_app.html"


class PageWebPathVO(StrEnum):
    HOME = ""
    ABOUT_US = "about-us/"
    CONTACT_US = "contact-us/"
    CHANNELS = "channels/"
    ANDROID_APP = "android/"
    ANDROID_APP_DOWNLOAD = "downloads/android/"


class PageWebRouteNameVO(StrEnum):
    HOME = "home"
    ABOUT_US = "about_us"
    CONTACT_US = "contact_us"
    CHANNELS = "channels"
    ANDROID_APP = "android_app"
    ANDROID_APP_DOWNLOAD = "download_android_app"


class PageWebReverseNameVO(StrEnum):
    HOME = "pages_web:home"
    ABOUT_US = "pages_web:about_us"
    CONTACT_US = "pages_web:contact_us"
    CHANNELS = "pages_web:channels"
    ANDROID_APP = "pages_web:android_app"
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
    ANDROID_VERSION = "android_version"
    ANDROID_FILENAME = "android_filename"


class PageWebMessageVO(StrEnum):
    EMPTY_FEATURED_COURSES = "هنوز دوره ویژه‌ای منتشر نشده است."


class PageHomeTestimonialVO:
    BACKEND_COMMENT = (
        "قبل از {project_name} هی بین آموزش‌ها می‌پریدم و هیچ پروژه‌ای رو کامل نمی‌کردم. "
        "اینجا بالاخره یه پروژه رو از اول تا آخر بستم و برای مصاحبه هم دستم پرتر بود."
    )
    BACKEND_NAME = "علی محمدی"
    BACKEND_ROLE = "Backend Developer"

    FRONTEND_COMMENT = (
        "چیزی که برام خوب بود این بود که فقط ویدئو ندیدم؛ هر بخش رو خودم ساختم و تازه فهمیدم "
        "کجاها واقعاً مشکل دارم."
    )
    FRONTEND_NAME = "سارا احمدی"
    FRONTEND_ROLE = "Frontend Developer"

    FULLSTACK_COMMENT = (
        "روی تمرین‌هام بازخورد گرفتم و خیلی از باگ‌هایی که خودم نمی‌دیدم زودتر پیدا شد. "
        "حس نمی‌کردم وسط مسیر تنها موندم."
    )
    FULLSTACK_NAME = "رضا کریمی"
    FULLSTACK_ROLE = "Fullstack Developer"

    FREELANCE_COMMENT = (
        "آخر دوره یه نمونه‌کار واقعی داشتم که می‌تونستم نشون بدم. برای گرفتن پروژه فریلنسری "
        "اعتمادبه‌نفسم خیلی بیشتر شد."
    )
    FREELANCE_NAME = "مریم رضایی"
    FREELANCE_ROLE = "Freelance Developer"


class PageHomeFaqVO:
    DEFAULT_ITEMS = (
        (
            "آیا دوره‌ها پیش‌نیاز دارند؟",
            "بیشتر دوره‌های مقدماتی بدون نیاز به پیش‌نیاز طراحی شده‌اند. اگر دوره‌ای پیش‌نیاز داشته باشد، در صفحه همان دوره کامل نوشته می‌شود.",
        ),
        (
            "آیا در طول دوره پروژه عملی انجام می‌دهیم؟",
            "بله، تمرکز اصلی دوره‌ها روی پروژه واقعی است تا در پایان مسیر نمونه‌کار قابل ارائه داشته باشید.",
        ),
        (
            "پشتیبانی دوره‌ها چگونه است؟",
            "سوالات از طریق کانال‌های پشتیبانی، ربات‌ها و تیکت‌ها بررسی می‌شود تا در مسیر یادگیری تنها نمانید.",
        ),
        (
            "آیا گواهی پایان دوره دریافت می‌کنیم؟",
            "پس از تکمیل دوره و انجام تمرین‌های اصلی، گواهی پایان دوره برای شما قابل صدور است.",
        ),
        (
            "آیا بوت‌کمپ برای افراد مبتدی مناسب است؟",
            "بله، مسیر از مباحث پایه شروع می‌شود و مرحله به مرحله تا سطح پروژه واقعی و ورود به بازار کار جلو می‌رود.",
        ),
        (
            "بعد از پایان دوره چه مسیری پیشنهاد می‌کنید؟",
            "تکمیل نمونه‌کار، انجام پروژه واقعی، فعالیت فریلنسری و ادامه مسیر از طریق نقشه‌راه‌های تخصصی پیشنهاد می‌شود.",
        ),
    )


class PageChannelLinkVO:
    TELEGRAM_TITLE = "ربات تلگرام"
    TELEGRAM_DESCRIPTION = "ثبت‌نام، خرید دوره و پیگیری سفارش از طریق تلگرام"
    TELEGRAM_ICON = "fa-brands fa-telegram"
    TELEGRAM_BADGE = "Telegram"

    BALE_TITLE = "ربات بله"
    BALE_DESCRIPTION = "ثبت‌نام و خرید دوره برای کاربرانی که از بله استفاده می‌کنند"
    BALE_ICON = "fa-solid fa-comments"
    BALE_BADGE = "Bale"

    RUBIKA_TITLE = "ربات روبیکا"
    RUBIKA_DESCRIPTION = "ثبت‌نام، خرید دوره و پیگیری سفارش از طریق روبیکا"
    RUBIKA_ICON = "fa-solid fa-comment-dots"
    RUBIKA_BADGE = "Rubika"

