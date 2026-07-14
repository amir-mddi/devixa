from enum import StrEnum


class AdminPanelAppVO(StrEnum):
    NAMESPACE = "admin_panel"
    TEMPLATE_ROOT = "web/admin_panel"


class AdminPanelRouteVO(StrEnum):
    DASHBOARD = "dashboard"
    TICKETS = "tickets"
    TICKET_DETAIL = "ticket_detail"
    TICKET_REPLY = "ticket_reply"
    TICKET_CLOSE = "ticket_close"
    REVIEWS = "reviews"
    REVIEW_MODERATE = "review_moderate"
    BILLING = "billing"
    RECEIPT_REVIEW = "receipt_review"
    RECEIPT_FILE = "receipt_file"
    USERS = "users"
    USER_CREATE = "user_create"
    USER_EDIT = "user_edit"
    USER_TOGGLE = "user_toggle"
    USER_DELETE = "user_delete"
    COURSES = "courses"
    COURSE_CREATE = "course_create"
    COURSE_EDIT = "course_edit"
    COURSE_DELETE = "course_delete"
    COURSE_LESSON_CREATE = "course_lesson_create"
    ARTICLES = "articles"
    ARTICLE_CREATE = "article_create"
    ARTICLE_EDIT = "article_edit"
    ARTICLE_DELETE = "article_delete"
    DISCOUNTS = "discounts"
    DISCOUNT_CREATE = "discount_create"
    DISCOUNT_DELETE = "discount_delete"
    NOTIFICATIONS = "notifications"
    NOTIFICATION_CREATE = "notification_create"
    BOT_SETTINGS = "bot_settings"
    BOT_SETTING_DELETE = "bot_setting_delete"


class AdminPanelMessageVO(StrEnum):
    PERMISSION_DENIED = "شما اجازه دسترسی به پنل مدیریت را ندارید."
    OPERATION_FAILED = "انجام عملیات با خطا روبه‌رو شد. اطلاعات را بررسی کنید."
    USER_CREATED = "کاربر با موفقیت ایجاد شد."
    USER_UPDATED = "اطلاعات کاربر با موفقیت به‌روزرسانی شد."
    USER_STATUS_UPDATED = "وضعیت دسترسی کاربر تغییر کرد."
    USER_DELETED = "کاربر با موفقیت به‌صورت نرم حذف شد."
    CANNOT_DELETE_SELF = "نمی‌توانید حساب مدیر فعلی را حذف کنید."
    CANNOT_MANAGE_PRIVILEGED_USER = (
        "فقط مدیر کل می‌تواند حساب مدیران سطح بالا را مدیریت کند."
    )
    CANNOT_GRANT_PRIVILEGED_ACCESS = (
        "فقط مدیر کل می‌تواند دسترسی مدیریتی یا staff اعطا کند."
    )
    COURSE_CREATED = "دوره با موفقیت ایجاد شد."
    COURSE_UPDATED = "دوره با موفقیت به‌روزرسانی شد."
    COURSE_DELETED = "دوره با موفقیت غیرفعال شد."
    LESSON_CREATED = "جلسه جدید به دوره اضافه شد."
    ARTICLE_CREATED = "مطلب با موفقیت ایجاد شد."
    ARTICLE_UPDATED = "مطلب با موفقیت به‌روزرسانی شد."
    ARTICLE_DELETED = "مطلب با موفقیت حذف شد."
    ARTICLE_CREATE_TITLE = "ایجاد مطلب جدید"
    ARTICLE_EDIT_TITLE = "ویرایش مطلب"
    ARTICLE_CREATE_SUBMIT = "ایجاد مطلب"
    ARTICLE_EDIT_SUBMIT = "ذخیره تغییرات"
    TICKET_REPLIED = "پاسخ برای کاربر ثبت شد."
    TICKET_CLOSED = "تیکت بسته شد."
    REVIEW_UPDATED = "وضعیت نظر کاربر به‌روزرسانی شد."
    RECEIPT_UPDATED = "وضعیت رسید پرداخت به‌روزرسانی شد."
    DISCOUNT_CREATED = "کد تخفیف با موفقیت ایجاد شد."
    DISCOUNT_DELETED = "کد تخفیف غیرفعال شد."
    NOTIFICATION_SENT = "اعلان برای کاربران متصل ارسال شد."
    NOTIFICATION_SCHEDULED = "اعلان برای زمان انتخاب‌شده برنامه‌ریزی شد."
    BOT_SETTINGS_UPDATED = "تنظیمات ربات با موفقیت ذخیره شد."
    BOT_SETTING_RESET = "تنظیم انتخاب‌شده به مقدار محیط یا پیش‌فرض بازگردانده شد."
    CANNOT_DEACTIVATE_SELF = "نمی‌توانید حساب مدیر فعلی را غیرفعال کنید."


class AdminPanelProviderVO:
    BOT_SETTING_LABELS = {
        "telegram": "تلگرام",
        "bale": "بله",
        "rubika": "روبیکا",
        "channel_sync": "همگام‌سازی کانال",
        "channel_member_sync": "همگام‌سازی اعضا",
        "commerce_bot": "تنظیمات فروش",
    }

    @classmethod
    def choices(cls, providers):
        return tuple(
            (provider, cls.BOT_SETTING_LABELS.get(provider, provider))
            for provider in providers
        )
