from __future__ import annotations

from enum import IntEnum, StrEnum


class AccountWebAppNameVO(StrEnum):
    NAMESPACE = "accounts_web"


class AccountWebTemplateVO(StrEnum):
    LOGIN = "web/accounts/login.html"
    REGISTER = "web/accounts/register.html"
    FORGOT_PASSWORD = "web/accounts/forgot_password.html"
    RECOVER_PASSWORD = "web/accounts/recover_password.html"


class AccountWebPathVO(StrEnum):
    LOGIN = "login/"
    REGISTER = "register/"
    LOGOUT = "logout/"
    FORGOT_PASSWORD = "forgot-password/"
    RECOVER_PASSWORD = "recover-password/"


class AccountWebRouteNameVO(StrEnum):
    LOGIN = "login"
    REGISTER = "register"
    LOGOUT = "logout"
    FORGOT_PASSWORD = "forgot_password"
    RECOVER_PASSWORD = "recover_password"


class AccountWebReverseNameVO(StrEnum):
    LOGIN = "accounts_web:login"
    REGISTER = "accounts_web:register"
    FORGOT_PASSWORD = "accounts_web:forgot_password"
    RECOVER_PASSWORD = "accounts_web:recover_password"


class AccountWebRequestKeyVO(StrEnum):
    NEXT = "next"


class AccountWebUrlSeparatorVO(StrEnum):
    QUERY = "?"


class AccountWebFieldNameVO(StrEnum):
    IDENTIFIER = "identifier"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    USERNAME = "username"
    EMAIL = "email"
    CODE = "code"
    PASSWORD = "password"
    NEW_PASSWORD = "new_password"
    PASSWORD_CONFIRM = "password_confirm"


class AccountWebFieldLimitVO(IntEnum):
    NAME_MAX_LENGTH = 150
    USERNAME_MAX_LENGTH = 150
    EMAIL_MAX_LENGTH = 254
    RECOVERY_CODE_MAX_LENGTH = 6


class AccountWebWidgetAttrVO(StrEnum):
    PLACEHOLDER = "placeholder"
    AUTOCOMPLETE = "autocomplete"


class AccountWebAutocompleteVO(StrEnum):
    USERNAME = "username"
    EMAIL = "email"
    CURRENT_PASSWORD = "current-password"
    NEW_PASSWORD = "new-password"
    ONE_TIME_CODE = "one-time-code"


class AccountWebPlaceholderVO(StrEnum):
    IDENTIFIER = "ایمیل یا نام کاربری"
    FIRST_NAME = "نام خود را وارد کنید"
    LAST_NAME = "نام خانوادگی خود را وارد کنید"
    USERNAME = "نام کاربری خود را وارد کنید"
    EMAIL = "ایمیل Gmail خود را وارد کنید"
    PASSWORD = "رمز عبور خود را وارد کنید"
    LOGIN_PASSWORD = "رمز عبور"
    PASSWORD_CONFIRM = "تکرار رمز عبور خود را وارد کنید"
    RECOVERY_CODE = "کد ۶ رقمی را وارد کنید"
    NEW_PASSWORD = "رمز عبور جدید"
    NEW_PASSWORD_CONFIRM = "تکرار رمز عبور جدید"


class AccountWebValidationMessageVO(StrEnum):
    REQUIRED = "این فیلد الزامی است."
    INVALID_EMAIL = "ایمیل وارد شده معتبر نیست."
    INVALID_GMAIL = "ایمیل باید از نوع Gmail باشد."
    INVALID_PERSIAN_TEXT = "این فیلد فقط باید شامل حروف فارسی باشد."
    INVALID_USERNAME = "نام کاربری باید با حرف انگلیسی شروع شود و فقط شامل حروف انگلیسی، عدد، خط زیر، نقطه یا خط تیره باشد."
    INVALID_RECOVERY_CODE = "کد بازیابی باید دقیقا ۶ رقم باشد."
    USERNAME_EXISTS = "این نام کاربری قبلا ثبت شده است."
    EMAIL_EXISTS = "این ایمیل قبلا ثبت شده است."
    PASSWORD_MISMATCH = "رمز عبور و تکرار آن یکسان نیستند."
    PASSWORD_TOO_SHORT = "رمز عبور باید حداقل %(min_length)d کاراکتر باشد."
    PASSWORD_TOO_COMMON = "این رمز عبور بیش از حد ساده و رایج است."
    PASSWORD_ENTIRELY_NUMERIC = "رمز عبور نمی‌تواند فقط عدد باشد."
    PASSWORD_TOO_SIMILAR = "رمز عبور بیش از حد به اطلاعات حساب کاربری شباهت دارد."
    PASSWORD_INVALID = "رمز عبور معتبر نیست."
    INVALID_CREDENTIALS = "ایمیل/نام کاربری یا رمز عبور اشتباه است."
    INVALID_OR_EXPIRED_RECOVERY_CODE = "کد بازیابی نامعتبر است یا منقضی شده است."
    INACTIVE_ACCOUNT = "حساب کاربری شما غیرفعال است."
    LOGIN_SUCCESS = "ورود شما با موفقیت انجام شد."
    REGISTER_SUCCESS = "حساب کاربری شما ساخته شد. حالا وارد شوید."
    LOGOUT_SUCCESS = "از حساب کاربری خارج شدید."
    RECOVERY_CODE_SENT = "اگر ایمیل وارد شده در سیستم وجود داشته باشد، کد بازیابی رمز عبور برای شما ارسال شد."
    PASSWORD_RESET_SUCCESS = "رمز عبور شما با موفقیت تغییر کرد. حالا می‌توانید وارد شوید."


class AccountWebFormErrorKeyVO(StrEnum):
    REQUIRED = "required"
    INVALID = "invalid"
    MAX_LENGTH = "max_length"


class AccountWebMaxLengthMessageVO(StrEnum):
    DEFAULT = "تعداد کاراکترهای این فیلد نباید بیشتر از %(limit_value)d باشد."


class AccountWebRegexVO(StrEnum):
    PERSIAN_TEXT = r"^[\u0600-\u06FF\s‌]+$"
    ENGLISH_USERNAME = r"^[A-Za-z][A-Za-z0-9_.-]*$"
    RECOVERY_CODE = r"^\d{6}$"


class AccountWebEmailVO(StrEnum):
    GMAIL_SUFFIX = "@gmail.com"


class AccountWebPasswordValidationCodeVO(StrEnum):
    PASSWORD_TOO_SHORT = "password_too_short"
    PASSWORD_TOO_COMMON = "password_too_common"
    PASSWORD_ENTIRELY_NUMERIC = "password_entirely_numeric"
    PASSWORD_TOO_SIMILAR = "password_too_similar"
