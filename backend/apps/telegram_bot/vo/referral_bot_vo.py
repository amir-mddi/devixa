from __future__ import annotations


class ReferralBotCallbackVO:
    MAIN_MENU = "menu:main"


class ReferralBotTextVO:
    TEXTS = {
        "fa": {
            "title": "🎁 <b>دعوت دوستان</b>",
            "body": "کد معرفی شما: <code>{code}</code>\nدعوت‌های موفق: <b>{count}</b> نفر\n\nدوست شما می‌تواند هنگام ثبت‌نام این کد را به‌صورت اختیاری وارد کند.",
            "share_hint": "لینک دعوت اختصاصی شما آماده است؛ می‌توانید آن را برای دوستانتان ارسال کنید.",
            "button_open": "🔗 ثبت‌نام با کد من",
            "button_profile": "👤 مشاهده در پروفایل",
            "button_back": "⬅️ منوی اصلی",
            "login_required": "🔐 برای دریافت کد معرف، ابتدا حساب سایت را به بات متصل کنید.",
        },
        "en": {
            "title": "🎁 <b>Referrals</b>",
            "body": "Your referral code: <code>{code}</code>\nSuccessful invites: <b>{count}</b>\n\nYour friend can optionally enter this code while registering.",
            "share_hint": "Your personal referral link is ready to share.",
            "button_open": "🔗 Register with my code",
            "button_profile": "👤 View in profile",
            "button_back": "⬅️ Main menu",
            "login_required": "🔐 Link your website account to get your referral code.",
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
