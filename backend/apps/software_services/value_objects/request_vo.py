from enum import StrEnum


class SoftwareRequestMessageVO(StrEnum):
    SENT = "درخواستت با موفقیت ثبت شد. تیم ما پس از بررسی از اطلاعات تماس ثبت‌شده باهات ارتباط می‌گیره."
    BOT_DETECTED = "ثبت درخواست امکان‌پذیر نبود. لطفاً فرم را دوباره ارسال کنید."
    INVALID_PHONE = "شماره تماس معتبر وارد کنید."
    INVALID_REFERENCE_URL = "لینک نمونه کار باید با HTTPS شروع شود."
    INVALID_DETAILS = "لطفاً توضیحات پروژه را کامل‌تر وارد کنید (حداقل ۲۰ کاراکتر)."
    INVALID_EMAIL = "ایمیل معتبر وارد کنید."
    INVALID_CATEGORY = "نوع خدمت یا بازه انتخاب‌شده معتبر نیست."
    INVALID_TITLE = "نام، عنوان و توضیحات پروژه را کامل وارد کنید."
    PRIVACY = "اطلاعات تماس فقط برای بررسی درخواست و پیگیری پروژه استفاده می‌شود."


class SoftwareRequestRouteVO(StrEnum):
    NAMESPACE = "software_services"
    LANDING = "index"
    PATH = "software-development/"
    REVERSE = "software_services:index"


class SoftwareRequestTemplateVO(StrEnum):
    LANDING = "web/software_services/landing.html"


class SoftwareRequestSeoVO(StrEnum):
    TITLE = "توسعه نرم‌افزار اختصاصی | طراحی سایت، اپلیکیشن و ربات"
    DESCRIPTION = "طراحی و توسعه وب‌سایت، وب‌اپلیکیشن، اپلیکیشن موبایل، ربات تلگرام و سامانه‌های اختصاصی. درخواست پروژه خود را ثبت کنید."
