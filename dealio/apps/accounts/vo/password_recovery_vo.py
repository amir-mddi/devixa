from __future__ import annotations

from enum import IntEnum, StrEnum


class AccountPasswordRecoveryErrorCodeVO(StrEnum):
    INVALID_OR_EXPIRED_CODE = "invalid_or_expired_code"
    USER_NOT_FOUND = "user_not_found"
    INACTIVE_ACCOUNT = "inactive_account"
    INVALID_PASSWORD = "invalid_password"


class AccountPasswordRecoveryCacheVO(StrEnum):
    EMAIL_KEY_TEMPLATE = "forget_password_verification:{user_id}:{identifier_fingerprint}"
    SMS_KEY_TEMPLATE = "sms_password_recovery:{user_id}:{identifier_fingerprint}"


class AccountPasswordRecoveryEmailVO(StrEnum):
    SUBJECT = "اعتبارسنجی رمز عبور"
    TEMPLATE_NAME = "emails/fa_forgot_password.html"
    CONTEXT_SUBJECT = "کد اعتبارسنجی فراموشی رمز عبور"
    FALLBACK_USER_NAME = "کاربر"


class AccountPasswordRecoveryEmailContextKeyVO(StrEnum):
    SUBJECT = "subject"
    APP_NAME = "app_name"
    USER_NAME = "user_name"
    CODE = "code"
    EXPIRATION_MINUTES = "expiration_minutes"
    CURRENT_YEAR = "current_year"


class AccountPasswordRecoveryCodeVO(IntEnum):
    MIN_VALUE = 100000
    MAX_RANDOM_VALUE = 900000
    EXPIRATION_MINUTES = 5


class AccountPasswordRecoveryApiMessageVO(StrEnum):
    CODE_SENT = "اگر این ایمیل وجود داشته باشد، کد بازیابی ارسال شده یا کد قبلی هنوز معتبر است."
    SMS_CODE_SENT = "اگر این شماره موبایل وجود داشته باشد، کد بازیابی ارسال شده یا کد قبلی هنوز معتبر است."
    INVALID_OR_EXPIRED_CODE = "کد بازیابی نامعتبر است یا منقضی شده است."
    PASSWORD_RESET_SUCCESS = "رمز عبور با موفقیت تغییر کرد."
    INVALID_PASSWORD = "رمز عبور جدید شرایط امنیتی لازم را ندارد."


class AccountPasswordRecoveryResponseKeyVO(StrEnum):
    DETAIL = "detail"
