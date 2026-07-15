from __future__ import annotations

from enum import IntEnum, StrEnum


class AccountProfileMessageVO(StrEnum):
    PROFILE_UPDATED = "اطلاعات پروفایل با موفقیت به‌روزرسانی شد."
    CONTACT_UPDATED = "اطلاعات تماس با موفقیت به‌روزرسانی شد."
    EMAIL_CHANGED_REVERIFY = (
        "ایمیل جدید ذخیره شد و برای استفاده کامل باید دوباره تأیید شود."
    )
    PHONE_CHANGED_REVERIFY = "شماره موبایل جدید ذخیره شد و باید دوباره تأیید شود."
    EMAIL_CODE_SENT = "کد تأیید ایمیل ارسال شد."
    EMAIL_CODE_STILL_ACTIVE = "کد قبلی ایمیل هنوز معتبر است؛ همان کد را استفاده کنید."
    EMAIL_VERIFIED = "ایمیل با موفقیت تأیید شد."
    EMAIL_ALREADY_VERIFIED = "ایمیل قبلاً تأیید شده است."
    EMAIL_REQUIRED = "برای تأیید، ابتدا یک ایمیل معتبر ثبت کنید."
    EMAIL_CODE_INVALID = "کد تأیید ایمیل نامعتبر است یا منقضی شده است."
    EMAIL_SEND_FAILED = "ارسال کد تأیید ایمیل انجام نشد. تنظیمات ایمیل را بررسی کنید."
    PHONE_CODE_SENT = "کد تأیید شماره موبایل ارسال شد."
    PHONE_CODE_STILL_ACTIVE = "کد قبلی موبایل هنوز معتبر است؛ همان کد را استفاده کنید."
    PHONE_VERIFIED = "شماره موبایل با موفقیت تأیید شد."
    PHONE_SEND_FAILED = "ارسال کد تأیید موبایل انجام نشد. کمی بعد دوباره تلاش کنید."
    MESSENGER_DISCONNECTED = "اتصال پیام‌رسان با موفقیت قطع شد."
    MESSENGER_DISCONNECT_FAILED = (
        "این اتصال پیام‌رسان یافت نشد یا متعلق به حساب شما نیست."
    )
    SUPPORT_TICKET_CREATED = "تیکت پشتیبانی با موفقیت ثبت شد."
    SUPPORT_REPLY_SENT = "پاسخ شما به تیکت اضافه شد."
    SUPPORT_OPERATION_FAILED = "انجام عملیات تیکت ممکن نبود. دوباره تلاش کنید."
    REVIEW_SUBMITTED = "دیدگاه شما ثبت شد و پس از بررسی مدیر نمایش داده می‌شود."
    REVIEW_OPERATION_FAILED = "ثبت دیدگاه انجام نشد. اطلاعات فرم را بررسی کنید."
    PAYMENT_RECEIPT_UPLOADED = "رسید پرداخت با موفقیت ثبت شد و در انتظار بررسی است."
    PAYMENT_RECEIPT_UPLOAD_FAILED = (
        "ثبت رسید پرداخت انجام نشد. اطلاعات فرم یا وضعیت پرداخت را بررسی کنید."
    )
    PROFILE_NOT_FOUND = "اطلاعات حساب کاربری یافت نشد."
    PROFILE_PHOTO_INVALID = (
        "تصویر پروفایل معتبر نیست. فقط JPG، PNG یا WebP تا حجم ۳ مگابایت مجاز است."
    )
    USERNAME_ALREADY_IN_USE = "این نام کاربری قبلاً استفاده شده است."
    EMAIL_ALREADY_IN_USE = "این ایمیل قبلاً برای حساب دیگری ثبت شده است."
    PHONE_ALREADY_IN_USE = "این شماره موبایل قبلاً برای حساب دیگری ثبت شده است."
    INACTIVE_ACCOUNT = "حساب کاربری شما غیرفعال است."


class AccountProfileFieldVO(StrEnum):
    PROFILE_PHOTO = "profile_photo"
    REMOVE_PROFILE_PHOTO = "remove_profile_photo"
    PHONE_NUMBER = "phone_number"
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


class AccountProfileSectionVO(StrEnum):
    OVERVIEW = "overview"
    PROFILE = "profile"
    CONTACT = "contact"
    COURSES = "courses"
    BILLING = "billing"
    TICKETS = "tickets"


class AccountProfileLimitVO(IntEnum):
    PHONE_NUMBER_MAX_LENGTH = 13
    SUPPORT_SUBJECT_MAX_LENGTH = 180
    SUPPORT_MESSAGE_MAX_LENGTH = 2500
    REVIEW_TITLE_MAX_LENGTH = 180
    REVIEW_COMMENT_MAX_LENGTH = 5000
    PAYMENT_TRACKING_CODE_MAX_LENGTH = 120
    PAYMENT_NOTE_MAX_LENGTH = 1000


class AccountProfileStatusLabelVO:
    ORDER = {
        "pending": "در انتظار پرداخت",
        "paid": "پرداخت‌شده",
        "cancelled": "لغوشده",
        "expired": "منقضی‌شده",
        "refunded": "بازپرداخت‌شده",
    }
    PAYMENT = {
        "initiated": "شروع‌شده",
        "pending_receipt": "در انتظار رسید",
        "pending_verification": "در انتظار بررسی",
        "receipt_rejected": "رسید رد شده",
        "succeeded": "موفق",
        "failed": "ناموفق",
        "cancelled": "لغوشده",
        "refunded": "بازپرداخت‌شده",
    }
    ENROLLMENT = {
        "active": "فعال",
        "refunded": "بازپرداخت‌شده",
        "cancelled": "لغوشده",
    }
    REVIEW = {
        "pending": "در انتظار بررسی",
        "approved": "تأییدشده",
        "rejected": "ردشده",
    }
    TICKET = {
        "open": "باز",
        "answered": "پاسخ داده شده",
        "closed": "بسته",
    }
    RECEIPT = {
        "pending": "در انتظار بررسی",
        "approved": "تأییدشده",
        "rejected": "ردشده",
    }
    PROVIDER = {
        "telegram": "تلگرام",
        "bale": "بله",
        "rubika": "روبیکا",
        "web": "وب‌سایت",
        "manual": "دستی",
        "card_to_card": "کارت‌به‌کارت",
        "pardakhtyar": "پرداخت‌یار",
        "sandbox": "آزمایشی",
    }
    CURRENCY = {
        "irr": "ریال",
        "usd": "دلار",
        "eur": "یورو",
    }
