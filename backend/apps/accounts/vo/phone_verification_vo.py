from enum import StrEnum


class AccountPhoneVerificationErrorCodeVO(StrEnum):
    USER_NOT_FOUND = "user_not_found"
    INACTIVE_ACCOUNT = "inactive_account"
    PHONE_NUMBER_REQUIRED = "phone_number_required"
    ALREADY_VERIFIED = "already_verified"
    INVALID_OR_EXPIRED_CODE = "invalid_or_expired_code"
    PHONE_NUMBER_ALREADY_IN_USE = "phone_number_already_in_use"


class AccountPhoneVerificationCacheVO(StrEnum):
    KEY_TEMPLATE = "phone_verification:{user_id}:{identifier_fingerprint}"


class AccountPhoneVerificationApiMessageVO(StrEnum):
    CODE_SENT = "کد تایید شماره موبایل ارسال شد."
    CODE_STILL_ACTIVE = "کد تایید قبلی هنوز معتبر است؛ همان کد را استفاده کنید."
    VERIFIED = "شماره موبایل با موفقیت تایید شد."
    PHONE_NUMBER_REQUIRED = "شماره موبایل برای حساب کاربری ثبت نشده است."
    ALREADY_VERIFIED = "شماره موبایل قبلاً تایید شده است."
    INVALID_OR_EXPIRED_CODE = "کد تایید نامعتبر است یا منقضی شده است."
    PHONE_NUMBER_ALREADY_IN_USE = "این شماره موبایل برای حساب دیگری ثبت شده است."
    INACTIVE_ACCOUNT = "حساب کاربری غیرفعال است."
    USER_NOT_FOUND = "حساب کاربری یافت نشد."
