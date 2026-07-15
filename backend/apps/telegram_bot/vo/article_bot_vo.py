from __future__ import annotations


class ArticleBotCallbackVO:
    PREFIX = "art:"
    MENU = "art:m"
    PUBLIC_LIST_PREFIX = "art:l"
    DETAIL_PREFIX = "art:d"
    ADMIN_LIST_PREFIX = "art:a"
    CREATE = "art:n"
    CREATE_TYPE_PREFIX = "art:ct"
    CREATE_STATUS_PREFIX = "art:cs"
    EDIT_PREFIX = "art:e"
    EDIT_FIELD_PREFIX = "art:ef"
    EDIT_TYPE_PREFIX = "art:et"
    EDIT_STATUS_PREFIX = "art:es"
    TOGGLE_FEATURED_PREFIX = "art:ft"
    DELETE_PREFIX = "art:x"
    DELETE_CONFIRM_PREFIX = "art:xd"
    CANCEL = "art:c"
    MAIN_MENU = "menu:main"

    @classmethod
    def public_list(cls, article_type: str, page: int) -> str:
        return f"{cls.PUBLIC_LIST_PREFIX}:{article_type}:{page}"

    @classmethod
    def detail(cls, article_id: object) -> str:
        return f"{cls.DETAIL_PREFIX}:{article_id}"

    @classmethod
    def admin_list(cls, page: int) -> str:
        return f"{cls.ADMIN_LIST_PREFIX}:{page}"

    @classmethod
    def create_type(cls, article_type: str) -> str:
        return f"{cls.CREATE_TYPE_PREFIX}:{article_type}"

    @classmethod
    def create_status(cls, status: str) -> str:
        return f"{cls.CREATE_STATUS_PREFIX}:{status}"

    @classmethod
    def edit(cls, article_id: object) -> str:
        return f"{cls.EDIT_PREFIX}:{article_id}"

    @classmethod
    def edit_field(cls, article_id: object, field: str) -> str:
        return f"{cls.EDIT_FIELD_PREFIX}:{article_id}:{field}"

    @classmethod
    def edit_type(cls, article_id: object, article_type: str) -> str:
        return f"{cls.EDIT_TYPE_PREFIX}:{article_id}:{article_type}"

    @classmethod
    def edit_status(cls, article_id: object, status: str) -> str:
        return f"{cls.EDIT_STATUS_PREFIX}:{article_id}:{status}"

    @classmethod
    def toggle_featured(cls, article_id: object) -> str:
        return f"{cls.TOGGLE_FEATURED_PREFIX}:{article_id}"

    @classmethod
    def delete(cls, article_id: object) -> str:
        return f"{cls.DELETE_PREFIX}:{article_id}"

    @classmethod
    def delete_confirm(cls, article_id: object) -> str:
        return f"{cls.DELETE_CONFIRM_PREFIX}:{article_id}"


class ArticleBotTextVO:
    TEXTS = {
        "en": {
            "menu_title": "📰 <b>News and weblog</b>\n\nChoose the content you want to browse.",
            "admin_menu_title": "🛠 <b>News and weblog management</b>\n\nCreate, edit, publish, archive, feature, or delete articles.",
            "list_title": "📰 <b>{label}</b> · page {page}/{pages}",
            "list_empty": "No published article was found in this section.",
            "admin_list_title": "🛠 <b>Article management</b> · page {page}/{pages}",
            "admin_list_empty": "No article exists yet.",
            "article_row": "{icon} <b>{title}</b>\n{excerpt}\n🕒 {date} · 👁 {views}",
            "admin_article_row": "{icon} <b>{title}</b>\n{type_label} · {status_label} · 👁 {views}",
            "detail": "{icon} <b>{title}</b>\n\n{excerpt}\n\n{content}\n\n🕒 {date} · ⏱ {minutes} min · 👁 {views}{source}",
            "admin_detail": "🛠 <b>{title}</b>\n\nType: {type_label}\nStatus: {status_label}\nFeatured: {featured}\nPublished: {date}\nViews: {views}\nSlug: <code>{slug}</code>",
            "admin_only": "This section is available only to administrators.",
            "not_found": "The requested article was not found.",
            "operation_failed": "The operation failed: {error}",
            "create_title_prompt": "Send the article title.",
            "create_excerpt_prompt": "Send a short excerpt. Send <code>-</code> to leave it empty.",
            "create_content_prompt": "Send the full article content.",
            "create_type_prompt": "Choose whether this is a weblog post or news item.",
            "create_status_prompt": "Choose the initial publication status.",
            "created": "✅ The article was created successfully.",
            "edit_prompt": "Send the new value for <b>{field}</b>. Send <code>-</code> to clear optional fields.",
            "updated": "✅ The article was updated successfully.",
            "featured_updated": "✅ Featured status was updated.",
            "delete_confirm": "⚠️ Delete <b>{title}</b>? This uses soft delete and removes it from public lists.",
            "deleted": "✅ The article was deleted.",
            "canceled": "The article operation was canceled.",
            "session_expired": "The article form expired. Start again from article management.",
            "invalid_state": "The current article step is invalid. Start again.",
            "invalid_type": "The selected article type is invalid.",
            "invalid_status": "The selected article status is invalid.",
            "invalid_field": "The selected article field is invalid.",
            "title_required": "The article title is required.",
            "content_required": "The article content is required.",
        },
        "fa": {
            "menu_title": "📰 <b>اخبار و وبلاگ</b>\n\nبخش مورد نظر برای مشاهده مطالب را انتخاب کنید.",
            "admin_menu_title": "🛠 <b>مدیریت اخبار و وبلاگ</b>\n\nمطلب ایجاد، ویرایش، منتشر، بایگانی، ویژه یا حذف کنید.",
            "list_title": "📰 <b>{label}</b> · صفحه {page} از {pages}",
            "list_empty": "هنوز مطلب منتشرشده‌ای در این بخش وجود ندارد.",
            "admin_list_title": "🛠 <b>مدیریت مطالب</b> · صفحه {page} از {pages}",
            "admin_list_empty": "هنوز مطلبی ایجاد نشده است.",
            "article_row": "{icon} <b>{title}</b>\n{excerpt}\n🕒 {date} · 👁 {views}",
            "admin_article_row": "{icon} <b>{title}</b>\n{type_label} · {status_label} · 👁 {views}",
            "detail": "{icon} <b>{title}</b>\n\n{excerpt}\n\n{content}\n\n🕒 {date} · ⏱ {minutes} دقیقه · 👁 {views}{source}",
            "admin_detail": "🛠 <b>{title}</b>\n\nنوع: {type_label}\nوضعیت: {status_label}\nویژه: {featured}\nانتشار: {date}\nبازدید: {views}\nنامک: <code>{slug}</code>",
            "admin_only": "این بخش فقط برای مدیران قابل استفاده است.",
            "not_found": "مطلب مورد نظر پیدا نشد.",
            "operation_failed": "عملیات انجام نشد: {error}",
            "create_title_prompt": "عنوان مطلب را ارسال کنید.",
            "create_excerpt_prompt": "خلاصه کوتاه مطلب را ارسال کنید. برای خالی گذاشتن <code>-</code> بفرستید.",
            "create_content_prompt": "محتوای کامل مطلب را ارسال کنید.",
            "create_type_prompt": "نوع مطلب را بین وبلاگ و خبر انتخاب کنید.",
            "create_status_prompt": "وضعیت اولیه انتشار را انتخاب کنید.",
            "created": "✅ مطلب با موفقیت ایجاد شد.",
            "edit_prompt": "مقدار جدید <b>{field}</b> را ارسال کنید. برای پاک‌کردن فیلد اختیاری <code>-</code> بفرستید.",
            "updated": "✅ مطلب با موفقیت به‌روزرسانی شد.",
            "featured_updated": "✅ وضعیت مطلب ویژه تغییر کرد.",
            "delete_confirm": "⚠️ مطلب <b>{title}</b> حذف شود؟ حذف به‌صورت نرم انجام می‌شود و مطلب از لیست عمومی خارج خواهد شد.",
            "deleted": "✅ مطلب حذف شد.",
            "canceled": "عملیات مطلب لغو شد.",
            "session_expired": "فرم مطلب منقضی شده است. دوباره از مدیریت مطالب شروع کنید.",
            "invalid_state": "مرحله فعلی معتبر نیست. دوباره شروع کنید.",
            "invalid_type": "نوع مطلب انتخاب‌شده معتبر نیست.",
            "invalid_status": "وضعیت مطلب انتخاب‌شده معتبر نیست.",
            "invalid_field": "فیلد مطلب انتخاب‌شده معتبر نیست.",
            "title_required": "عنوان مطلب الزامی است.",
            "content_required": "محتوای مطلب الزامی است.",
        },
    }

    @classmethod
    def get(cls, language: str, key: str, **values) -> str:
        language = language if language in cls.TEXTS else "en"
        return cls.TEXTS[language][key].format(**values)


class ArticleBotButtonTextVO:
    BUTTONS = {
        "en": {
            "articles": "📰 News & weblog",
            "all": "🗂 All articles",
            "blog": "✍️ Weblog",
            "news": "📰 News",
            "set_blog": "✍️ Set as weblog",
            "set_news": "📰 Set as news",
            "admin_articles": "🛠 Manage articles",
            "new": "➕ New article",
            "edit": "✏️ Edit",
            "delete": "🗑 Delete",
            "confirm_delete": "✅ Confirm delete",
            "featured": "⭐ Toggle featured",
            "draft": "📝 Draft",
            "published": "✅ Published",
            "archived": "📦 Archived",
            "title": "Title",
            "excerpt": "Excerpt",
            "content": "Content",
            "source_name": "Source name",
            "source_url": "Source URL",
            "meta_title": "SEO title",
            "meta_description": "SEO description",
            "back": "⬅️ Back",
            "next": "Next ➡️",
            "previous": "⬅️ Previous",
            "cancel": "Cancel",
            "main_menu": "🏠 Main menu",
        },
        "fa": {
            "articles": "📰 اخبار و وبلاگ",
            "all": "🗂 همه مطالب",
            "blog": "✍️ وبلاگ",
            "news": "📰 اخبار",
            "set_blog": "✍️ تبدیل به وبلاگ",
            "set_news": "📰 تبدیل به خبر",
            "admin_articles": "🛠 مدیریت مطالب",
            "new": "➕ مطلب جدید",
            "edit": "✏️ ویرایش",
            "delete": "🗑 حذف",
            "confirm_delete": "✅ تأیید حذف",
            "featured": "⭐ تغییر وضعیت ویژه",
            "draft": "📝 پیش‌نویس",
            "published": "✅ منتشرشده",
            "archived": "📦 بایگانی‌شده",
            "title": "عنوان",
            "excerpt": "خلاصه",
            "content": "محتوا",
            "source_name": "نام منبع",
            "source_url": "لینک منبع",
            "meta_title": "عنوان SEO",
            "meta_description": "توضیحات SEO",
            "back": "⬅️ بازگشت",
            "next": "بعدی ➡️",
            "previous": "⬅️ قبلی",
            "cancel": "لغو",
            "main_menu": "🏠 منوی اصلی",
        },
    }

    @classmethod
    def get(cls, language: str, key: str) -> str:
        language = language if language in cls.BUTTONS else "en"
        return cls.BUTTONS[language][key]


class ArticleBotInputVO:
    EMPTY_VALUE = "-"


class ArticleBotLabelVO:
    TYPE_LABELS = {
        "en": {"all": "All articles", "blog": "Weblog", "news": "News"},
        "fa": {"all": "همه مطالب", "blog": "وبلاگ", "news": "اخبار"},
    }
    STATUS_LABELS = {
        "en": {"draft": "Draft", "published": "Published", "archived": "Archived"},
        "fa": {"draft": "پیش‌نویس", "published": "منتشرشده", "archived": "بایگانی‌شده"},
    }
    YES_NO = {
        "en": {True: "Yes", False: "No"},
        "fa": {True: "بله", False: "خیر"},
    }

    @classmethod
    def type_label(cls, language: str, value: str) -> str:
        return cls.TYPE_LABELS.get(language, cls.TYPE_LABELS["en"]).get(value, value)

    @classmethod
    def status_label(cls, language: str, value: str) -> str:
        return cls.STATUS_LABELS.get(language, cls.STATUS_LABELS["en"]).get(value, value)

    @classmethod
    def yes_no(cls, language: str, value: bool) -> str:
        return cls.YES_NO.get(language, cls.YES_NO["en"])[bool(value)]
