from enum import IntEnum, StrEnum


class ReferralVO(StrEnum):
    CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    CODE_PREFIX = "DVX"


class ReferralLimitVO(IntEnum):
    CODE_RANDOM_LENGTH = 7
    RECENT_INVITEES = 8
    GENERATION_ATTEMPTS = 12


class ReferralMessageVO(StrEnum):
    INVALID_CODE = "کد معرف معتبر نیست. می‌توانید این فیلد را خالی بگذارید."
    SELF_REFERRAL = "امکان استفاده از کد معرف خودتان وجود ندارد."
    ALREADY_REFERRED = "برای این حساب قبلاً معرف ثبت شده است."
