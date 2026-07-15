from __future__ import annotations

from enum import StrEnum


class ProjectConfigSingletonVO(StrEnum):
    DEFAULT_KEY = "default"


class ProjectConfigFieldNameVO(StrEnum):
    SINGLETON_KEY = "singleton_key"
    NAME = "name"
    DISPLAY_NAME = "display_name"
    SLUG = "slug"
    DESCRIPTION = "description"
    TAGLINE = "tagline"
    EMAIL_DOMAIN = "email_domain"
    CONTACT_EMAIL = "contact_email"
    SUPPORT_EMAIL = "support_email"
    SALES_EMAIL = "sales_email"
    PARTNERSHIP_EMAIL = "partnership_email"
    GITHUB_URL = "github_url"
    LINKEDIN_URL = "linkedin_url"
    TELEGRAM_URL = "telegram_url"
    INSTAGRAM_URL = "instagram_url"
    TELEGRAM_BOT_URL = "telegram_bot_url"
    BALE_BOT_URL = "bale_bot_url"
    RUBIKA_BOT_URL = "rubika_bot_url"
    PHONE = "phone"
    ADDRESS = "address"
    WORKING_HOURS = "working_hours"


class ProjectConfigEnvNameVO(StrEnum):
    NAME = "PROJECT_NAME"
    DISPLAY_NAME = "PROJECT_DISPLAY_NAME"
    SLUG = "PROJECT_SLUG"
    DESCRIPTION = "PROJECT_DESCRIPTION"
    TAGLINE = "PROJECT_TAGLINE"
    EMAIL_DOMAIN = "PROJECT_EMAIL_DOMAIN"
    CONTACT_EMAIL = "PROJECT_CONTACT_EMAIL"
    SUPPORT_EMAIL = "PROJECT_SUPPORT_EMAIL"
    SALES_EMAIL = "PROJECT_SALES_EMAIL"
    PARTNERSHIP_EMAIL = "PROJECT_PARTNERSHIP_EMAIL"
    GITHUB_URL = "PROJECT_GITHUB_URL"
    LINKEDIN_URL = "PROJECT_LINKEDIN_URL"
    TELEGRAM_URL = "PROJECT_TELEGRAM_URL"
    INSTAGRAM_URL = "PROJECT_INSTAGRAM_URL"
    TELEGRAM_BOT_URL = "PROJECT_TELEGRAM_BOT_URL"
    BALE_BOT_URL = "PROJECT_BALE_BOT_URL"
    RUBIKA_BOT_URL = "PROJECT_RUBIKA_BOT_URL"
    PHONE = "PROJECT_PHONE"
    ADDRESS = "PROJECT_ADDRESS"
    WORKING_HOURS = "PROJECT_WORKING_HOURS"


class ProjectConfigDefaultVO(StrEnum):
    NAME = "devixa"
    DISPLAY_NAME = "Devixa"
    SLUG = "devixa"
    DESCRIPTION_TEMPLATE = "{project_name}؛ تجربه یادگیری برنامه‌نویسی پروژه‌محور با رابط کاربری سریع، مدرن و حرفه‌ای."
    TAGLINE = "مسیر یادگیری برنامه نویسی از مقدماتی تا ورود به بازارکار"
    EMAIL_DOMAIN = "acdevixa.ir"
    CONTACT_EMAIL_LOCAL_PART = "hello"
    SUPPORT_EMAIL_LOCAL_PART = "support"
    SALES_EMAIL_LOCAL_PART = "sales"
    PARTNERSHIP_EMAIL_LOCAL_PART = "partnership"
    EMPTY_URL = "#"
    PHONE = "+98 9123456789"
    ADDRESS = "ایران، تهران"
    WORKING_HOURS = "شنبه تا چهارشنبه، 9:00 تا 18:00"


class ProjectConfigSerializerMessageVO(StrEnum):
    SLUG_INVALID = "اسلاگ فقط می‌تواند شامل حروف انگلیسی، عدد، خط تیره و خط زیر باشد."
