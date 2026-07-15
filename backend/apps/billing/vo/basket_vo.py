from enum import StrEnum


class BasketMetadataVO(StrEnum):
    KIND_KEY = "kind"
    KIND_VALUE = "basket"
    DISCOUNT_CODE_KEY = "discount_code"
    DISCOUNT_ID_KEY = "discount_id"


class BasketWebTemplateVO(StrEnum):
    BASKET = "web/billing/basket.html"
    CHECKOUT = "web/billing/checkout.html"
    CARD_TO_CARD = "web/billing/card_to_card.html"


class BasketWebPathVO(StrEnum):
    BASKET = "basket/"
    ADD_ITEM = "basket/items/add/"
    REMOVE_ITEM = "basket/items/<uuid:item_id>/remove/"
    CLEAR = "basket/clear/"
    APPLY_DISCOUNT = "basket/discount/apply/"
    REMOVE_DISCOUNT = "basket/discount/remove/"
    CHECKOUT = "checkout/"
    START_PAYMENT = "checkout/payment/start/"
    PAYMENT_DETAIL = "checkout/payment/<uuid:payment_id>/"
    UPLOAD_RECEIPT = "checkout/payment/<uuid:payment_id>/receipt/"


class BasketWebRouteNameVO(StrEnum):
    BASKET = "basket"
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"
    CLEAR = "clear"
    APPLY_DISCOUNT = "apply_discount"
    REMOVE_DISCOUNT = "remove_discount"
    CHECKOUT = "checkout"
    START_PAYMENT = "start_payment"
    PAYMENT_DETAIL = "payment_detail"
    UPLOAD_RECEIPT = "upload_receipt"


class BasketWebReverseNameVO(StrEnum):
    BASKET = "billing_web:basket"
    ADD_ITEM = "billing_web:add_item"
    REMOVE_ITEM = "billing_web:remove_item"
    CLEAR = "billing_web:clear"
    APPLY_DISCOUNT = "billing_web:apply_discount"
    REMOVE_DISCOUNT = "billing_web:remove_discount"
    CHECKOUT = "billing_web:checkout"
    START_PAYMENT = "billing_web:start_payment"
    PAYMENT_DETAIL = "billing_web:payment_detail"
    UPLOAD_RECEIPT = "billing_web:upload_receipt"


class BasketWebMessageVO(StrEnum):
    EMPTY = "سبد خرید شما خالی است."
    ITEM_ADDED = "دوره به سبد خرید اضافه شد."
    ITEM_ALREADY_EXISTS = "این دوره از قبل در سبد خرید شما قرار دارد."
    ITEM_REMOVED = "دوره از سبد خرید حذف شد."
    CLEARED = "سبد خرید پاک شد."
    DISCOUNT_APPLIED = "کد تخفیف با موفقیت اعمال شد."
    DISCOUNT_REMOVED = "کد تخفیف حذف شد."
    PAYMENT_CREATED = "اطلاعات پرداخت آماده شد. پس از انتقال وجه، تصویر رسید را ارسال کنید."
    RECEIPT_UPLOADED = "رسید شما ثبت شد و در انتظار بررسی مدیر است."
    FREE_ORDER_COMPLETED = "ثبت‌نام دوره‌های رایگان با موفقیت انجام شد."
    INVALID_ACTION = "درخواست انجام‌شده معتبر نیست."
    BASKET_LOCKED = "تا زمان بررسی رسید فعلی، امکان تغییر این سبد وجود ندارد."
    COURSE_UNAVAILABLE = "یکی از دوره‌های سبد دیگر برای خرید در دسترس نیست."
    ALREADY_ENROLLED = "شما قبلاً در یکی از دوره‌های این سبد ثبت‌نام کرده‌اید."
    PAYMENT_METHOD_UNAVAILABLE = "درگاه پرداخت آنلاین در حال حاضر فعال نیست."
    ORDER_NOT_FOUND = "سبد خرید معتبر پیدا نشد."
    MIXED_CURRENCY = "دوره‌هایی با واحد پول متفاوت را نمی‌توان در یک سبد قرار داد."
    RECEIPT_INVALID = "اطلاعات رسید معتبر نیست."


class BasketWebFieldVO(StrEnum):
    COURSE_ID = "course_id"
    CODE = "code"
    PROVIDER = "provider"
    RECEIPT_FILE = "receipt_file"
    TRACKING_CODE = "tracking_code"
    PAYER_CARD_LAST4 = "payer_card_last4"
    PAID_AMOUNT = "paid_amount"
    NOTE = "note"


class BasketWebPlaceholderVO(StrEnum):
    DISCOUNT_CODE = "کد تخفیف"
    TRACKING_CODE = "کد رهگیری تراکنش"
    CARD_LAST4 = "۴ رقم آخر کارت پرداخت‌کننده"
    PAID_AMOUNT = "مبلغ پرداخت‌شده"
    NOTE = "توضیحات تکمیلی (اختیاری)"


class BasketWebValidationVO(StrEnum):
    REQUIRED = "این فیلد الزامی است."
    DISCOUNT_REQUIRED = "کد تخفیف را وارد کنید."
    RECEIPT_REQUIRED = "تصویر رسید یا کد رهگیری را وارد کنید."
    INVALID_RECEIPT = "فقط فایل JPG، PNG یا PDF تا حجم ۵ مگابایت مجاز است."
    INVALID_CARD_LAST4 = "۴ رقم آخر کارت باید دقیقاً چهار رقم باشد."


class BasketWebProviderLabelVO(StrEnum):
    CARD_TO_CARD = "کارت‌به‌کارت"
    PARDAKHTYAR = "درگاه پرداخت آنلاین"


class BasketWebStatusLabelVO:
    PAYMENT = {
        "initiated": "ایجادشده",
        "pending_receipt": "در انتظار ارسال رسید",
        "pending_verification": "در انتظار بررسی مدیر",
        "receipt_rejected": "رسید رد شده",
        "succeeded": "پرداخت موفق",
        "failed": "پرداخت ناموفق",
        "cancelled": "لغوشده",
        "refunded": "بازگشت وجه",
    }
    RECEIPT = {
        "pending": "در انتظار بررسی",
        "approved": "تأییدشده",
        "rejected": "ردشده",
    }
