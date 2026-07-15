from __future__ import annotations

from enum import IntEnum, StrEnum


class OAuthEndpointVO(StrEnum):
    GOOGLE_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"
    GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
    GITHUB_USER = "https://api.github.com/user"
    GITHUB_EMAILS = "https://api.github.com/user/emails"


class OAuthScopeVO(StrEnum):
    GOOGLE = "openid email profile"
    GITHUB = "read:user user:email"


class OAuthSettingNameVO(StrEnum):
    GOOGLE_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"
    GOOGLE_CLIENT_SECRET = "GOOGLE_OAUTH_CLIENT_SECRET"
    GITHUB_CLIENT_ID = "GITHUB_OAUTH_CLIENT_ID"
    GITHUB_CLIENT_SECRET = "GITHUB_OAUTH_CLIENT_SECRET"


class OAuthMessageVO(StrEnum):
    PROVIDER_NOT_CONFIGURED = "ورود با این سرویس هنوز پیکربندی نشده است."
    PROVIDER_REJECTED = "سرویس ورود، درخواست را نپذیرفت. دوباره تلاش کنید."
    PROVIDER_UNAVAILABLE = "سرویس ورود موقتاً در دسترس نیست."
    PROVIDER_INVALID_RESPONSE = "پاسخ سرویس ورود معتبر نبود."
    PROVIDER_OVERSIZED_RESPONSE = "پاسخ سرویس ورود بیش از حد مجاز بود."
    MISSING_ACCESS_TOKEN = "سرویس ورود توکن دسترسی برنگرداند."
    MISSING_STABLE_ID = "شناسه پایدار حساب از سرویس ورود دریافت نشد."
    MISSING_EMAIL = "ایمیل معتبر از سرویس ورود دریافت نشد."
    UNVERIFIED_EMAIL = "ایمیل حساب شما در سرویس ورود تأیید نشده است."
    GITHUB_EMAIL_REQUIRED = "برای ورود با GitHub باید یک ایمیل اصلی تأییدشده داشته باشید."
    ACCOUNT_NOT_REGISTERED = "این ایمیل قبلاً در سایت ثبت نشده است. ابتدا با همین ایمیل حساب بسازید."
    ACCOUNT_INACTIVE = "این حساب کاربری غیرفعال است."
    ACCOUNT_LINK_CONFLICT = "این حساب اجتماعی قبلاً به حساب کاربری دیگری متصل شده است."
    PROVIDER_ALREADY_LINKED = "یک حساب دیگر از همین سرویس قبلاً به حساب کاربری شما متصل شده است."
    REDIRECT_NOT_ALLOWED = "آدرس بازگشت OAuth مجاز نیست."
    REDIRECT_ALLOWLIST_MISSING = "فهرست آدرس‌های بازگشت OAuth پیکربندی نشده است."
    INVALID_STATE = "درخواست ورود منقضی یا نامعتبر است. دوباره از صفحه ورود شروع کنید."
    AUTHORIZATION_CANCELLED = "ورود توسط کاربر یا سرویس لغو شد."
    LOGIN_SUCCESS = "ورود با حساب اجتماعی با موفقیت انجام شد."
    UNSUPPORTED_PROVIDER = "سرویس ورود پشتیبانی نمی‌شود."


class OAuthLogMessageVO(StrEnum):
    MISSING_SETTING = "Missing required OAuth setting: {setting_name}"
    PROVIDER_HTTP_ERROR = "OAuth provider HTTP error: provider={provider} status={status}"
    PROVIDER_CONNECTION_ERROR = "OAuth provider connection error: provider={provider} error={error}"
    PROVIDER_NON_JSON = "OAuth provider returned non-JSON data: provider={provider}"
    LOGIN_FAILED = "OAuth login failed: {error}"


class OAuthResponseKeyVO(StrEnum):
    DETAIL = "detail"


class OAuthSafeProfileKeyVO(StrEnum):
    SUBJECT = "sub"
    ID = "id"
    LOGIN = "login"
    NAME = "name"
    GIVEN_NAME = "given_name"
    FAMILY_NAME = "family_name"
    PICTURE = "picture"
    AVATAR_URL = "avatar_url"
    HTML_URL = "html_url"
    LOCALE = "locale"


class OAuthDefaultVO(IntEnum):
    STATE_TTL_SECONDS = 600
    MAX_RESPONSE_BYTES = 1024 * 1024
