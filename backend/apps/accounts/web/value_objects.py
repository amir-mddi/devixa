from __future__ import annotations

from enum import IntEnum, StrEnum


class AccountWebAppNameVO(StrEnum):
    NAMESPACE = "accounts_web"


class AccountWebTemplateVO(StrEnum):
    LOGIN = "web/accounts/login.html"
    REGISTER = "web/accounts/register.html"
    FORGOT_PASSWORD = "web/accounts/forgot_password.html"
    RECOVER_PASSWORD = "web/accounts/recover_password.html"
    PROFILE = "web/accounts/profile.html"


class AccountWebPathVO(StrEnum):
    LOGIN = "login/"
    REGISTER = "register/"
    LOGOUT = "logout/"
    FORGOT_PASSWORD = "forgot-password/"
    RECOVER_PASSWORD = "recover-password/"
    PROFILE = "profile/"
    PROFILE_EDIT = "profile/edit/"
    PROFILE_CONTACT = "profile/contact/"
    PROFILE_EMAIL_SEND = "profile/email/send/"
    PROFILE_EMAIL_VERIFY = "profile/email/verify/"
    PROFILE_PHONE_SEND = "profile/phone/send/"
    PROFILE_PHONE_VERIFY = "profile/phone/verify/"
    PROFILE_MESSENGER_DISCONNECT = "profile/messengers/<int:profile_id>/disconnect/"
    PROFILE_PAYMENT_RECEIPT = "profile/payments/<uuid:payment_id>/receipt/"
    PROFILE_TICKET_CREATE = "profile/tickets/new/"
    PROFILE_TICKET_REPLY = "profile/tickets/<int:ticket_id>/reply/"
    PROFILE_COURSE_REVIEW = "profile/courses/<uuid:course_id>/review/"
    OAUTH_GOOGLE_START = "oauth/google/start/"
    OAUTH_GOOGLE_CALLBACK = "oauth/google/callback/"
    OAUTH_GITHUB_START = "oauth/github/start/"
    OAUTH_GITHUB_CALLBACK = "oauth/github/callback/"


class AccountWebRouteNameVO(StrEnum):
    LOGIN = "login"
    REGISTER = "register"
    LOGOUT = "logout"
    FORGOT_PASSWORD = "forgot_password"
    RECOVER_PASSWORD = "recover_password"
    PROFILE = "profile"
    PROFILE_EDIT = "profile_edit"
    PROFILE_CONTACT = "profile_contact"
    PROFILE_EMAIL_SEND = "profile_email_send"
    PROFILE_EMAIL_VERIFY = "profile_email_verify"
    PROFILE_PHONE_SEND = "profile_phone_send"
    PROFILE_PHONE_VERIFY = "profile_phone_verify"
    PROFILE_MESSENGER_DISCONNECT = "profile_messenger_disconnect"
    PROFILE_PAYMENT_RECEIPT = "profile_payment_receipt"
    PROFILE_TICKET_CREATE = "profile_ticket_create"
    PROFILE_TICKET_REPLY = "profile_ticket_reply"
    PROFILE_COURSE_REVIEW = "profile_course_review"
    OAUTH_GOOGLE_START = "oauth_google_start"
    OAUTH_GOOGLE_CALLBACK = "oauth_google_callback"
    OAUTH_GITHUB_START = "oauth_github_start"
    OAUTH_GITHUB_CALLBACK = "oauth_github_callback"


class AccountWebReverseNameVO(StrEnum):
    LOGIN = "accounts_web:login"
    REGISTER = "accounts_web:register"
    FORGOT_PASSWORD = "accounts_web:forgot_password"
    RECOVER_PASSWORD = "accounts_web:recover_password"
    PROFILE = "accounts_web:profile"
    PROFILE_EDIT = "accounts_web:profile_edit"
    PROFILE_CONTACT = "accounts_web:profile_contact"
    PROFILE_EMAIL_SEND = "accounts_web:profile_email_send"
    PROFILE_EMAIL_VERIFY = "accounts_web:profile_email_verify"
    PROFILE_PHONE_SEND = "accounts_web:profile_phone_send"
    PROFILE_PHONE_VERIFY = "accounts_web:profile_phone_verify"
    PROFILE_MESSENGER_DISCONNECT = "accounts_web:profile_messenger_disconnect"
    PROFILE_PAYMENT_RECEIPT = "accounts_web:profile_payment_receipt"
    PROFILE_TICKET_CREATE = "accounts_web:profile_ticket_create"
    PROFILE_TICKET_REPLY = "accounts_web:profile_ticket_reply"
    PROFILE_COURSE_REVIEW = "accounts_web:profile_course_review"
    OAUTH_GOOGLE_START = "accounts_web:oauth_google_start"
    OAUTH_GOOGLE_CALLBACK = "accounts_web:oauth_google_callback"
    OAUTH_GITHUB_START = "accounts_web:oauth_github_start"
    OAUTH_GITHUB_CALLBACK = "accounts_web:oauth_github_callback"


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
    METHOD = "method"
    CODE = "code"
    PASSWORD = "password"
    NEW_PASSWORD = "new_password"
    PASSWORD_CONFIRM = "password_confirm"
    PHONE_NUMBER = "phone_number"
    PROFILE_PHOTO = "profile_photo"
    REMOVE_PROFILE_PHOTO = "remove_profile_photo"
    SUBJECT = "subject"
    MESSAGE = "message"
    RATING = "rating"
    TITLE = "title"
    COMMENT = "comment"
    RECEIPT_FILE = "receipt_file"
    TRACKING_CODE = "tracking_code"
    PAYER_CARD_LAST4 = "payer_card_last4"
    PAID_AMOUNT = "paid_amount"
    NOTE = "note"
    RECAPTCHA_TOKEN = "recaptcha_token"


class AccountWebFieldLimitVO(IntEnum):
    NAME_MAX_LENGTH = 150
    USERNAME_MAX_LENGTH = 150
    EMAIL_MAX_LENGTH = 254
    RECOVERY_CODE_MAX_LENGTH = 6
    PHONE_NUMBER_MAX_LENGTH = 13
    SUPPORT_SUBJECT_MAX_LENGTH = 180
    SUPPORT_MESSAGE_MAX_LENGTH = 2500
    REVIEW_TITLE_MAX_LENGTH = 180
    REVIEW_COMMENT_MAX_LENGTH = 5000
    PAYMENT_TRACKING_CODE_MAX_LENGTH = 120
    PAYMENT_NOTE_MAX_LENGTH = 1000
    RECAPTCHA_TOKEN_MAX_LENGTH = 4096


class AccountWebWidgetAttrVO(StrEnum):
    PLACEHOLDER = "placeholder"
    AUTOCOMPLETE = "autocomplete"


class AccountWebAutocompleteVO(StrEnum):
    USERNAME = "username"
    EMAIL = "email"
    CURRENT_PASSWORD = "current-password"
    NEW_PASSWORD = "new-password"
    ONE_TIME_CODE = "one-time-code"
    TEL = "tel"


class AccountWebPlaceholderVO(StrEnum):
    IDENTIFIER = "ایمیل یا نام کاربری"
    FIRST_NAME = "نام خود را وارد کنید"
    LAST_NAME = "نام خانوادگی خود را وارد کنید"
    USERNAME = "نام کاربری خود را وارد کنید"
    EMAIL = "ایمیل Gmail خود را وارد کنید"
    RECOVERY_EMAIL = "ایمیل حساب را وارد کنید"
    RECOVERY_PHONE = "شماره موبایل تأییدشده مانند 09121234567"
    PASSWORD = "رمز عبور خود را وارد کنید"
    LOGIN_PASSWORD = "رمز عبور"
    PASSWORD_CONFIRM = "تکرار رمز عبور خود را وارد کنید"
    RECOVERY_CODE = "کد ۶ رقمی را وارد کنید"
    NEW_PASSWORD = "رمز عبور جدید"
    NEW_PASSWORD_CONFIRM = "تکرار رمز عبور جدید"
    PHONE_NUMBER = "شماره موبایل مانند 09121234567"
    SUPPORT_SUBJECT = "موضوع تیکت"
    SUPPORT_MESSAGE = "پیام خود را برای پشتیبانی بنویسید"
    VERIFICATION_CODE = "کد ۶ رقمی تأیید"
    REVIEW_TITLE = "عنوان کوتاه دیدگاه (اختیاری)"
    REVIEW_COMMENT = "نظر شما درباره این دوره"
    PAYMENT_TRACKING_CODE = "کد رهگیری تراکنش"
    PAYMENT_CARD_LAST4 = "۴ رقم آخر کارت پرداخت‌کننده"
    PAYMENT_AMOUNT = "مبلغ پرداخت‌شده"
    PAYMENT_NOTE = "توضیحات تکمیلی (اختیاری)"


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
    RECOVERY_SMS_CODE_SENT = "اگر شماره موبایل وارد شده در سیستم وجود داشته و تأیید شده باشد، کد بازیابی برای شما پیامک شد."
    PASSWORD_RESET_SUCCESS = (
        "رمز عبور شما با موفقیت تغییر کرد. حالا می‌توانید وارد شوید."
    )
    INVALID_PHONE_NUMBER = "شماره موبایل معتبر نیست."
    INVALID_PROFILE_PHOTO = "تصویر پروفایل معتبر نیست."
    SUPPORT_MESSAGE_TOO_SHORT = "متن تیکت باید حداقل ۳ کاراکتر باشد."
    REVIEW_COMMENT_TOO_SHORT = "متن دیدگاه باید حداقل ۳ کاراکتر باشد."
    INVALID_PAYMENT_RECEIPT = (
        "رسید معتبر نیست. فقط JPG، PNG یا PDF تا حجم ۵ مگابایت مجاز است."
    )
    PAYMENT_RECEIPT_REQUIRED = "فایل رسید یا کد رهگیری را وارد کنید."
    INVALID_CARD_LAST4 = "۴ رقم آخر کارت باید دقیقاً چهار رقم باشد."
    RECAPTCHA_FAILED = "اعتبارسنجی امنیتی ناموفق بود. صفحه را تازه‌سازی کنید و دوباره تلاش کنید."
    RECAPTCHA_UNAVAILABLE = "سرویس اعتبارسنجی امنیتی در دسترس نیست. اتصال اینترنت را بررسی کرده و دوباره تلاش کنید."


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
