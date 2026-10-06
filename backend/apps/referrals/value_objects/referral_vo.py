from enum import IntEnum, StrEnum


class ReferralVO(StrEnum):
    CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    CODE_PREFIX = "DVX"


class ReferralLimitVO(IntEnum):
    CODE_RANDOM_LENGTH = 7
    RECENT_INVITEES = 8
    GENERATION_ATTEMPTS = 12
    ADMIN_MEMBER_LIMIT = 200


class ReferralMessageVO(StrEnum):
    INVALID_CODE = "کد معرف معتبر نیست. می‌توانید این فیلد را خالی بگذارید."
    SELF_REFERRAL = "امکان استفاده از کد معرف خودتان وجود ندارد."
    ALREADY_REFERRED = "برای این حساب قبلاً معرف ثبت شده است."
    CHANNEL_NOT_CONFIGURED = "کانال رفرال تلگرام هنوز در تنظیمات پروژه مشخص نشده است."
    CHANNEL_INVITE_CREATED = "لینک اختصاصی دعوت کانال با موفقیت ساخته شد."
    CHANNEL_INVITE_CREATE_FAILED = "ساخت لینک اختصاصی کانال انجام نشد. دسترسی ادمین ربات در کانال را بررسی کنید."


class TelegramChannelReferralVO(StrEnum):
    DEFAULT_CHANNEL_USERNAME = "@DevixaTEch"
    INVITE_NAME_PREFIX = "dvx_"
