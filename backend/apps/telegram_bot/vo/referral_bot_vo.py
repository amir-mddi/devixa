from __future__ import annotations


class ReferralBotCallbackVO:
    PREFIX = "ref:"
    CREATE_CHANNEL_LINK = "ref:channel:create"
    REFRESH = "ref:refresh"
    MAIN_MENU = "menu:main"


class ReferralBotTextVO:
    TEXTS = {
        "fa": {
            "title": "🎁 <b>دعوت دوستان</b>",
            "body": "کد معرفی سایت شما: <code>{code}</code>\n\nدوست شما می‌تواند هنگام ثبت‌نام این کد را به‌صورت اختیاری وارد کند.",
            "channel_ready": "\n📣 لینک اختصاصی دعوت به <b>{channel}</b> آماده است.",
            "channel_missing": "\n📣 برای <b>{channel}</b> هنوز لینک اختصاصی نساخته‌اید.",
            "private_stats": "🔒 آمار تعداد اعضای دعوت‌شده فقط در پنل مدیران قابل مشاهده است.",
            "button_register": "🔗 لینک معرفی سایت",
            "button_create_channel": "➕ ساخت لینک دعوت کانال",
            "button_open_channel": "📨 دعوت به کانال",
            "button_profile": "👤 مشاهده در پروفایل",
            "button_back": "⬅️ منوی اصلی",
            "login_required": "🔐 برای ساخت لینک دعوت، ابتدا حساب سایت را به بات متصل کنید.",
            "channel_created": "✅ لینک اختصاصی کانال ساخته شد.",
            "channel_create_failed": "❌ ساخت لینک کانال انجام نشد. دسترسی ادمین ربات در کانال را بررسی کنید.",
        },
        "en": {
            "title": "🎁 <b>Invite friends</b>",
            "body": "Your website referral code: <code>{code}</code>\n\nYour friend can optionally enter it during registration.",
            "channel_ready": "\n📣 Your personal invite link for <b>{channel}</b> is ready.",
            "channel_missing": "\n📣 You have not created your personal <b>{channel}</b> invite link yet.",
            "private_stats": "🔒 Invite counts are visible to administrators only.",
            "button_register": "🔗 Website referral link",
            "button_create_channel": "➕ Create channel invite link",
            "button_open_channel": "📨 Invite to channel",
            "button_profile": "👤 View in profile",
            "button_back": "⬅️ Main menu",
            "login_required": "🔐 Link your website account before creating an invite link.",
            "channel_created": "✅ Your personal channel invite link was created.",
            "channel_create_failed": "❌ Could not create the channel link. Check the bot's channel admin permissions.",
        },
    }

    @classmethod
    def get(cls, language: str, key: str, **kwargs) -> str:
        language = language if language in cls.TEXTS else "en"
        value = cls.TEXTS[language].get(key, cls.TEXTS["en"].get(key, key))
        return value.format(**kwargs) if kwargs else value


class ReferralBotWebPathVO:
    REGISTER = "/register/?ref={code}"
    PROFILE = "/profile/#referrals"
