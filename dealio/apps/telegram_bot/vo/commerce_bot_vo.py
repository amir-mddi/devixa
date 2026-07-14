from __future__ import annotations

from dealio.apps.common.project_config import get_project_name


class TelegramBotLanguageVO:
    EN = "en"
    FA = "fa"
    SUPPORTED = {EN, FA}


class TelegramBotCallbackVO:
    MAIN_MENU = "menu:main"
    LINK = "menu:link"
    ACCOUNT = "menu:account"
    VERIFY_EMAIL = "menu:verify_email"
    VERIFY_PHONE = "menu:verify_phone"
    FORGOT_PASSWORD = "menu:forgot_password"
    CREATE_USER = "menu:create_user"
    WEBAPP = "menu:webapp"
    LANGUAGE = "menu:language"
    LANG_EN = "lang:en"
    LANG_FA = "lang:fa"
    HELP = "menu:help"
    COURSES = "c:l:1"
    MY_COURSES = "e:mine"
    MY_ORDERS = "o:mine"
    REVIEW_QUEUE = "r:q"
    PAYMENT_QUEUE = "pay:q"
    UNLINK_ASK = "menu:unlink_ask"
    UNLINK_CONFIRM = "menu:unlink_confirm"
    CANCEL = "menu:cancel"
    CHANNELS = "menu:channels"
    BOT_SETTINGS = "bs:menu"
    ADMIN_NOTIFICATION = "ntf:menu"
    ADMIN_NOTIFICATION_START = "ntf:start"
    ADMIN_NOTIFICATION_CONFIRM = "ntf:confirm"
    ADMIN_NOTIFICATION_CONFIRM_NOW = "ntf:confirm_now"
    ADMIN_NOTIFICATION_SCHEDULE = "ntf:schedule"
    DISCOUNTS = "dsc:menu"
    DISCOUNT_CREATE = "dsc:create"
    DISCOUNT_TYPE_PERCENT = "dsc:type:percent"
    DISCOUNT_TYPE_AMOUNT = "dsc:type:amount"
    DISCOUNT_SCOPE_ALL = "dsc:scope:all"
    DISCOUNT_USAGE_LIMIT_UNLIMITED = "dsc:limit:none"
    DISCOUNT_USAGE_LIMIT_CUSTOM = "dsc:limit:set"
    SUPPORT = "sup:menu"
    SUPPORT_NEW = "sup:new"
    SUPPORT_QUEUE = "sup:q"


class TelegramBotStateVO:
    LINK_METHOD = "link_method"
    LINK_EMAIL = "link_email"
    LINK_PHONE = "link_phone"
    LINK_CODE = "link_code"
    VERIFY_EMAIL_CODE = "verify_email_code"
    VERIFY_PHONE_METHOD = "verify_phone_method"
    VERIFY_PHONE_CODE = "verify_phone_code"
    FORGOT_PASSWORD_METHOD = "forgot_password_method"
    FORGOT_PASSWORD_EMAIL = "forgot_password_email"
    FORGOT_PASSWORD_PHONE = "forgot_password_phone"
    CREATE_USERNAME = "create_user_username"
    CREATE_EMAIL = "create_user_email"
    CREATE_PHONE = "create_user_phone"
    CREATE_FIRST_NAME = "create_user_first_name"
    CREATE_LAST_NAME = "create_user_last_name"
    CREATE_CONFIRM = "create_user_confirm"
    UNLINK_CONFIRM = "unlink_confirm"
    REVIEW_RATING = "course_review_rating"
    REVIEW_TITLE = "course_review_title"
    REVIEW_COMMENT = "course_review_comment"
    COURSE_TITLE = "admin_course_title"
    COURSE_SHORT_DESCRIPTION = "admin_course_short_description"
    COURSE_DESCRIPTION = "admin_course_description"
    COURSE_PRICE = "admin_course_price"
    COURSE_DURATION = "admin_course_duration"
    COURSE_LEVEL = "admin_course_level"
    COURSE_PUBLISH = "admin_course_publish"
    LESSON_TITLE = "admin_lesson_title"
    LESSON_DESCRIPTION = "admin_lesson_description"
    LESSON_CONTENT = "admin_lesson_content"
    LESSON_VIDEO_URL = "admin_lesson_video_url"
    LESSON_DURATION = "admin_lesson_duration"
    LESSON_POSITION = "admin_lesson_position"
    LESSON_PREVIEW = "admin_lesson_preview"
    PAYMENT_RECEIPT_TRACKING = "payment_receipt_tracking"
    BOT_SETTING_VALUE = "bot_setting_value"
    BOT_SETTING_EMAIL_CODE = "bot_setting_email_code"
    COURSE_EDIT_VALUE = "admin_course_edit_value"
    ADMIN_NOTIFICATION_MESSAGE = "admin_notification_message"
    ADMIN_NOTIFICATION_EMAIL_CODE = "admin_notification_email_code"
    ADMIN_NOTIFICATION_SCHEDULE_AT = "admin_notification_schedule_at"
    SUPPORT_MESSAGE = "support_message"
    SUPPORT_REPLY = "support_reply"
    DISCOUNT_CREATE = "discount_create"
    DISCOUNT_CODE = "discount_code"
    DISCOUNT_VALUE = "discount_value"
    DISCOUNT_USAGE_LIMIT = "discount_usage_limit"
    CHECKOUT_DISCOUNT_CODE = "checkout_discount_code"


class TelegramBotButtonKeyVO:
    LINK = "link"
    LINK_BY_EMAIL = "link_by_email"
    LINK_BY_PHONE = "link_by_phone"
    ACCOUNT = "account"
    VERIFY_EMAIL = "verify_email"
    VERIFY_PHONE = "verify_phone"
    VERIFY_PHONE_SMS = "verify_phone_sms"
    VERIFY_PHONE_TELEGRAM = "verify_phone_telegram"
    FORGOT_PASSWORD = "forgot_password"
    FORGOT_BY_EMAIL = "forgot_by_email"
    FORGOT_BY_PHONE = "forgot_by_phone"
    CREATE_USER = "create_user"
    WEBAPP = "webapp"
    LANGUAGE = "language"
    UNLINK = "unlink"
    HELP = "help"
    ARTICLES = "articles"
    ADMIN_ARTICLES = "admin_articles"
    COURSES = "courses"
    MY_COURSES = "my_courses"
    MY_ORDERS = "my_orders"
    REVIEW_QUEUE = "review_queue"
    PAYMENT_QUEUE = "payment_queue"
    ADMIN_COURSES = "admin_courses"
    CREATE_COURSE = "create_course"
    MAIN_MENU = "main_menu"
    CANCEL = "cancel"
    CHANNELS = "channels"
    BOT_SETTINGS = "bot_settings"
    ADMIN_NOTIFICATION = "admin_notification"
    DISCOUNTS = "discounts"
    SUPPORT = "support"
    SUPPORT_QUEUE = "support_queue"
    YES_UNLINK = "yes_unlink"
    CONFIRM_CREATE = "confirm_create"


class TelegramBotButtonTextVO:
    LANGUAGE_BUTTONS = {
        TelegramBotLanguageVO.EN: "🇬🇧 English",
        TelegramBotLanguageVO.FA: "🇮🇷 فارسی",
    }

    BUTTONS = {
        TelegramBotLanguageVO.EN: {
            TelegramBotButtonKeyVO.LINK: "🔗 Link account",
            TelegramBotButtonKeyVO.LINK_BY_EMAIL: "📧 Connect by email",
            TelegramBotButtonKeyVO.LINK_BY_PHONE: "📱 Connect by phone",
            TelegramBotButtonKeyVO.ACCOUNT: "👤 My account",
            TelegramBotButtonKeyVO.VERIFY_EMAIL: "✅ Verify email",
            TelegramBotButtonKeyVO.VERIFY_PHONE: "📱 Verify phone",
            TelegramBotButtonKeyVO.VERIFY_PHONE_SMS: "✉️ Send SMS code",
            TelegramBotButtonKeyVO.VERIFY_PHONE_TELEGRAM: "📲 Share Telegram phone",
            TelegramBotButtonKeyVO.FORGOT_PASSWORD: "🔐 Forgot password",
            TelegramBotButtonKeyVO.FORGOT_BY_EMAIL: "📧 Recover by email",
            TelegramBotButtonKeyVO.FORGOT_BY_PHONE: "📱 Recover by phone",
            TelegramBotButtonKeyVO.CREATE_USER: "➕ Create user",
            TelegramBotButtonKeyVO.WEBAPP: "🌐 Open app",
            TelegramBotButtonKeyVO.LANGUAGE: "🌍 Language",
            TelegramBotButtonKeyVO.UNLINK: "🚪 Unlink",
            TelegramBotButtonKeyVO.HELP: "❓ Help",
            TelegramBotButtonKeyVO.CHANNELS: "📣 Channels",
            TelegramBotButtonKeyVO.BOT_SETTINGS: "⚙️ Bot settings",
            TelegramBotButtonKeyVO.ADMIN_NOTIFICATION: "📣 Send notification",
            TelegramBotButtonKeyVO.DISCOUNTS: "🏷 Discounts",
            TelegramBotButtonKeyVO.SUPPORT: "💬 Support",
            TelegramBotButtonKeyVO.SUPPORT_QUEUE: "🎧 Support tickets",
            TelegramBotButtonKeyVO.ARTICLES: "📰 News & weblog",
            TelegramBotButtonKeyVO.ADMIN_ARTICLES: "🛠 Manage articles",
            TelegramBotButtonKeyVO.COURSES: "📚 Courses",
            TelegramBotButtonKeyVO.MY_COURSES: "🎓 My courses",
            TelegramBotButtonKeyVO.MY_ORDERS: "🧾 My orders",
            TelegramBotButtonKeyVO.REVIEW_QUEUE: "🛡 Review queue",
            TelegramBotButtonKeyVO.PAYMENT_QUEUE: "💳 Payment queue",
            TelegramBotButtonKeyVO.ADMIN_COURSES: "🧑‍🏫 Admin courses",
            TelegramBotButtonKeyVO.CREATE_COURSE: "➕ Create course",
            TelegramBotButtonKeyVO.MAIN_MENU: "⬅️ Main menu",
            TelegramBotButtonKeyVO.CANCEL: "Cancel",
            TelegramBotButtonKeyVO.YES_UNLINK: "✅ Yes, unlink",
            TelegramBotButtonKeyVO.CONFIRM_CREATE: "✅ Create user",
        },
        TelegramBotLanguageVO.FA: {
            TelegramBotButtonKeyVO.LINK: "🔗 اتصال حساب",
            TelegramBotButtonKeyVO.LINK_BY_EMAIL: "📧 اتصال با ایمیل",
            TelegramBotButtonKeyVO.LINK_BY_PHONE: "📱 اتصال با موبایل",
            TelegramBotButtonKeyVO.ACCOUNT: "👤 حساب من",
            TelegramBotButtonKeyVO.VERIFY_EMAIL: "✅ تأیید ایمیل",
            TelegramBotButtonKeyVO.VERIFY_PHONE: "📱 تأیید موبایل",
            TelegramBotButtonKeyVO.VERIFY_PHONE_SMS: "✉️ ارسال کد پیامکی",
            TelegramBotButtonKeyVO.VERIFY_PHONE_TELEGRAM: "📲 اشتراک شماره تلگرام",
            TelegramBotButtonKeyVO.FORGOT_PASSWORD: "🔐 فراموشی رمز عبور",
            TelegramBotButtonKeyVO.FORGOT_BY_EMAIL: "📧 بازیابی با ایمیل",
            TelegramBotButtonKeyVO.FORGOT_BY_PHONE: "📱 بازیابی با موبایل",
            TelegramBotButtonKeyVO.CREATE_USER: "➕ ساخت کاربر",
            TelegramBotButtonKeyVO.WEBAPP: "🌐 باز کردن برنامه",
            TelegramBotButtonKeyVO.LANGUAGE: "🌍 زبان",
            TelegramBotButtonKeyVO.UNLINK: "🚪 قطع اتصال",
            TelegramBotButtonKeyVO.HELP: "❓ راهنما",
            TelegramBotButtonKeyVO.CHANNELS: "📣 کانال‌ها",
            TelegramBotButtonKeyVO.BOT_SETTINGS: "⚙️ تنظیمات بات",
            TelegramBotButtonKeyVO.ADMIN_NOTIFICATION: "📣 ارسال اعلان",
            TelegramBotButtonKeyVO.DISCOUNTS: "🏷 تخفیف‌ها",
            TelegramBotButtonKeyVO.SUPPORT: "💬 پشتیبانی",
            TelegramBotButtonKeyVO.SUPPORT_QUEUE: "🎧 مدیریت تیکت‌ها",
            TelegramBotButtonKeyVO.ARTICLES: "📰 اخبار و وبلاگ",
            TelegramBotButtonKeyVO.ADMIN_ARTICLES: "🛠 مدیریت مطالب",
            TelegramBotButtonKeyVO.COURSES: "📚 دوره‌ها",
            TelegramBotButtonKeyVO.MY_COURSES: "🎓 دوره‌های من",
            TelegramBotButtonKeyVO.MY_ORDERS: "🧾 سفارش‌های من",
            TelegramBotButtonKeyVO.REVIEW_QUEUE: "🛡 بررسی دیدگاه‌ها",
            TelegramBotButtonKeyVO.PAYMENT_QUEUE: "💳 بررسی پرداخت‌ها",
            TelegramBotButtonKeyVO.ADMIN_COURSES: "🧑‍🏫 مدیریت دوره‌ها",
            TelegramBotButtonKeyVO.CREATE_COURSE: "➕ ساخت دوره",
            TelegramBotButtonKeyVO.MAIN_MENU: "⬅️ منوی اصلی",
            TelegramBotButtonKeyVO.CANCEL: "لغو",
            TelegramBotButtonKeyVO.YES_UNLINK: "✅ بله، قطع اتصال",
            TelegramBotButtonKeyVO.CONFIRM_CREATE: "✅ ساخت کاربر",
        },
    }


class TelegramBotAliasVO:
    LANGUAGE_EN_ALIASES = {"english", "en"}
    LANGUAGE_FA_ALIASES = {"فارسی", "farsi", "fa", "persian"}
    CANCEL_ALIASES = {"cancel", "لغو"}
    MAIN_MENU_ALIASES = {"main menu", "menu", "منوی اصلی"}
    YES_UNLINK_ALIASES = {"yes unlink", "yes", "unlink", "بله حذف اتصال", "بله قطع اتصال"}
    CREATE_CONFIRM_ALIASES = {"create user", "create", "yes create", "confirm", "تایید", "ساخت کاربر"}
    YES_ALIASES = {"yes", "y", "true", "1", "publish", "preview", "بله", "آره", "اره", "بلی"}
    NO_ALIASES = {"no", "n", "false", "0", "draft", "نه", "خیر"}
    MENU_BUTTON_ALIASES = {
        TelegramBotButtonKeyVO.LINK: {"link account", "اتصال حساب"},
        TelegramBotButtonKeyVO.LINK_BY_EMAIL: {"connect by email", "link by email", "اتصال با ایمیل"},
        TelegramBotButtonKeyVO.LINK_BY_PHONE: {"connect by phone", "link by phone", "connect by mobile", "اتصال با موبایل", "اتصال با شماره موبایل"},
        TelegramBotButtonKeyVO.ACCOUNT: {"my account", "account", "حساب من"},
        TelegramBotButtonKeyVO.VERIFY_EMAIL: {"verify email", "email verification", "تایید ایمیل", "تأیید ایمیل"},
        TelegramBotButtonKeyVO.VERIFY_PHONE: {"verify phone", "phone verification", "verify mobile", "تایید موبایل", "تأیید موبایل", "تایید شماره موبایل", "تأیید شماره موبایل"},
        TelegramBotButtonKeyVO.VERIFY_PHONE_SMS: {"send sms code", "verify by sms", "ارسال کد پیامکی", "تایید با پیامک", "تأیید با پیامک"},
        TelegramBotButtonKeyVO.VERIFY_PHONE_TELEGRAM: {"share telegram phone", "share phone", "اشتراک شماره تلگرام", "اشتراک موبایل"},
        TelegramBotButtonKeyVO.FORGOT_PASSWORD: {"forgot password", "فراموشی رمز عبور"},
        TelegramBotButtonKeyVO.FORGOT_BY_EMAIL: {"recover by email", "email recovery", "بازیابی با ایمیل"},
        TelegramBotButtonKeyVO.FORGOT_BY_PHONE: {"recover by phone", "phone recovery", "بازیابی با موبایل", "بازیابی با شماره موبایل"},
        TelegramBotButtonKeyVO.CREATE_USER: {"create user", "ساخت کاربر"},
        TelegramBotButtonKeyVO.WEBAPP: {"open app", "web app", "باز کردن برنامه"},
        TelegramBotButtonKeyVO.LANGUAGE: {"language", "زبان"},
        TelegramBotButtonKeyVO.UNLINK: {"unlink", "قطع اتصال"},
        TelegramBotButtonKeyVO.HELP: {"help", "راهنما"},
        TelegramBotButtonKeyVO.CHANNELS: {"channels", "channel", "کانال", "کانال‌ها", "کانال ها"},
        TelegramBotButtonKeyVO.BOT_SETTINGS: {"bot settings", "settings", "تنظیمات بات", "تنظیمات"},
        TelegramBotButtonKeyVO.ADMIN_NOTIFICATION: {"send notification", "notification", "broadcast", "announcement", "ارسال اعلان", "اعلان", "پیام همگانی", "نوتیفیکیشن"},
        TelegramBotButtonKeyVO.DISCOUNTS: {"discounts", "discount", "coupon", "coupons", "تخفیف", "تخفیف‌ها", "کد تخفیف"},
        TelegramBotButtonKeyVO.SUPPORT: {"support", "ticket", "help desk", "پشتیبانی", "تیکت"},
        TelegramBotButtonKeyVO.SUPPORT_QUEUE: {"support tickets", "tickets", "support queue", "تیکت‌های پشتیبانی", "صف پشتیبانی", "مدیریت تیکت‌ها", "مدیریت تیکت ها"},
        TelegramBotButtonKeyVO.ARTICLES: {"articles", "news", "blog", "weblog", "اخبار", "وبلاگ", "اخبار و وبلاگ"},
        TelegramBotButtonKeyVO.ADMIN_ARTICLES: {"manage articles", "admin articles", "article admin", "مدیریت مطالب", "مدیریت اخبار", "مدیریت وبلاگ"},
        TelegramBotButtonKeyVO.COURSES: {"courses", "course", "دوره", "دوره‌ها", "دوره ها"},
        TelegramBotButtonKeyVO.MY_COURSES: {"my courses", "my course", "دوره‌های من", "دوره های من"},
        TelegramBotButtonKeyVO.MY_ORDERS: {"my orders", "orders", "سفارش‌های من", "سفارش های من"},
        TelegramBotButtonKeyVO.REVIEW_QUEUE: {"review queue", "reviews queue", "بررسی دیدگاه‌ها", "بررسی دیدگاه ها"},
        TelegramBotButtonKeyVO.PAYMENT_QUEUE: {"payment queue", "payments", "payment approvals", "بررسی پرداخت‌ها", "بررسی پرداخت ها", "پرداخت‌ها", "پرداخت ها"},
        TelegramBotButtonKeyVO.ADMIN_COURSES: {"admin courses", "manage courses", "course admin", "مدیریت دوره‌ها", "مدیریت دوره ها"},
        TelegramBotButtonKeyVO.CREATE_COURSE: {"create course", "new course", "ساخت دوره", "دوره جدید"},
    }


class TelegramBotIconKeyVO:
    WARNING = "warning"
    EDIT = "edit"
    SUCCESS = "success"
    STAR = "star"
    UNLOCKED = "unlocked"
    LOCKED = "locked"


class TelegramBotIconVO:
    """Central place for visual symbols used by Telegram bot presentation.

    Services and repositories should never hard-code icons directly. This keeps
    platform-specific UI copy in VO and makes it cheap to disable/replace icons.
    """

    ICONS = {
        TelegramBotIconKeyVO.WARNING: "⚠️",
        TelegramBotIconKeyVO.EDIT: "✏️",
        TelegramBotIconKeyVO.SUCCESS: "✅",
        TelegramBotIconKeyVO.STAR: "⭐",
        TelegramBotIconKeyVO.UNLOCKED: "🔓",
        TelegramBotIconKeyVO.LOCKED: "🔒",
    }

    @classmethod
    def get(cls, key: str) -> str:
        return cls.ICONS.get(key, "")

    @classmethod
    def prefix(cls, key: str, text: str, *, separator: str = " ") -> str:
        icon = cls.get(key)
        return f"{icon}{separator}{text}" if icon else text


class TelegramCommerceFeatureVO:
    """Commerce/domain configuration used by the bot orchestration layer.

    Keep business-model naming, field lists, clear markers and callback-facing
    values here. To change the bot from courses to another purchasable domain
    such as gym plans, change the feature VO plus repository adapter/logic;
    TelegramBotService should not need copy or icon edits.
    """

    PUBLIC_LIST_PAGE_SIZE = 5
    ADMIN_LIST_PAGE_SIZE = 5
    CLEAR_VALUE_MARKER = "-"
    ADMIN_NOTIFICATION_MAX_LENGTH = 3500
    SUPPORT_MESSAGE_MAX_LENGTH = 2500

    FIELD_TITLE = "title"
    FIELD_SHORT_DESCRIPTION = "short_description"
    FIELD_DESCRIPTION = "description"
    FIELD_PRICE = "price"
    FIELD_CURRENCY = "currency"
    FIELD_DURATION_MINUTES = "duration_minutes"
    FIELD_LEVEL = "level"
    FIELD_STATUS = "status"
    FIELD_IS_FEATURED = "is_featured"

    EDITABLE_FIELDS = [
        FIELD_TITLE,
        FIELD_SHORT_DESCRIPTION,
        FIELD_DESCRIPTION,
        FIELD_PRICE,
        FIELD_CURRENCY,
        FIELD_DURATION_MINUTES,
        FIELD_LEVEL,
        FIELD_STATUS,
        FIELD_IS_FEATURED,
    ]

    CHOICE_FIELDS = {
        FIELD_CURRENCY,
        FIELD_LEVEL,
        FIELD_STATUS,
        FIELD_IS_FEATURED,
    }

    BOOLEAN_TRUE_VALUE = "true"
    BOOLEAN_FALSE_VALUE = "false"
    CREATE_LEVEL_FIELD = "level"
    CREATE_PUBLISH_FIELD = "publish"
    CREATE_PREVIEW_FIELD = "preview"

    @classmethod
    def field_text_key(cls, field: str) -> str:
        return f"course_field_{field}"

    @classmethod
    def is_choice_field(cls, field: str) -> bool:
        return field in cls.CHOICE_FIELDS


class TelegramBotMessageTextVO:
    DEFAULT_USER_NAME = {
        TelegramBotLanguageVO.EN: "there",
        TelegramBotLanguageVO.FA: "کاربر",
    }
    LINK_EMAIL_SUBJECT = {
        TelegramBotLanguageVO.EN: "{provider_name} account link code",
        TelegramBotLanguageVO.FA: "کد اتصال حساب {provider_name}",
    }

    TEXTS = {
        TelegramBotLanguageVO.EN: {
            "choose_language": "Please choose your language / لطفاً زبان خود را انتخاب کنید:",
            "language_saved": "Language saved. Choose an action:",
            "canceled": "Canceled.",
            "use_buttons": "Please use the menu buttons below.",
            "unknown": "Unknown action. Use the buttons below.",
            "channels_title": "Join our official channels:",
            "channels_not_configured": "Channel links are not configured yet.",
            "telegram_channel": "Telegram channel",
            "bale_channel": "Bale channel",
            "rubika_channel": "Rubika channel",
            "private_only": "Please message me privately to manage your account.",
            "menu_linked": "Welcome back, <b>{name}</b>!\n\nChoose an action:",
            "menu_guest": "Welcome to {project_name} bot.\n\nChoose an action:",
            "not_linked": "Your account is not linked yet. Tap <b>Link account</b> below.",
            "already_linked": "Your messenger account is already linked.",
            "link_choose": "Choose how to connect your {project_name} account:",
            "link_email_prompt": "Send the email address registered on your account.\n\nExample: <code>you@example.com</code>",
            "link_phone_prompt": "Send the Iranian mobile number registered on your account.\n\nExample: <code>09123456789</code>",
            "link_prompt": "Send the email address registered on your account.\n\nExample: <code>you@example.com</code>",
            "invalid_email": "That does not look like a valid email. Please send only your email address.",
            "invalid_link_phone": "That phone number is invalid. Send an Iranian mobile number such as <code>09123456789</code>.",
            "link_email_code_sent": "If an active account exists for this email, a 6-digit connection code was sent or the previous code is still valid.\n\nSend the 6-digit code here.",
            "link_phone_code_sent": "If an active account exists for this phone number, a 6-digit SMS connection code was sent or the previous code is still valid.\n\nSend the 6-digit code here.",
            "link_code_sent": "If an active account exists for this email, a 6-digit connection code was sent or the previous code is still valid.\n\nSend the 6-digit code here.",
            "link_usage": "Use <code>/link email@example.com</code> or <code>/link 09123456789</code>, or use the Link account button.",
            "code_only": "Please send the 6-digit code only. Example: <code>123456</code>",
            "invalid_link_code": "Invalid or expired link code. Try again, or cancel and request a new code.",
            "linked_success": "Your messenger account is linked successfully.",
            "verify_already": "Your email is already verified.",
            "verify_sent": "I sent a 6-digit email verification code to your linked email. Send the code here.",
            "verify_code_active": "Your previous email verification code is still active. Send that 6-digit code here.",
            "verify_success": "✅ Email verified successfully.",
            "verify_invalid": "Invalid or expired verification code. Try again or request a new code.",
            "phone_verify_choose": "Choose how to verify your phone number. You can receive an SMS code or securely share your own Telegram phone number.",
            "phone_verify_already": "Your phone number is already verified.",
            "phone_verify_required": "No phone number is registered for this account. Share your own Telegram phone number, or add one in the app first.",
            "phone_verify_inactive": "This account is inactive and its phone number cannot be verified.",
            "phone_verify_sent": "I sent a 6-digit SMS verification code to <code>{phone}</code>. Send the code here.",
            "phone_verify_code_active": "The previous SMS verification code for <code>{phone}</code> is still active. Send that code here.",
            "phone_verify_share_prompt": "Tap <b>Share Telegram phone</b> below. Telegram will ask permission before sharing your own contact.",
            "phone_verify_contact_not_own": "For security, share your own Telegram contact using the button below. Forwarded or another person's contact is not accepted.",
            "phone_verify_contact_invalid": "Telegram returned an invalid phone number. Check the number on your Telegram account and try again.",
            "phone_verify_phone_in_use": "This phone number is already registered for another account.",
            "phone_verify_success": "✅ Phone number verified successfully.",
            "phone_verify_invalid": "Invalid or expired phone verification code. Try again or request a new code.",
            "forgot_choose": "Choose how you want to receive the password recovery code:",
            "forgot_email_prompt": "Send your account email address.",
            "forgot_phone_prompt": "Send your account phone number. Example: <code>09123456789</code>",
            "forgot_invalid_phone": "That phone number is invalid. Send an Iranian mobile number such as <code>09123456789</code>.",
            "forgot_email_sent": "If this account exists, an email recovery code was sent or the previous code is still active.\n\nFor security, set the new password only in the app/API reset form.",
            "forgot_phone_sent": "If this account exists and its phone is verified, an SMS recovery code was sent or the previous code is still active.\n\nFor security, set the new password only in the app/API reset form.",
            "forgot_phone_unavailable": "This linked account has no verified phone number. Verify the phone first or recover by email.",
            "forgot_prompt": "Send your account email address, and I will send a password recovery code if it exists.",
            "forgot_sent": "If this account exists, a password recovery code has been sent or the previous code is still active.\n\nFor security, do not send your new password in Telegram. Use the app/API reset form with the code.",
            "unlink_ask": "Are you sure you want to unlink this Telegram account?",
            "unlink_choose": "Choose <b>Yes, unlink</b> or <b>Cancel</b> from the keyboard below.",
            "unlinked": "Your Telegram account has been unlinked.",
            "webapp_missing": "Web app URL is not configured yet.",
            "webapp_open": "Open the app here: <a href=\"{url}\">Open app</a>",
            "admin_only": "Only a linked admin can use this Telegram admin action.",
            "bot_settings_title": "⚙️ Bot runtime settings",
            "bot_settings_hint": "Tap a provider, choose a setting, then send the new value. The value is saved in the database only. Secrets are masked.",
            "bot_settings_provider_title": "⚙️ Runtime settings: {provider}",
            "bot_settings_not_configured": "not configured",
            "bot_settings_choose_key": "Choose a setting to edit:",
            "bot_settings_edit_title": "✏️ Edit setting",
            "bot_settings_current_value": "Current value",
            "bot_settings_source": "Source",
            "bot_settings_type": "Type",
            "bot_settings_choices": "Allowed values",
            "bot_settings_write_target_prompt": "This value will be saved in the database only.",
            "bot_settings_target_db": "Database only",
            "bot_settings_target_env": ".env only",
            "bot_settings_target_both": "Database + .env",
            "bot_settings_send_value_prompt": "Send the new value for <b>{label}</b>.\n\nIt will be saved in the database only. Env fallback: <code>{env_name}</code>\n\nSend <code>-</code> to clear optional values. For secrets, send the real new value; the bot will not show it back. After this, a confirmation code will be sent to your email.",
            "bot_settings_value_saved": "✅ Setting updated successfully after email confirmation.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>\nSaved to: <code>{target}</code>",
            "bot_settings_invalid_value": "⚠️ Invalid value: {error}\n\nPlease send a valid value again or cancel.",
            "bot_settings_pending_missing": "The edit session expired. Please choose the setting again.",
            "bot_settings_env_only_warning": "Editing .env from Telegram is disabled. Runtime bot settings are saved in the database only.",
            "bot_settings_db_only_notice": "For security, Telegram can update only the database value. .env editing is disabled.",
            "bot_settings_edit_value_button": "✏️ Edit database value",
            "bot_settings_custom_value_button": "✍️ Enter custom value",
            "bot_settings_delete_db_value_button": "🗑 Delete database value",
            "bot_settings_delete_confirm": "Delete the database override for <b>{label}</b>?\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>\n\nAfter deletion, the bot will fall back to env/default value.",
            "bot_settings_db_value_deleted": "✅ Database value deleted.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>",
            "bot_settings_db_value_not_found": "No database value existed for this setting. Env/default fallback is still active.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>",
            "confirm_delete_button": "✅ Yes, delete",
            "bot_settings_email_code_sent": "I sent a 6-digit confirmation code to <code>{email}</code>. Send that code here within {minutes} minutes to save the change.",
            "bot_settings_delete_email_code_sent": "I sent a 6-digit confirmation code to <code>{email}</code>. Send that code here within {minutes} minutes to delete the database value.",
            "bot_settings_email_code_invalid": "Invalid or expired confirmation code. Try again or cancel.",
            "bot_settings_email_missing": "Your linked admin account has no email address, so this setting cannot be changed from Telegram.",
            "bot_settings_email_send_failed": "Could not send the confirmation email: {error}",
            "bot_settings_env_write_disabled": "Editing .env values from Telegram is disabled. Please choose the database edit option again.",
            "admin_notification_title": "Admin notification",
            "discounts_title": "Discount codes",
            "discounts_hint": "Manage discounts step by step. You do not need to remember any command format.",
            "discounts_create_button": "Create discount",
            "discounts_empty": "No discount codes exist yet.",
            "discounts_list_count": "Total discounts: <code>{count}</code>",
            "discounts_item_text": "Code: <code>{code}</code>\nType: <code>{discount_type}</code>\nValue: <code>{value}</code>\nScope: <code>{scope}</code>\nUsage: <code>{used}</code>/<code>{limit}</code>",
            "discounts_create_prompt": "Step 1 of 5\nSend the discount code.\n\nExample: <code>DJANGO30</code>",
            "discounts_code_invalid": "Code is invalid. Use English letters, numbers, dash, or underscore. Example: <code>DJANGO30</code>",
            "discounts_type_prompt": "Step 2 of 5\nChoose discount type for <code>{code}</code>.",
            "discounts_type_percent_button": "Percent",
            "discounts_type_amount_button": "Fixed amount",
            "discounts_value_prompt_percent": "Step 3 of 5\nSend percent value for <code>{code}</code>.\n\nExample: <code>30</code> means 30% off.",
            "discounts_value_prompt_amount": "Step 3 of 5\nSend fixed discount amount for <code>{code}</code>.\n\nExample: <code>500000</code>",
            "discounts_value_invalid": "Discount value is invalid. Send a positive number. Percent must be between 1 and 100.",
            "discounts_scope_prompt": "Step 4 of 5\nChoose where this discount can be used.",
            "discounts_scope_all_button": "All courses",
            "discounts_scope_course_button": "Course: {title}",
            "discounts_usage_limit_prompt": "Step 5 of 5\nChoose usage limit for <code>{code}</code>.",
            "discounts_usage_unlimited_button": "Unlimited",
            "discounts_usage_custom_button": "Set limit",
            "discounts_usage_custom_prompt": "Send maximum usage count. Example: <code>100</code>",
            "discounts_usage_invalid": "Usage limit is invalid. Send a positive whole number.",
            "discounts_session_expired": "Discount creation session expired. Start again from discounts menu.",
            "discounts_created": "Discount created successfully.\n\nCode: <code>{code}</code>\nType: <code>{discount_type}</code>\nValue: <code>{value}</code>\nScope: <code>{scope}</code>\nUsage limit: <code>{usage_limit}</code>",
            "discounts_invalid_format": "Discount data is incomplete. Please use the step-by-step buttons.",
            "discounts_delete_button": "Delete",
            "discounts_deleted": "Discount deleted: <code>{code}</code>",
            "checkout_discount_prompt": "Send a discount code, or send <code>-</code> to continue without discount.",
            "checkout_discount_invalid": "Discount could not be applied: {error}\n\nSend another code or <code>-</code> to continue without discount.",
            "support_title": "Support",
            "support_hint": "Send a support ticket to admins. You can also view your recent tickets.",
            "support_new_button": "New ticket",
            "support_my_tickets_button": "My tickets",
            "support_queue_button": "Support queue",
            "support_prompt": "Send your support message now. An admin will receive it.",
            "support_empty": "Support message cannot be empty. Send a message or cancel.",
            "support_created": "Your support ticket was created. Ticket ID: <code>{ticket_id}</code>",
            "support_user_reply_prompt": "Send your reply for ticket <code>{ticket_id}</code>.",
            "support_reply_sent": "Reply sent.",
            "support_admin_queue_empty": "No open support tickets.",
            "support_admin_reply_button": "Reply",
            "support_admin_close_button": "Close",
            "support_admin_reply_prompt": "Send admin reply for ticket <code>{ticket_id}</code>.",
            "support_admin_replied": "Admin reply sent to user.",
            "support_closed": "Ticket closed.",
            "support_user_notification": "Support reply for ticket <code>{ticket_id}</code>:\n\n{message}",
            "support_admin_new_ticket_notice": "New support ticket <code>{ticket_id}</code> from <code>{user}</code>:\n\n{message}",
            "admin_notification_send_now_button": "Send now",
            "admin_notification_schedule_button": "Schedule",
            "admin_notification_schedule_prompt": "Send schedule time as <code>YYYY-MM-DD HH:MM</code>. Example: <code>2026-07-03 10:30</code>",
            "admin_notification_schedule_invalid": "Invalid date/time. Use <code>YYYY-MM-DD HH:MM</code>.",
            "admin_notification_scheduled_result": "Notification scheduled.\n\nID: <code>{id}</code>\nTime: <code>{scheduled_at}</code>\nRecipients now: <code>{count}</code>",
            "admin_notification_hint": "Send one message to all linked active Telegram bot users. Current recipients: <code>{count}</code>. Max length: <code>{max_length}</code> characters. Email confirmation is required before delivery.",
            "admin_notification_start_button": "Create notification",
            "admin_notification_prompt": "Send the notification text now. It will be shown to all linked active bot users after email confirmation.",
            "admin_notification_empty": "Notification text cannot be empty. Send a message or cancel.",
            "admin_notification_too_long": "Notification is too long. Max length is <code>{max_length}</code> characters. Send a shorter message or cancel.",
            "admin_notification_preview": "Preview for <code>{count}</code> recipients:\n\n{message}",
            "admin_notification_confirm_button": "Send after email verification",
            "admin_notification_edit_button": "Edit message",
            "admin_notification_email_subject": "Confirm bot notification",
            "admin_notification_email_code_sent": "I sent a 6-digit confirmation code to <code>{email}</code>. Send that code here within {minutes} minutes to deliver the notification.",
            "admin_notification_email_code_invalid": "Invalid or expired confirmation code. Try again or cancel.",
            "admin_notification_email_missing": "Your linked admin account has no email address, so the notification cannot be sent from Telegram.",
            "admin_notification_email_send_failed": "Could not send the confirmation email: {error}",
            "admin_notification_pending_missing": "The notification session expired. Start again from the admin notification menu.",
            "admin_notification_delivery_text": "<b>Announcement</b>\n\n{message}",
            "admin_notification_sent_result": "Notification delivery finished.\n\nRecipients: <code>{total}</code>\nDelivered: <code>{success}</code>\nFailed: <code>{failed}</code>",
            "admin_courses_empty": "No courses exist yet.",
            "course_create_start": "Create a new course. Send the course title first.",
            "course_short_description_prompt": "Send a short description for the course. Max 300 chars.",
            "course_description_prompt": "Send the full course description, or send <code>-</code> to skip.",
            "course_price_prompt": "Send the course price as a number. Use <code>0</code> for a free course.",
            "course_duration_prompt": "Send total course duration in minutes. Example: <code>120</code>",
            "course_level_prompt": "Send course level: <code>beginner</code>, <code>intermediate</code>, <code>advanced</code>, or <code>all_levels</code>.",
            "course_publish_prompt": "Publish now? Send <code>yes</code> to publish or <code>no</code> to keep it as draft.",
            "course_created": "✅ Course created successfully.",
            "course_status_updated": "✅ Course status updated.",
            "course_field_updated": "✅ Course field updated.",
            "course_edit_title": "✏️ Edit course: {title}",
            "course_edit_value_prompt": "Send new value for <b>{field}</b>.\n\nCurrent: <code>{current}</code>\n\nSend <code>-</code> to clear optional text fields.",
            "course_edit_choice_prompt": "Choose new value for <b>{field}</b>.\n\nCurrent: <code>{current}</code>",
            "course_edit_session_expired": "The course edit session expired. Choose the course field again.",
            "course_choice_session_expired": "This choice session expired. Start the course flow again.",
            "course_delete_confirm": "Are you sure you want to delete <b>{title}</b>?\n\nThis is a soft delete and the course will be hidden from users.",
            "course_deleted": "✅ Course deleted: <b>{title}</b>",
            "edit_course_button": "✏️ Edit course",
            "delete_course_button": "🗑 Delete course",
            "course_edit_back_button": "⬅️ Edit fields",
            "course_field_title": "Title",
            "course_field_short_description": "Short description",
            "course_field_description": "Description",
            "course_field_price": "Price",
            "course_field_currency": "Currency",
            "course_field_duration_minutes": "Duration",
            "course_field_level": "Level",
            "course_field_status": "Status",
            "course_field_is_featured": "Featured",
            "lesson_create_start": "Add a lesson to this course. Send the lesson title first.",
            "lesson_description_prompt": "Send lesson description, or send <code>-</code> to skip.",
            "lesson_content_prompt": "Send lesson content/text, or send <code>-</code> to skip.",
            "lesson_video_url_prompt": "Send video URL, or send <code>-</code> to skip.",
            "lesson_duration_prompt": "Send lesson duration in minutes. Example: <code>15</code>",
            "lesson_position_prompt": "Send lesson position number, or send <code>-</code> to auto-place at the end.",
            "lesson_preview_prompt": "Is this a free preview lesson? Send <code>yes</code> or <code>no</code>.",
            "lesson_created": "✅ Lesson added successfully.",
            "course_login_required": "Please link your account before buying courses, viewing enrollments, or writing reviews.",
            "courses_empty": "No published courses are available yet.",
            "my_courses_empty": "You do not have any active courses yet.",
            "orders_empty": "You do not have any orders yet.",
            "reviews_empty": "No approved reviews yet.",
            "review_rating_prompt": "Send a rating from 1 to 5 for this course.",
            "review_title_prompt": "Optional: send a short review title, or send <code>-</code> to skip.",
            "review_comment_prompt": "Now send your review comment. It will be visible only after admin approval.",
            "review_comment_too_short": "Please send at least 2 non-space characters for the review text.",
            "review_pending": "✅ Thanks! Your review is waiting for admin approval.",
            "review_queue_empty": "There are no pending reviews.",
            "payment_manual": "✅ Card-to-card payment was created. Upload/register the receipt code; admin approval is required before enrollment.",
            "payment_success": "✅ Payment succeeded. You are now enrolled in the course.",
            "payment_created": "✅ Order/payment created successfully.",
            "payment_receipt_button": "📎 Send receipt",
            "payment_receipt_prompt": "Send the receipt photo/document, or send the tracking/reference number as text.",
            "payment_receipt_saved": "✅ Receipt was registered and is waiting for admin verification.",
            "payment_receipt_saved_with_id": "{message}\nReceipt ID: <code>{receipt_id}</code>",
            "payment_receipt_admin_notified": "A new payment receipt was sent to admins for review.",
            "payment_receipt_unsupported_file": "Please send a receipt photo/document, or send the tracking/reference number as text.",
            "payment_queue_empty": "There are no pending payment receipts.",
            "payment_queue_heading": "<b>💳 Pending payment receipts</b>",
            "pending_payment_receipt_item": "\n<b>{order}</b>\nUser: <code>{user}</code>\nPayment: <code>{payment}</code>\nAmount: <code>{amount}</code>\nTracking: <code>{tracking}</code>\nSource: <code>{source}</code>",
            "view_receipt_button": "👁 View receipt",
            "back_to_payment_queue_button": "Back to payment queue",
            "admin_payment_approve_note": "Approved from Telegram bot.",
            "admin_payment_reject_note": "Rejected from Telegram bot.",
            "payment_receipt_moderated": "✅ Payment receipt <code>{receipt_id}</code> marked as <b>{status}</b>.",
            "order_payment_card_info": "Card: <code>{card}</code>\nAccount: <code>{account}</code>\nHolder: <code>{holder}</code>\nBank: <code>{bank}</code>\nIBAN: <code>{iban}</code>",
            "order_payment_receipt_hint": "After transfer, send the receipt photo/document here or register the receipt code.",
            "course_already_owned": "You already purchased this course.",
            "create_start": "Create a new app user.\n\nSend the username first.\nExample: <code>ali_ahmadi</code>",
            "create_email": "Now send the user Gmail address.\nExample: <code>user@gmail.com</code>",
            "create_phone": "Now send the phone number.\nExample: <code>09123456789</code>",
            "create_first_name": "Now send the first name in Persian.\nExample: <code>علی</code>",
            "create_last_name": "Now send the last name in Persian.\nExample: <code>احمدی</code>",
            "create_choose": "Choose <b>Create user</b> or <b>Cancel</b> from the keyboard below.",
            "create_expired": "The create-user session expired. Send the username again.",
            "create_duplicate": "A user with this username, email, or phone already exists. Start again with new data.",
            "create_done_followup": "I also sent a password setup/recovery code to the user's email. They can use the app forgot-password reset form to set their password.",
            "create_email_failed": "The user was created, but I could not send the password setup email. Use the app/admin panel forgot-password flow to send it again.",
            "link_usage": "Usage: <code>/link your-email@example.com</code>",
            "invalid_username_detail": "Invalid username: {error}\n\nSend the username again.",
            "username_exists": "This username already exists. Send another username.",
            "invalid_create_email_detail": "Invalid email: {error}\n\nSend a Gmail address again.",
            "email_exists": "This email already exists. Send another Gmail address.",
            "invalid_phone_detail": "Invalid phone number: {error}\n\nSend the phone number again.",
            "phone_exists": "This phone number already exists. Send another phone number.",
            "invalid_first_name_detail": "Invalid first name: {error}\n\nSend the first name again.",
            "invalid_last_name_detail": "Invalid last name: {error}\n\nSend the last name again.",
            "create_failed": "Could not create the user: {error}",
            "create_success": "✅ User created successfully.\n\nUsername: <code>{username}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\n\n{follow_up}",
            "create_confirm_text": "Please confirm this new user:\n\nUsername: <code>{username}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\nFirst name: <code>{first_name}</code>\nLast name: <code>{last_name}</code>\n\nNo password will be sent in Telegram. The user will set their password by email reset code.",
            "yes": "yes",
            "no": "no",
            "account_text": "<b>Your account</b>\nUsername: <code>{username}</code>\nFirst name: <code>{first_name}</code>\nLast name: <code>{last_name}</code>\nEmail: <code>{email}</code>\nPhone: <code>{phone}</code>\nEmail verified: <code>{email_verified}</code>\nPhone verified: <code>{phone_verified}</code>",
            "courses_heading": "<b>📚 Courses</b>",
            "course_list_item": "\n<b>{index}. {title}</b>{rating}\n{description}\nPrice: <code>{price}</code>",
            "view_course_button": "🔎 {title}",
            "prev_button": "⬅️ Prev",
            "next_button": "Next ➡️",
            "main_menu_button": "⬅️ Main menu",
            "course_detail_text": "<b>{title}</b>\n\n{description}\n\nLevel: <code>{level}</code>\nDuration: <code>{duration} min</code>\nLessons: <code>{lessons}</code>\nRating: <code>{rating}</code>\nPrice: <code>{price}</code>",
            "lessons_button": "🧩 Lessons",
            "reviews_button": "⭐ Reviews",
            "buy_button": "🛒 Buy / Enroll",
            "write_review_button": "✍️ Write review",
            "courses_back_button": "⬅️ Courses",
            "course_back_button": "⬅️ Course",
            "lessons_heading": "<b>🧩 {title} lessons</b>",
            "no_lessons": "No lessons are published for this course yet.",
            "lesson_item": "\n{lock} <b>{position}. {title}</b>\nDuration: <code>{duration} min</code>",
            "video_line": "Video: {url}",
            "reviews_heading": "<b>⭐ Approved reviews for {title}</b>",
            "review_item": "\n<b>{rating}/5{title}</b>\nBy: <code>{user}</code>\n{comment}",
            "my_courses_heading": "<b>🎓 My courses</b>",
            "enrollment_item": "\n<b>{title}</b>\nStatus: <code>{status}</code>\nEnrolled: <code>{enrolled_at}</code>",
            "open_course_button": "Open {title}",
            "my_orders_heading": "<b>🧾 My orders</b>",
            "order_item": "\n<b>{order_number}</b>\nCourses: <code>{courses}</code>\nStatus: <code>{status}</code>\nTotal: <code>{total}</code>",
            "review_saved_with_id": "{message}\nReview ID: <code>{review_id}</code>",
            "review_queue_heading": "<b>🛡 Pending course reviews</b>",
            "pending_review_item": "\n<b>{course}</b>\nUser: <code>{user}</code> | Rating: <code>{rating}/5</code>\n{comment}",
            "approve_button": "✅ Approve",
            "reject_button": "❌ Reject",
            "refresh_button": "Refresh",
            "list_page_indicator": "Page <code>{page}</code> of <code>{total_pages}</code> • Total items: <code>{total_count}</code>",
            "admin_review_note": "Moderated from Telegram bot.",
            "review_moderated": "✅ Review <code>{review_id}</code> marked as <b>{status}</b>.",
            "back_to_queue_button": "Back to queue",
            "payment_my_courses_button": "🎓 My courses",
            "payment_my_orders_button": "🧾 My orders",
            "order_payment_order": "Order: <code>{order_number}</code>",
            "order_payment_status": "Status: <code>{status}</code>",
            "order_payment_total": "Total: <code>{total}</code>",
            "order_payment_payment": "Payment: <code>{payment_number}</code>",
            "order_payment_provider": "Provider: <code>{provider}</code>",
            "order_payment_payment_status": "Payment status: <code>{status}</code>",
            "order_payment_url": "Payment URL: {url}",
            "course_title_invalid": "Course title must be between 3 and 180 characters.",
            "lesson_title_invalid": "Lesson title must be between 2 and 180 characters.",
            "lesson_created_detail": "{message}\n\n<b>{title}</b>\nCourse: <code>{course}</code>\nPosition: <code>{position}</code>",
            "admin_courses_heading": "<b>🧑‍🏫 Admin courses</b>",
            "admin_course_list_item": "\n<b>{index}. {title}</b>\nStatus: <code>{status}</code> | Price: <code>{price}</code>",
            "manage_course_button": "Manage {title}",
            "admin_course_text": "<b>{title}</b>\n\nStatus: <code>{status}</code>\nSlug: <code>{slug}</code>\nLevel: <code>{level}</code>\nDuration: <code>{duration} min</code>\nLessons: <code>{lessons}</code>\nPrice: <code>{price}</code>\n\n{description}",
            "add_lesson_button": "➕ Add lesson",
            "publish_button": "✅ Publish",
            "unpublish_button": "📥 Unpublish",
            "archive_button": "🗄 Archive",
            "public_view_button": "👁 Public view",
            "all_courses_button": "📋 All courses",
            "help_text": "<b>{project_name} bot guide</b>\nUse the keyboard buttons; you usually do not need to type commands.\n\n<b>Account and security</b>\n🔗 <b>Link account</b> - connect by registered email or Iranian phone number. Email receives an email code; phone receives an SMS code.\n👤 <b>My account</b> - view username, email, phone, and verification status.\n✅ <b>Verify email</b> - receive and confirm the email verification code.\n📱 <b>Verify phone</b> - receive an SMS code, or on Telegram securely share your own contact.\n🔐 <b>Forgot password</b> - request recovery by email or verified phone. Set the new password only in the app/API.\n🚪 <b>Unlink</b> - remove only the messenger connection; your app account remains active.\n\n<b>Courses and purchases</b>\n📚 Browse courses, view details and reviews, buy a course, upload a manual-payment receipt, and follow your orders and enrollments.\n\n<b>Other tools</b>\n💬 Contact support and follow your tickets.\n📣 Open official channels.\n🌐 Open the web app.\n🌍 Change language.\n\n<b>Admin tools</b>\nAdmins can manage courses and lessons, create users, review payments and comments, manage discounts, notifications, support tickets, and runtime bot settings.",
            "placeholder_language": "Language / زبان",
            "placeholder_main_menu": "Choose an action",
            "placeholder_cancel": "Send the requested value or cancel",
            "placeholder_confirm": "Confirm or cancel",
        },
        TelegramBotLanguageVO.FA: {
            "choose_language": "لطفاً زبان ربات را انتخاب کنید:",
            "language_saved": "زبان ذخیره شد. یک گزینه را انتخاب کنید:",
            "canceled": "لغو شد.",
            "use_buttons": "لطفاً از دکمه‌های پایین استفاده کنید.",
            "unknown": "گزینه نامعتبر است. از دکمه‌های پایین استفاده کنید.",
            "private_only": "لطفاً برای مدیریت حساب، به صورت خصوصی به من پیام بدهید.",
            "menu_linked": "خوش برگشتی، <b>{name}</b>!\n\nیک گزینه را انتخاب کنید:",
            "menu_guest": "به ربات {project_name} خوش آمدید.\n\nیک گزینه را انتخاب کنید:",
            "not_linked": "حساب شما هنوز متصل نشده است. دکمه <b>اتصال حساب</b> را بزنید.",
            "already_linked": "حساب پیام‌رسان شما قبلاً متصل شده است.",
            "link_choose": "روش اتصال حساب {project_name} را انتخاب کنید:",
            "link_email_prompt": "ایمیل ثبت‌شده در حساب کاربری را ارسال کنید.\n\nمثال: <code>you@example.com</code>",
            "link_phone_prompt": "شماره موبایل ایرانی ثبت‌شده در حساب را ارسال کنید.\n\nمثال: <code>09123456789</code>",
            "link_prompt": "ایمیل ثبت‌شده در حساب کاربری را ارسال کنید.\n\nمثال: <code>you@example.com</code>",
            "invalid_email": "ایمیل وارد شده معتبر نیست. لطفاً فقط آدرس ایمیل را ارسال کنید.",
            "invalid_link_phone": "شماره موبایل معتبر نیست. یک شماره ایرانی مانند <code>09123456789</code> ارسال کنید.",
            "link_email_code_sent": "اگر حساب فعالی با این ایمیل وجود داشته باشد، کد ۶ رقمی اتصال ارسال شده یا کد قبلی هنوز معتبر است.\n\nکد ۶ رقمی را همین‌جا بفرستید.",
            "link_phone_code_sent": "اگر حساب فعالی با این شماره وجود داشته باشد، کد ۶ رقمی اتصال پیامک شده یا کد قبلی هنوز معتبر است.\n\nکد ۶ رقمی را همین‌جا بفرستید.",
            "link_code_sent": "اگر حساب فعالی با این ایمیل وجود داشته باشد، کد ۶ رقمی اتصال ارسال شده یا کد قبلی هنوز معتبر است.\n\nکد ۶ رقمی را همین‌جا بفرستید.",
            "link_usage": "از <code>/link email@example.com</code> یا <code>/link 09123456789</code> استفاده کنید، یا دکمه اتصال حساب را بزنید.",
            "code_only": "لطفاً فقط کد ۶ رقمی را ارسال کنید. مثال: <code>123456</code>",
            "invalid_link_code": "کد اتصال نامعتبر است یا منقضی شده. دوباره تلاش کنید یا لغو کنید و کد جدید بگیرید.",
            "linked_success": "حساب پیام‌رسان شما با موفقیت متصل شد.",
            "verify_already": "ایمیل شما قبلاً تأیید شده است.",
            "verify_sent": "کد ۶ رقمی تأیید ایمیل به ایمیل متصل‌شده ارسال شد. کد را همین‌جا بفرستید.",
            "verify_code_active": "کد تأیید ایمیل قبلی هنوز معتبر است. همان کد ۶ رقمی را همین‌جا بفرستید.",
            "verify_success": "✅ ایمیل با موفقیت تأیید شد.",
            "verify_invalid": "کد تأیید نامعتبر است یا منقضی شده. دوباره تلاش کنید یا کد جدید بگیرید.",
            "phone_verify_choose": "روش تأیید شماره موبایل را انتخاب کنید. می‌توانید کد پیامکی بگیرید یا شماره شخصی تلگرام خود را با اجازه خودتان به اشتراک بگذارید.",
            "phone_verify_already": "شماره موبایل شما قبلاً تأیید شده است.",
            "phone_verify_required": "برای این حساب شماره موبایلی ثبت نشده است. شماره شخصی تلگرام خود را به اشتراک بگذارید یا ابتدا در برنامه شماره ثبت کنید.",
            "phone_verify_inactive": "این حساب غیرفعال است و امکان تأیید شماره موبایل آن وجود ندارد.",
            "phone_verify_sent": "کد ۶ رقمی تأیید موبایل به <code>{phone}</code> پیامک شد. کد را همین‌جا ارسال کنید.",
            "phone_verify_code_active": "کد پیامکی قبلی برای <code>{phone}</code> هنوز معتبر است. همان کد را همین‌جا ارسال کنید.",
            "phone_verify_share_prompt": "دکمه <b>اشتراک شماره تلگرام</b> را بزنید. تلگرام قبل از ارسال شماره شخصی شما اجازه می‌گیرد.",
            "phone_verify_contact_not_own": "برای امنیت، فقط شماره شخصی خودتان را با دکمه پایین ارسال کنید. مخاطب فورواردشده یا شماره شخص دیگر پذیرفته نمی‌شود.",
            "phone_verify_contact_invalid": "شماره‌ای که تلگرام ارسال کرد معتبر نیست. شماره حساب تلگرام خود را بررسی و دوباره تلاش کنید.",
            "phone_verify_phone_in_use": "این شماره موبایل برای حساب دیگری ثبت شده است.",
            "phone_verify_success": "✅ شماره موبایل با موفقیت تأیید شد.",
            "phone_verify_invalid": "کد تأیید موبایل نامعتبر است یا منقضی شده. دوباره تلاش کنید یا کد جدید بگیرید.",
            "forgot_choose": "روش دریافت کد بازیابی رمز عبور را انتخاب کنید:",
            "forgot_email_prompt": "ایمیل حساب کاربری خود را ارسال کنید.",
            "forgot_phone_prompt": "شماره موبایل حساب را ارسال کنید. مثال: <code>09123456789</code>",
            "forgot_invalid_phone": "شماره موبایل معتبر نیست. شماره ایرانی مانند <code>09123456789</code> ارسال کنید.",
            "forgot_email_sent": "اگر حساب وجود داشته باشد، کد بازیابی ایمیلی ارسال شده یا کد قبلی هنوز معتبر است.\n\nبرای امنیت، رمز جدید را فقط در فرم بازیابی برنامه/API تنظیم کنید.",
            "forgot_phone_sent": "اگر حساب وجود داشته باشد و موبایل آن تأیید شده باشد، کد پیامکی ارسال شده یا کد قبلی هنوز معتبر است.\n\nبرای امنیت، رمز جدید را فقط در فرم بازیابی برنامه/API تنظیم کنید.",
            "forgot_phone_unavailable": "این حساب متصل شماره موبایل تأییدشده ندارد. ابتدا موبایل را تأیید کنید یا بازیابی با ایمیل را انتخاب کنید.",
            "forgot_prompt": "ایمیل حساب خود را ارسال کنید تا در صورت وجود حساب، کد بازیابی رمز عبور ارسال شود.",
            "forgot_sent": "اگر این حساب وجود داشته باشد، کد بازیابی ارسال شده یا کد قبلی هنوز معتبر است.\n\nبرای امنیت، رمز جدید خود را در تلگرام ارسال نکنید. از فرم تغییر رمز برنامه/API با همین کد استفاده کنید.",
            "unlink_ask": "آیا مطمئن هستید که می‌خواهید اتصال تلگرام را حذف کنید؟",
            "unlink_choose": "از دکمه‌های پایین <b>بله، قطع اتصال</b> یا <b>لغو</b> را انتخاب کنید.",
            "unlinked": "اتصال حساب تلگرام شما حذف شد.",
            "webapp_missing": "آدرس برنامه وب هنوز تنظیم نشده است.",
            "webapp_open": "برنامه را از اینجا باز کنید: <a href=\"{url}\">باز کردن برنامه</a>",
            "admin_only": "فقط ادمین متصل‌شده می‌تواند از این قابلیت مدیریتی تلگرام استفاده کند.",
            "bot_settings_title": "⚙️ تنظیمات runtime بات",
            "bot_settings_hint": "روی provider بزن، یک setting را انتخاب کن و مقدار جدید را ارسال کن. مقدار فقط در دیتابیس ذخیره می‌شود. مقادیر حساس مخفی هستند.",
            "bot_settings_provider_title": "⚙️ تنظیمات runtime: {provider}",
            "bot_settings_not_configured": "تنظیم نشده",
            "bot_settings_choose_key": "یک setting را برای ویرایش انتخاب کن:",
            "bot_settings_edit_title": "✏️ ویرایش setting",
            "bot_settings_current_value": "مقدار فعلی",
            "bot_settings_source": "منبع",
            "bot_settings_type": "نوع",
            "bot_settings_choices": "مقادیر مجاز",
            "bot_settings_write_target_prompt": "این مقدار فقط در دیتابیس ذخیره می‌شود.",
            "bot_settings_target_db": "فقط دیتابیس",
            "bot_settings_target_env": "فقط .env",
            "bot_settings_target_both": "دیتابیس + .env",
            "bot_settings_send_value_prompt": "مقدار جدید <b>{label}</b> را ارسال کن.\n\nفقط در دیتابیس ذخیره می‌شود. نام env فقط fallback است: <code>{env_name}</code>\n\nبرای خالی کردن مقدارهای اختیاری <code>-</code> بفرست. برای secret مقدار واقعی جدید را بفرست؛ بات آن را دوباره نمایش نمی‌دهد. بعد از این مرحله، کد تایید به ایمیل تو ارسال می‌شود.",
            "bot_settings_value_saved": "✅ setting بعد از تایید ایمیل با موفقیت به‌روزرسانی شد.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>\nذخیره در: <code>{target}</code>",
            "bot_settings_invalid_value": "⚠️ مقدار نامعتبر است: {error}\n\nدوباره مقدار معتبر را ارسال کن یا لغو کن.",
            "bot_settings_pending_missing": "جلسه ویرایش منقضی شده است. دوباره setting را انتخاب کن.",
            "bot_settings_env_only_warning": "ویرایش .env از تلگرام غیرفعال است. تنظیمات runtime بات فقط در دیتابیس ذخیره می‌شود.",
            "bot_settings_db_only_notice": "برای امنیت، تلگرام فقط مقدار دیتابیس را تغییر می‌دهد. ویرایش .env غیرفعال است.",
            "bot_settings_edit_value_button": "✏️ ویرایش مقدار دیتابیس",
            "bot_settings_custom_value_button": "✍️ ورود مقدار دستی",
            "bot_settings_delete_db_value_button": "🗑 حذف مقدار دیتابیس",
            "bot_settings_delete_confirm": "مقدار دیتابیس <b>{label}</b> حذف شود؟\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>\n\nبعد از حذف، بات از مقدار env/default استفاده می‌کند.",
            "bot_settings_db_value_deleted": "✅ مقدار دیتابیس حذف شد.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>",
            "bot_settings_db_value_not_found": "برای این setting مقدار دیتابیس وجود نداشت. مقدار env/default همچنان فعال است.\n\nProvider: <code>{provider}</code>\nKey: <code>{key}</code>",
            "confirm_delete_button": "✅ بله، حذف کن",
            "bot_settings_email_code_sent": "یک کد تایید ۶ رقمی به <code>{email}</code> فرستادم. برای ذخیره تغییر، کد را تا {minutes} دقیقه دیگر همین‌جا ارسال کن.",
            "bot_settings_delete_email_code_sent": "یک کد تایید ۶ رقمی به <code>{email}</code> فرستادم. برای حذف مقدار دیتابیس، کد را تا {minutes} دقیقه دیگر همین‌جا ارسال کن.",
            "bot_settings_email_code_invalid": "کد تایید نامعتبر یا منقضی شده است. دوباره تلاش کن یا لغو کن.",
            "bot_settings_email_missing": "اکانت ادمین متصل‌شده ایمیل ندارد، بنابراین این setting از تلگرام قابل تغییر نیست.",
            "bot_settings_email_send_failed": "ارسال ایمیل تایید ناموفق بود: {error}",
            "bot_settings_env_write_disabled": "ویرایش مقدارهای .env از تلگرام غیرفعال است. دوباره گزینه ویرایش دیتابیس را انتخاب کن.",
            "admin_notification_title": "ارسال اعلان مدیریتی",
            "discounts_title": "مدیریت کدهای تخفیف",
            "discounts_hint": "برای ساخت تخفیف لازم نیست فرمت خاصی حفظ کنید. بات مرحله‌به‌مرحله کد، نوع تخفیف، مقدار، دوره و محدودیت استفاده را می‌پرسد.",
            "discounts_create_button": "ساخت کد تخفیف جدید",
            "discounts_empty": "هنوز کد تخفیفی وجود ندارد.",
            "discounts_list_count": "تعداد کدها: <code>{count}</code>",
            "discounts_item_text": "کد: <code>{code}</code>\nنوع: <code>{discount_type}</code>\nمقدار: <code>{value}</code>\nقابل استفاده برای: <code>{scope}</code>\nاستفاده‌شده: <code>{used}</code>/<code>{limit}</code>",
            "discounts_create_prompt": "مرحله ۱ از ۵\nکد تخفیف را بفرستید.\n\nمثال: <code>DJANGO30</code>",
            "discounts_code_invalid": "کد تخفیف نامعتبر است. فقط حروف انگلیسی، عدد، خط تیره یا آندرلاین وارد کنید. مثال: <code>DJANGO30</code>",
            "discounts_type_prompt": "مرحله ۲ از ۵\nنوع تخفیف برای <code>{code}</code> را انتخاب کنید.",
            "discounts_type_percent_button": "درصدی",
            "discounts_type_amount_button": "مبلغ ثابت",
            "discounts_value_prompt_percent": "مرحله ۳ از ۵\nدرصد تخفیف را برای <code>{code}</code> بفرستید.\n\nمثال: <code>30</code> یعنی ۳۰ درصد تخفیف.",
            "discounts_value_prompt_amount": "مرحله ۳ از ۵\nمبلغ تخفیف را برای <code>{code}</code> بفرستید.\n\nمثال: <code>500000</code>",
            "discounts_value_invalid": "مقدار تخفیف نامعتبر است. یک عدد مثبت بفرستید. درصد باید بین ۱ تا ۱۰۰ باشد.",
            "discounts_scope_prompt": "مرحله ۴ از ۵\nانتخاب کنید این تخفیف برای کجا قابل استفاده باشد.",
            "discounts_scope_all_button": "همه دوره‌ها",
            "discounts_scope_course_button": "دوره: {title}",
            "discounts_usage_limit_prompt": "مرحله ۵ از ۵\nمحدودیت تعداد استفاده برای <code>{code}</code> را انتخاب کنید.",
            "discounts_usage_unlimited_button": "بدون محدودیت",
            "discounts_usage_custom_button": "تعیین تعداد",
            "discounts_usage_custom_prompt": "حداکثر تعداد استفاده را بفرستید. مثال: <code>100</code>",
            "discounts_usage_invalid": "محدودیت استفاده نامعتبر است. یک عدد صحیح مثبت بفرستید.",
            "discounts_session_expired": "جلسه ساخت تخفیف منقضی شده است. دوباره از منوی تخفیف‌ها شروع کنید.",
            "discounts_created": "کد تخفیف با موفقیت ساخته شد.\n\nکد: <code>{code}</code>\nنوع: <code>{discount_type}</code>\nمقدار: <code>{value}</code>\nقابل استفاده برای: <code>{scope}</code>\nمحدودیت استفاده: <code>{usage_limit}</code>",
            "discounts_invalid_format": "اطلاعات تخفیف کامل نیست. لطفا از دکمه‌های مرحله‌به‌مرحله استفاده کنید.",
            "discounts_delete_button": "حذف",
            "discounts_deleted": "تخفیف حذف شد: <code>{code}</code>",
            "checkout_discount_prompt": "کد تخفیف را بفرستید، یا برای ادامه بدون تخفیف <code>-</code> بفرستید.",
            "checkout_discount_invalid": "کد تخفیف اعمال نشد: {error}\n\nکد دیگری بفرستید یا <code>-</code> را ارسال کنید.",
            "support_title": "پشتیبانی",
            "support_hint": "پیام خود را برای پشتیبانی ارسال کنید و وضعیت تیکت‌های قبلی را ببینید.",
            "support_new_button": "تیکت جدید",
            "support_my_tickets_button": "تیکت‌های من",
            "support_queue_button": "مدیریت تیکت‌ها",
            "support_prompt": "پیام پشتیبانی خود را بفرستید. ادمین آن را دریافت می‌کند.",
            "support_empty": "پیام پشتیبانی نمی‌تواند خالی باشد. پیام را بفرستید یا لغو کنید.",
            "support_created": "تیکت پشتیبانی ساخته شد. شناسه: <code>{ticket_id}</code>",
            "support_user_reply_prompt": "پاسخ خود را برای تیکت <code>{ticket_id}</code> بفرستید.",
            "support_reply_sent": "پاسخ ارسال شد.",
            "support_admin_queue_empty": "تیکت باز وجود ندارد.",
            "support_admin_reply_button": "پاسخ",
            "support_admin_close_button": "بستن",
            "support_admin_reply_prompt": "پاسخ ادمین برای تیکت <code>{ticket_id}</code> را بفرستید.",
            "support_admin_replied": "پاسخ ادمین برای کاربر ارسال شد.",
            "support_closed": "تیکت بسته شد.",
            "support_user_notification": "پاسخ پشتیبانی برای تیکت <code>{ticket_id}</code>:\n\n{message}",
            "support_admin_new_ticket_notice": "تیکت پشتیبانی جدید <code>{ticket_id}</code> از <code>{user}</code>:\n\n{message}",
            "admin_notification_send_now_button": "ارسال فوری",
            "admin_notification_schedule_button": "زمان‌بندی",
            "admin_notification_schedule_prompt": "زمان ارسال را با فرمت <code>YYYY-MM-DD HH:MM</code> بفرستید. مثال: <code>2026-07-03 10:30</code>",
            "admin_notification_schedule_invalid": "زمان نامعتبر است. از فرمت <code>YYYY-MM-DD HH:MM</code> استفاده کنید.",
            "admin_notification_scheduled_result": "اعلان زمان‌بندی شد.\n\nID: <code>{id}</code>\nزمان: <code>{scheduled_at}</code>\nگیرنده‌های فعلی: <code>{count}</code>",
            "admin_notification_hint": "یک پیام برای همه کاربران فعال و متصل‌شده به ربات تلگرام ارسال می‌شود. تعداد گیرنده‌های فعلی: <code>{count}</code>. حداکثر طول پیام: <code>{max_length}</code> کاراکتر. قبل از ارسال، تایید ایمیل لازم است.",
            "admin_notification_start_button": "ساخت اعلان",
            "admin_notification_prompt": "متن اعلان را ارسال کنید. بعد از تایید ایمیل، این پیام برای همه کاربران فعال و متصل‌شده به ربات ارسال می‌شود.",
            "admin_notification_empty": "متن اعلان نمی‌تواند خالی باشد. پیام را ارسال کنید یا لغو کنید.",
            "admin_notification_too_long": "متن اعلان بیش از حد طولانی است. حداکثر طول <code>{max_length}</code> کاراکتر است. پیام کوتاه‌تری ارسال کنید یا لغو کنید.",
            "admin_notification_preview": "پیش‌نمایش برای <code>{count}</code> گیرنده:\n\n{message}",
            "admin_notification_confirm_button": "ارسال بعد از تایید ایمیل",
            "admin_notification_edit_button": "ویرایش پیام",
            "admin_notification_email_subject": "تایید ارسال اعلان ربات",
            "admin_notification_email_code_sent": "یک کد تایید ۶ رقمی به <code>{email}</code> فرستادم. برای ارسال اعلان، کد را تا {minutes} دقیقه دیگر همین‌جا ارسال کنید.",
            "admin_notification_email_code_invalid": "کد تایید نامعتبر یا منقضی شده است. دوباره تلاش کنید یا لغو کنید.",
            "admin_notification_email_missing": "اکانت ادمین متصل‌شده ایمیل ندارد، بنابراین اعلان از تلگرام قابل ارسال نیست.",
            "admin_notification_email_send_failed": "ارسال ایمیل تایید ناموفق بود: {error}",
            "admin_notification_pending_missing": "جلسه ارسال اعلان منقضی شده است. دوباره از منوی اعلان مدیریتی شروع کنید.",
            "admin_notification_delivery_text": "<b>اعلان</b>\n\n{message}",
            "admin_notification_sent_result": "ارسال اعلان تمام شد.\n\nگیرنده‌ها: <code>{total}</code>\nارسال موفق: <code>{success}</code>\nناموفق: <code>{failed}</code>",
            "admin_courses_empty": "هنوز دوره‌ای ساخته نشده است.",
            "course_create_start": "ساخت دوره جدید. ابتدا عنوان دوره را ارسال کنید.",
            "course_short_description_prompt": "توضیح کوتاه دوره را ارسال کنید. حداکثر ۳۰۰ کاراکتر.",
            "course_description_prompt": "توضیح کامل دوره را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "course_price_prompt": "قیمت دوره را به عدد ارسال کنید. برای دوره رایگان <code>0</code> بفرستید.",
            "course_duration_prompt": "مدت کل دوره را به دقیقه ارسال کنید. مثال: <code>120</code>",
            "course_level_prompt": "سطح دوره را ارسال کنید: <code>beginner</code>، <code>intermediate</code>، <code>advanced</code> یا <code>all_levels</code>.",
            "course_publish_prompt": "همین الان منتشر شود؟ برای انتشار <code>yes</code> و برای پیش‌نویس <code>no</code> ارسال کنید.",
            "course_created": "✅ دوره با موفقیت ساخته شد.",
            "course_status_updated": "✅ وضعیت دوره به‌روزرسانی شد.",
            "course_field_updated": "✅ فیلد دوره به‌روزرسانی شد.",
            "course_edit_title": "✏️ ویرایش دوره: {title}",
            "course_edit_value_prompt": "مقدار جدید <b>{field}</b> را ارسال کنید.\n\nمقدار فعلی: <code>{current}</code>\n\nبرای خالی کردن متن‌های اختیاری <code>-</code> بفرستید.",
            "course_edit_choice_prompt": "مقدار جدید <b>{field}</b> را انتخاب کنید.\n\nمقدار فعلی: <code>{current}</code>",
            "course_edit_session_expired": "جلسه ویرایش دوره منقضی شد. دوباره فیلد دوره را انتخاب کنید.",
            "course_choice_session_expired": "جلسه انتخاب منقضی شده است. دوباره فرایند دوره را شروع کنید.",
            "course_delete_confirm": "آیا مطمئن هستید که <b>{title}</b> حذف شود؟\n\nاین حذف نرم است و دوره از دید کاربران مخفی می‌شود.",
            "course_deleted": "✅ دوره حذف شد: <b>{title}</b>",
            "edit_course_button": "✏️ ویرایش دوره",
            "delete_course_button": "🗑 حذف دوره",
            "course_edit_back_button": "⬅️ فیلدهای ویرایش",
            "course_field_title": "عنوان",
            "course_field_short_description": "توضیح کوتاه",
            "course_field_description": "توضیحات",
            "course_field_price": "قیمت",
            "course_field_currency": "واحد پول",
            "course_field_duration_minutes": "مدت",
            "course_field_level": "سطح",
            "course_field_status": "وضعیت",
            "course_field_is_featured": "ویژه",
            "lesson_create_start": "افزودن درس به این دوره. ابتدا عنوان درس را ارسال کنید.",
            "lesson_description_prompt": "توضیح درس را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_content_prompt": "محتوای درس را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_video_url_prompt": "لینک ویدیو را ارسال کنید، یا برای رد شدن <code>-</code> بفرستید.",
            "lesson_duration_prompt": "مدت درس را به دقیقه ارسال کنید. مثال: <code>15</code>",
            "lesson_position_prompt": "شماره ترتیب درس را ارسال کنید، یا برای قرارگیری خودکار در انتها <code>-</code> بفرستید.",
            "lesson_preview_prompt": "آیا این درس پیش‌نمایش رایگان است؟ <code>yes</code> یا <code>no</code> ارسال کنید.",
            "lesson_created": "✅ درس با موفقیت اضافه شد.",
            "course_login_required": "برای خرید دوره، دیدن دوره‌های من یا ثبت دیدگاه ابتدا حساب خود را متصل کنید.",
            "courses_empty": "هنوز دوره منتشرشده‌ای وجود ندارد.",
            "my_courses_empty": "شما هنوز دوره فعالی ندارید.",
            "orders_empty": "شما هنوز سفارشی ندارید.",
            "reviews_empty": "هنوز دیدگاه تأییدشده‌ای وجود ندارد.",
            "review_rating_prompt": "امتیاز این دوره را از ۱ تا ۵ ارسال کنید.",
            "review_title_prompt": "اختیاری: یک عنوان کوتاه برای دیدگاه بفرستید، یا برای رد شدن <code>-</code> ارسال کنید.",
            "review_comment_prompt": "حالا متن دیدگاه خود را ارسال کنید. دیدگاه فقط بعد از تأیید ادمین نمایش داده می‌شود.",
            "review_comment_too_short": "متن دیدگاه باید حداقل ۲ کاراکتر غیر فاصله داشته باشد.",
            "review_pending": "✅ ممنون! دیدگاه شما در انتظار تأیید ادمین است.",
            "review_queue_empty": "دیدگاه در انتظار بررسی وجود ندارد.",
            "payment_manual": "✅ سفارش و پرداخت کارت‌به‌کارت ایجاد شد. بعد از ثبت رسید و تأیید ادمین، ثبت‌نام فعال می‌شود.",
            "payment_success": "✅ پرداخت موفق بود. شما در دوره ثبت‌نام شدید.",
            "payment_created": "✅ سفارش/پرداخت با موفقیت ایجاد شد.",
            "payment_receipt_button": "📎 ارسال رسید",
            "payment_receipt_prompt": "تصویر/فایل رسید را همینجا بفرستید، یا کد پیگیری/شماره ارجاع را به‌صورت متن ارسال کنید.",
            "payment_receipt_saved": "✅ رسید ثبت شد و در انتظار تأیید ادمین است.",
            "payment_receipt_saved_with_id": "{message}\nشناسه رسید: <code>{receipt_id}</code>",
            "payment_receipt_admin_notified": "رسید جدید برای بررسی به ادمین‌ها ارسال شد.",
            "payment_receipt_unsupported_file": "لطفاً تصویر/فایل رسید را بفرستید، یا کد پیگیری را به‌صورت متن ارسال کنید.",
            "payment_queue_empty": "رسید پرداختی در انتظار بررسی وجود ندارد.",
            "payment_queue_heading": "<b>💳 رسیدهای پرداخت در انتظار بررسی</b>",
            "pending_payment_receipt_item": "\n<b>{order}</b>\nکاربر: <code>{user}</code>\nپرداخت: <code>{payment}</code>\nمبلغ: <code>{amount}</code>\nکد پیگیری: <code>{tracking}</code>\nمنبع: <code>{source}</code>",
            "view_receipt_button": "👁 مشاهده رسید",
            "back_to_payment_queue_button": "بازگشت به صف پرداخت‌ها",
            "admin_payment_approve_note": "تأییدشده از ربات تلگرام.",
            "admin_payment_reject_note": "ردشده از ربات تلگرام.",
            "payment_receipt_moderated": "✅ رسید پرداخت <code>{receipt_id}</code> با وضعیت <b>{status}</b> ثبت شد.",
            "order_payment_card_info": "کارت: <code>{card}</code>\nشماره حساب: <code>{account}</code>\nنام صاحب حساب: <code>{holder}</code>\nبانک: <code>{bank}</code>\nشبا: <code>{iban}</code>",
            "order_payment_receipt_hint": "بعد از انتقال وجه، تصویر/فایل رسید را همینجا بفرستید یا کد رسید را ثبت کنید.",
            "course_already_owned": "شما قبلاً این دوره را خریده‌اید.",
            "create_start": "ساخت کاربر جدید.\n\nابتدا نام کاربری را ارسال کنید.\nمثال: <code>ali_ahmadi</code>",
            "create_email": "حالا آدرس جیمیل کاربر را ارسال کنید.\nمثال: <code>user@gmail.com</code>",
            "create_phone": "حالا شماره موبایل را ارسال کنید.\nمثال: <code>09123456789</code>",
            "create_first_name": "حالا نام کوچک را به فارسی ارسال کنید.\nمثال: <code>علی</code>",
            "create_last_name": "حالا نام خانوادگی را به فارسی ارسال کنید.\nمثال: <code>احمدی</code>",
            "create_choose": "از دکمه‌های پایین <b>ساخت کاربر</b> یا <b>لغو</b> را انتخاب کنید.",
            "create_expired": "زمان ساخت کاربر تمام شد. دوباره نام کاربری را ارسال کنید.",
            "create_duplicate": "کاربری با این نام کاربری، ایمیل یا موبایل وجود دارد. با اطلاعات جدید دوباره شروع کنید.",
            "create_done_followup": "کد تنظیم/بازیابی رمز عبور هم به ایمیل کاربر ارسال شد. کاربر می‌تواند از فرم فراموشی رمز عبور برنامه، رمز خود را تنظیم کند.",
            "create_email_failed": "کاربر ساخته شد، اما ارسال ایمیل تنظیم رمز ناموفق بود. از پنل ادمین یا فرایند فراموشی رمز عبور دوباره ارسال کنید.",
            "link_usage": "روش استفاده: <code>/link your-email@example.com</code>",
            "invalid_username_detail": "نام کاربری نامعتبر است: {error}\n\nدوباره نام کاربری را ارسال کنید.",
            "username_exists": "این نام کاربری وجود دارد. نام کاربری دیگری ارسال کنید.",
            "invalid_create_email_detail": "ایمیل نامعتبر است: {error}\n\nدوباره یک جیمیل معتبر ارسال کنید.",
            "email_exists": "این ایمیل وجود دارد. جیمیل دیگری ارسال کنید.",
            "invalid_phone_detail": "شماره موبایل نامعتبر است: {error}\n\nدوباره شماره موبایل را ارسال کنید.",
            "phone_exists": "این شماره موبایل وجود دارد. شماره دیگری ارسال کنید.",
            "invalid_first_name_detail": "نام کوچک نامعتبر است: {error}\n\nدوباره نام کوچک را ارسال کنید.",
            "invalid_last_name_detail": "نام خانوادگی نامعتبر است: {error}\n\nدوباره نام خانوادگی را ارسال کنید.",
            "create_failed": "ساخت کاربر ناموفق بود: {error}",
            "create_success": "✅ کاربر با موفقیت ساخته شد.\n\nنام کاربری: <code>{username}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\n\n{follow_up}",
            "create_confirm_text": "لطفاً اطلاعات کاربر جدید را تأیید کنید:\n\nنام کاربری: <code>{username}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\nنام: <code>{first_name}</code>\nنام خانوادگی: <code>{last_name}</code>\n\nهیچ رمزی در تلگرام ارسال نمی‌شود. کاربر رمز خود را با کد ایمیلی تنظیم می‌کند.",
            "yes": "بله",
            "no": "خیر",
            "account_text": "<b>حساب شما</b>\nنام کاربری: <code>{username}</code>\nنام: <code>{first_name}</code>\nنام خانوادگی: <code>{last_name}</code>\nایمیل: <code>{email}</code>\nموبایل: <code>{phone}</code>\nتأیید ایمیل: <code>{email_verified}</code>\nتأیید موبایل: <code>{phone_verified}</code>",
            "courses_heading": "<b>📚 دوره‌ها</b>",
            "course_list_item": "\n<b>{index}. {title}</b>{rating}\n{description}\nقیمت: <code>{price}</code>",
            "view_course_button": "🔎 {title}",
            "prev_button": "⬅️ قبلی",
            "next_button": "بعدی ➡️",
            "main_menu_button": "⬅️ منوی اصلی",
            "course_detail_text": "<b>{title}</b>\n\n{description}\n\nسطح: <code>{level}</code>\nمدت: <code>{duration} دقیقه</code>\nدرس‌ها: <code>{lessons}</code>\nامتیاز: <code>{rating}</code>\nقیمت: <code>{price}</code>",
            "lessons_button": "🧩 درس‌ها",
            "reviews_button": "⭐ دیدگاه‌ها",
            "buy_button": "🛒 خرید / ثبت‌نام",
            "write_review_button": "✍️ ثبت دیدگاه",
            "courses_back_button": "⬅️ دوره‌ها",
            "course_back_button": "⬅️ دوره",
            "lessons_heading": "<b>🧩 درس‌های {title}</b>",
            "no_lessons": "هنوز درسی برای این دوره منتشر نشده است.",
            "lesson_item": "\n{lock} <b>{position}. {title}</b>\nمدت: <code>{duration} دقیقه</code>",
            "video_line": "ویدیو: {url}",
            "reviews_heading": "<b>⭐ دیدگاه‌های تأییدشده برای {title}</b>",
            "review_item": "\n<b>{rating}/5{title}</b>\nتوسط: <code>{user}</code>\n{comment}",
            "my_courses_heading": "<b>🎓 دوره‌های من</b>",
            "enrollment_item": "\n<b>{title}</b>\nوضعیت: <code>{status}</code>\nتاریخ ثبت‌نام: <code>{enrolled_at}</code>",
            "open_course_button": "باز کردن {title}",
            "my_orders_heading": "<b>🧾 سفارش‌های من</b>",
            "order_item": "\n<b>{order_number}</b>\nدوره‌ها: <code>{courses}</code>\nوضعیت: <code>{status}</code>\nمجموع: <code>{total}</code>",
            "review_saved_with_id": "{message}\nشناسه دیدگاه: <code>{review_id}</code>",
            "review_queue_heading": "<b>🛡 دیدگاه‌های در انتظار بررسی</b>",
            "pending_review_item": "\n<b>{course}</b>\nکاربر: <code>{user}</code> | امتیاز: <code>{rating}/5</code>\n{comment}",
            "approve_button": "✅ تأیید",
            "reject_button": "❌ رد",
            "refresh_button": "به‌روزرسانی",
            "list_page_indicator": "صفحه <code>{page}</code> از <code>{total_pages}</code> • مجموع آیتم‌ها: <code>{total_count}</code>",
            "admin_review_note": "بررسی‌شده از ربات تلگرام.",
            "review_moderated": "✅ دیدگاه <code>{review_id}</code> با وضعیت <b>{status}</b> ثبت شد.",
            "back_to_queue_button": "بازگشت به صف بررسی",
            "payment_my_courses_button": "🎓 دوره‌های من",
            "payment_my_orders_button": "🧾 سفارش‌های من",
            "order_payment_order": "سفارش: <code>{order_number}</code>",
            "order_payment_status": "وضعیت: <code>{status}</code>",
            "order_payment_total": "مجموع: <code>{total}</code>",
            "order_payment_payment": "پرداخت: <code>{payment_number}</code>",
            "order_payment_provider": "درگاه: <code>{provider}</code>",
            "order_payment_payment_status": "وضعیت پرداخت: <code>{status}</code>",
            "order_payment_url": "لینک پرداخت: {url}",
            "course_title_invalid": "عنوان دوره باید بین ۳ تا ۱۸۰ کاراکتر باشد.",
            "lesson_title_invalid": "عنوان درس باید بین ۲ تا ۱۸۰ کاراکتر باشد.",
            "lesson_created_detail": "{message}\n\n<b>{title}</b>\nدوره: <code>{course}</code>\nترتیب: <code>{position}</code>",
            "admin_courses_heading": "<b>🧑‍🏫 مدیریت دوره‌ها</b>",
            "admin_course_list_item": "\n<b>{index}. {title}</b>\nوضعیت: <code>{status}</code> | قیمت: <code>{price}</code>",
            "manage_course_button": "مدیریت {title}",
            "admin_course_text": "<b>{title}</b>\n\nوضعیت: <code>{status}</code>\nاسلاگ: <code>{slug}</code>\nسطح: <code>{level}</code>\nمدت: <code>{duration} دقیقه</code>\nدرس‌ها: <code>{lessons}</code>\nقیمت: <code>{price}</code>\n\n{description}",
            "add_lesson_button": "➕ افزودن درس",
            "publish_button": "✅ انتشار",
            "unpublish_button": "📥 پیش‌نویس",
            "archive_button": "🗄 آرشیو",
            "public_view_button": "👁 نمایش عمومی",
            "all_courses_button": "📋 همه دوره‌ها",
            "help_text": "<b>راهنمای ربات {project_name}</b>\nبرای بیشتر کارها از دکمه‌های پایین استفاده کنید و نیازی به تایپ دستور نیست.\n\n<b>حساب و امنیت</b>\n🔗 <b>اتصال حساب</b> - اتصال با ایمیل ثبت‌شده یا شماره موبایل ایرانی. برای ایمیل کد ایمیلی و برای موبایل کد پیامکی ارسال می‌شود.\n👤 <b>حساب من</b> - نمایش نام کاربری، ایمیل، موبایل و وضعیت تأییدها.\n✅ <b>تأیید ایمیل</b> - دریافت و بررسی کد تأیید ایمیل.\n📱 <b>تأیید موبایل</b> - دریافت کد پیامکی یا در تلگرام اشتراک امن شماره شخصی خودتان.\n🔐 <b>فراموشی رمز عبور</b> - دریافت کد بازیابی با ایمیل یا موبایل تأییدشده. رمز جدید را فقط در برنامه/API تنظیم کنید.\n🚪 <b>قطع اتصال</b> - فقط اتصال پیام‌رسان حذف می‌شود و حساب برنامه فعال می‌ماند.\n\n<b>دوره‌ها و خرید</b>\n📚 مشاهده دوره‌ها، جزئیات و دیدگاه‌ها، خرید دوره، ارسال رسید کارت‌به‌کارت و پیگیری سفارش‌ها و دوره‌های ثبت‌نام‌شده.\n\n<b>ابزارهای دیگر</b>\n💬 ارتباط با پشتیبانی و پیگیری تیکت‌ها.\n📣 مشاهده کانال‌های رسمی.\n🌐 باز کردن برنامه وب.\n🌍 تغییر زبان ربات.\n\n<b>امکانات مدیر</b>\nمدیران می‌توانند دوره و درس را مدیریت کنند، کاربر بسازند، پرداخت‌ها و دیدگاه‌ها را بررسی کنند و تخفیف، اعلان، تیکت پشتیبانی و تنظیمات runtime بات را مدیریت کنند.",
            "placeholder_language": "Language / زبان",
            "placeholder_main_menu": "یک گزینه را انتخاب کنید",
            "placeholder_cancel": "مقدار خواسته‌شده را ارسال کنید یا لغو کنید",
            "placeholder_confirm": "تأیید یا لغو",
        },
    }


class TelegramCommerceMessagesVO:
    AUTH_REQUIRED = "Please link your account before using this feature."
    COURSE_NOT_FOUND = "Course not found or not published."
    EMPTY_COURSES = "No published courses are available yet."
    EMPTY_REVIEWS = "No approved reviews yet."
    EMPTY_ENROLLMENTS = "You do not have any active courses yet."
    EMPTY_ORDERS = "You do not have any orders yet."
    REVIEW_PENDING = "Thanks! Your review was saved and is waiting for admin approval."
    PAYMENT_CREATED = "Payment/order was created."
    PAYMENT_SUCCEEDED = "Payment succeeded. You are now enrolled."
    MANUAL_PAYMENT_CREATED = "Manual payment was created. Admin confirmation is required before enrollment."
    ALREADY_PURCHASED = "You already purchased this course."
    ADMIN_EMPTY_REVIEWS = "There are no pending reviews."


class TelegramBotProfileVO:
    DESCRIPTION = {
        TelegramBotLanguageVO.FA: (
            "سلام! به ربات {project_name} خوش آمدید. 👋\n\n"
            "با این ربات می‌توانید دوره‌ها را ببینید، خرید و ثبت‌نام انجام دهید، "
            "سفارش‌ها و دوره‌های خود را پیگیری کنید، دیدگاه ثبت کنید، حساب را متصل کنید، "
            "ایمیل و شماره موبایل را تأیید کنید و اگر مدیر باشید کاربران و دیدگاه‌ها را مدیریت کنید.\n\n"
            "برای شروع، دکمه Start را بزنید."
        ),
        TelegramBotLanguageVO.EN: (
            "Welcome to {project_name} bot. 👋\n\n"
            "Use this bot to browse and buy courses, track orders and enrollments, "
            "submit reviews, link your account, verify email and phone, recover password, "
            "and manage users/reviews if you are an admin.\n\n"
            "Tap Start to begin."
        ),
    }
    SHORT_DESCRIPTION = {
        TelegramBotLanguageVO.FA: "دوره‌ها، خرید، پشتیبانی و اتصال امن حساب {project_name}",
        TelegramBotLanguageVO.EN: "Courses, purchases, support, and secure {project_name} account linking.",
    }

    @classmethod
    def description(cls, language: str) -> str:
        return cls.DESCRIPTION[language].format(project_name=get_project_name())

    @classmethod
    def short_description(cls, language: str) -> str:
        return cls.SHORT_DESCRIPTION[language].format(project_name=get_project_name())

    COMMANDS = {
        TelegramBotLanguageVO.FA: [
            {"command": "start", "description": "شروع و نمایش منو"},
            {"command": "link", "description": "اتصال حساب با ایمیل یا موبایل"},
            {"command": "courses", "description": "مشاهده دوره‌ها"},
            {"command": "my_courses", "description": "دوره‌های من"},
            {"command": "orders", "description": "سفارش‌های من"},
            {"command": "channels", "description": "کانال‌های رسمی"},
            {"command": "admin_courses", "description": "مدیریت دوره‌ها - فقط ادمین"},
            {"command": "create_course", "description": "ساخت دوره - فقط ادمین"},
            {"command": "review_queue", "description": "بررسی دیدگاه‌ها - فقط ادمین"},
            {"command": "payment_queue", "description": "بررسی پرداخت‌ها - فقط ادمین"},
            {"command": "account", "description": "نمایش حساب من"},
            {"command": "verify_email", "description": "تأیید ایمیل"},
            {"command": "verify_phone", "description": "تأیید شماره موبایل"},
            {"command": "forgot_password", "description": "بازیابی رمز عبور"},
            {"command": "language", "description": "تغییر زبان"},
            {"command": "help", "description": "راهنما"},
        ],
        TelegramBotLanguageVO.EN: [
            {"command": "start", "description": "Start and show menu"},
            {"command": "link", "description": "Link account by email or phone"},
            {"command": "courses", "description": "Browse courses"},
            {"command": "my_courses", "description": "My courses"},
            {"command": "orders", "description": "My orders"},
            {"command": "channels", "description": "Official channels"},
            {"command": "admin_courses", "description": "Manage courses - admin only"},
            {"command": "create_course", "description": "Create course - admin only"},
            {"command": "review_queue", "description": "Review queue - admin only"},
            {"command": "payment_queue", "description": "Payment queue - admin only"},
            {"command": "account", "description": "Show my account"},
            {"command": "verify_email", "description": "Verify email"},
            {"command": "verify_phone", "description": "Verify phone number"},
            {"command": "forgot_password", "description": "Recover password"},
            {"command": "language", "description": "Change language"},
            {"command": "help", "description": "Help"},
        ],
    }
    SETUP_SUCCESS_MESSAGE = "Telegram bot profile UX was updated successfully."
