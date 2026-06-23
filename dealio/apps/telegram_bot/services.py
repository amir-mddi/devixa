import hashlib
import hmac
import html
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from dealio.apps.accounts.models import Role
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.common.helpers.validators.account_validators import (
    validate_english_username,
    validate_gmail_email,
    validate_iranian_phone_number,
    validate_persian_text,
)
from dealio.apps.common.email_service import send_html_email_async
from dealio.apps.telegram_bot.models import TelegramProfile

logger = logging.getLogger("dealio")
User = get_user_model()


@dataclass(frozen=True)
class TelegramCommand:
    name: str
    args: list[str]
    raw_text: str


class TelegramBotClient:
    """Small Telegram Bot API client using requests; no extra bot package needed."""

    def __init__(self, token: str | None = None, proxy_url: str | None = None):
        self.token = token or getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.token = self.token.strip()

        self.base_url = f"https://api.telegram.org/bot{self.token}"

        self.proxy_url = proxy_url or getattr(settings, "PROXY_URL", "")
        self.proxy_url = self.proxy_url.strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    @property
    def proxies(self) -> dict[str, str] | None:
        if not self.proxy_url:
            return None

        return {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def _request(self, method_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured.")

        response = requests.post(
            f"{self.base_url}/{method_name}",
            json=payload or {},
            timeout=(3.0, 15.0),
            proxies=self.proxies,
        )

        try:
            body = response.json()
        except ValueError:
            body = {"ok": False, "description": response.text}

        if not response.ok or not body.get("ok"):
            raise RuntimeError(f"Telegram API error in {method_name}: {body}")

        return body

    def send_message(
            self,
            chat_id: int,
            text: str,
            *,
            reply_markup: dict[str, Any] | None = None,
            disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._request("sendMessage", payload)

    def answer_callback_query(
            self,
            callback_query_id: str,
            *,
            text: str | None = None,
            show_alert: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            payload["text"] = text
        return self._request("answerCallbackQuery", payload)

    def set_my_description(self, description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"description": description}
        if language_code:
            payload["language_code"] = language_code
        return self._request("setMyDescription", payload)

    def set_my_short_description(self, short_description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"short_description": short_description}
        if language_code:
            payload["language_code"] = language_code
        return self._request("setMyShortDescription", payload)

    def set_my_commands(
            self,
            commands: list[dict[str, str]],
            *,
            language_code: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"commands": commands}
        if language_code:
            payload["language_code"] = language_code
        return self._request("setMyCommands", payload)

    def set_webhook(
            self,
            url: str,
            *,
            secret_token: str | None = None,
            drop_pending_updates: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": url,
            "drop_pending_updates": drop_pending_updates,
            "allowed_updates": ["message", "edited_message", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return self._request("setWebhook", payload)

    def delete_webhook(self, *, drop_pending_updates: bool = False) -> dict[str, Any]:
        return self._request("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    def get_webhook_info(self) -> dict[str, Any]:
        return self._request("getWebhookInfo")

    def get_updates(
            self,
            *,
            offset: int | None = None,
            timeout: int = 30,
            allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": allowed_updates or ["message", "edited_message", "callback_query"],
        }

        if offset is not None:
            payload["offset"] = offset

        response = self._request("getUpdates", payload)
        return response.get("result", [])


class TelegramAccountLinkService:
    LINK_CODE_EXPIRATION_MINUTES = 10

    @staticmethod
    def generate_code() -> str:
        return str(secrets.randbelow(900000) + 100000)

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @classmethod
    def link_cache_key(cls, chat_id: int, user_id: str) -> str:
        return f"telegram_link:{chat_id}:{user_id}"

    @classmethod
    def pending_user_cache_key(cls, chat_id: int) -> str:
        return f"telegram_pending_link:{chat_id}"

    @classmethod
    def send_link_code(cls, *, email: str, chat_id: int) -> bool:
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return False

        code = cls.generate_code()
        timeout_seconds = cls.LINK_CODE_EXPIRATION_MINUTES * 60

        cache.set(cls.pending_user_cache_key(chat_id), str(user.id), timeout=timeout_seconds)
        cache.set(cls.link_cache_key(chat_id, str(user.id)), cls.hash_code(code), timeout=timeout_seconds)

        profile = TelegramProfile.objects.filter(chat_id=chat_id).only("bot_language").first()
        is_fa = bool(profile and profile.bot_language == "fa")
        subject = "کد اتصال حساب تلگرام" if is_fa else "Telegram account link code"
        user_name = user.first_name or user.username or ("کاربر" if is_fa else "there")

        send_html_email_async(
            subject=subject,
            template_name="emails/fa_telegram_link_code.html" if is_fa else "emails/telegram_link_code.html",
            context={
                "subject": subject,
                "app_name": "Devixa",
                "user_name": user_name,
                "code": code,
                "expiration_minutes": cls.LINK_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )
        return True

    @classmethod
    def confirm_link_code(cls, *, profile: TelegramProfile, code: str) -> bool:
        user_id = cache.get(cls.pending_user_cache_key(profile.chat_id))
        if not user_id:
            return False

        saved_hash = cache.get(cls.link_cache_key(profile.chat_id, user_id))
        if not saved_hash or not hmac.compare_digest(saved_hash, cls.hash_code(code)):
            return False

        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            return False

        with transaction.atomic():
            profile.user = user
            profile.is_verified = True
            profile.is_active = True
            profile.save(update_fields=["user", "is_verified", "is_active", "updated_at"])

        cache.delete(cls.pending_user_cache_key(profile.chat_id))
        cache.delete(cls.link_cache_key(profile.chat_id, user_id))
        return True


class TelegramBotService:
    # Callback constants are kept so old inline buttons still work after deployment.
    CALLBACK_MAIN_MENU = "menu:main"
    CALLBACK_LINK = "menu:link"
    CALLBACK_ACCOUNT = "menu:account"
    CALLBACK_VERIFY_EMAIL = "menu:verify_email"
    CALLBACK_FORGOT_PASSWORD = "menu:forgot_password"
    CALLBACK_CREATE_USER = "menu:create_user"
    CALLBACK_WEBAPP = "menu:webapp"
    CALLBACK_LANGUAGE = "menu:language"
    CALLBACK_LANG_EN = "lang:en"
    CALLBACK_LANG_FA = "lang:fa"
    CALLBACK_HELP = "menu:help"
    CALLBACK_UNLINK_ASK = "menu:unlink_ask"
    CALLBACK_UNLINK_CONFIRM = "menu:unlink_confirm"
    CALLBACK_CANCEL = "menu:cancel"

    LANG_EN = "en"
    LANG_FA = "fa"
    SUPPORTED_LANGUAGES = {LANG_EN, LANG_FA}

    LANGUAGE_BUTTONS = {
        LANG_EN: "🇬🇧 English",
        LANG_FA: "🇮🇷 فارسی",
    }

    # English constants are kept for backward compatibility with old keyboards.
    BTN_LINK = "🔗 Link account"
    BTN_ACCOUNT = "👤 My account"
    BTN_VERIFY_EMAIL = "✅ Verify email"
    BTN_FORGOT_PASSWORD = "🔐 Forgot password"
    BTN_CREATE_USER = "➕ Create user"
    BTN_WEBAPP = "🌐 Open app"
    BTN_LANGUAGE = "🌍 Language"
    BTN_UNLINK = "🚪 Unlink"
    BTN_HELP = "❓ Help"
    BTN_MAIN_MENU = "⬅️ Main menu"
    BTN_CANCEL = "Cancel"
    BTN_YES_UNLINK = "✅ Yes, unlink"

    BUTTONS = {
        LANG_EN: {
            "link": BTN_LINK,
            "account": BTN_ACCOUNT,
            "verify_email": BTN_VERIFY_EMAIL,
            "forgot_password": BTN_FORGOT_PASSWORD,
            "create_user": BTN_CREATE_USER,
            "webapp": BTN_WEBAPP,
            "language": BTN_LANGUAGE,
            "unlink": BTN_UNLINK,
            "help": BTN_HELP,
            "main_menu": BTN_MAIN_MENU,
            "cancel": BTN_CANCEL,
            "yes_unlink": BTN_YES_UNLINK,
            "confirm_create": "✅ Create user",
        },
        LANG_FA: {
            "link": "🔗 اتصال حساب",
            "account": "👤 حساب من",
            "verify_email": "✅ تأیید ایمیل",
            "forgot_password": "🔐 فراموشی رمز عبور",
            "create_user": "➕ ساخت کاربر",
            "webapp": "🌐 باز کردن برنامه",
            "language": "🌍 زبان",
            "unlink": "🚪 قطع اتصال",
            "help": "❓ راهنما",
            "main_menu": "⬅️ منوی اصلی",
            "cancel": "لغو",
            "yes_unlink": "✅ بله، قطع اتصال",
            "confirm_create": "✅ ساخت کاربر",
        },
    }

    STATE_LINK_EMAIL = "link_email"
    STATE_LINK_CODE = "link_code"
    STATE_VERIFY_EMAIL_CODE = "verify_email_code"
    STATE_FORGOT_PASSWORD_EMAIL = "forgot_password_email"
    STATE_CREATE_USERNAME = "create_user_username"
    STATE_CREATE_EMAIL = "create_user_email"
    STATE_CREATE_PHONE = "create_user_phone"
    STATE_CREATE_FIRST_NAME = "create_user_first_name"
    STATE_CREATE_LAST_NAME = "create_user_last_name"
    STATE_CREATE_CONFIRM = "create_user_confirm"
    STATE_UNLINK_CONFIRM = "unlink_confirm"

    ACTION_TIMEOUT_SECONDS = TelegramAccountLinkService.LINK_CODE_EXPIRATION_MINUTES * 60

    def __init__(self, client: TelegramBotClient | None = None):
        self.client = client or TelegramBotClient()
        self.link_service = TelegramAccountLinkService()

    def handle_update(self, update: dict[str, Any]) -> None:
        callback_query = update.get("callback_query")
        if callback_query:
            self.handle_callback_query(callback_query)
            return

        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        telegram_user = message.get("from") or {}
        text = (message.get("text") or "").strip()

        if not chat_id or not telegram_user:
            return

        profile = self._upsert_profile(chat_id=chat_id, telegram_user=telegram_user)

        if chat.get("type") != "private":
            self.client.send_message(chat_id, "Please message me privately to manage your account.")
            return

        if text and self.handle_language_selection_text(profile, text):
            return

        if not self.has_selected_language(profile):
            self.show_language_selection(profile)
            return

        if not text:
            self.client.send_message(
                chat_id,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        # ReplyKeyboard buttons arrive as normal text messages. Handle them before
        # command parsing so users can navigate without typing /commands.
        if self.is_main_menu_button(text):
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            self.client.send_message(
                chat_id,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if self.is_cancel_button(text):
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            self.client.send_message(
                chat_id,
                self.t(profile, "canceled"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if self._handle_waiting_text(profile, text):
            return

        if self._handle_menu_button(profile, text):
            return

        command = self.parse_command(text)
        if not command:
            self.client.send_message(
                chat_id,
                self.t(profile, "use_buttons"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        handler_name = f"handle_{command.name.lstrip('/')}"
        handler = getattr(self, handler_name, None)
        if not handler:
            self.client.send_message(
                chat_id,
                self.unknown_command_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        handler(profile, command)

    def handle_callback_query(self, callback_query: dict[str, Any]) -> None:
        callback_query_id = callback_query.get("id")
        data = callback_query.get("data") or ""
        message = callback_query.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        telegram_user = callback_query.get("from") or {}

        if callback_query_id:
            self.client.answer_callback_query(callback_query_id)

        if not chat_id or not telegram_user:
            return

        profile = self._upsert_profile(chat_id=chat_id, telegram_user=telegram_user)

        if chat.get("type") != "private":
            self.client.send_message(chat_id, "Please message me privately to manage your account.")
            return

        if data == self.CALLBACK_LANG_EN:
            self.set_bot_language(profile, self.LANG_EN)
            return

        if data == self.CALLBACK_LANG_FA:
            self.set_bot_language(profile, self.LANG_FA)
            return

        if data == self.CALLBACK_LANGUAGE:
            self.show_language_selection(profile)
            return

        if not self.has_selected_language(profile):
            self.show_language_selection(profile)
            return

        if data == self.CALLBACK_MAIN_MENU:
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if data == self.CALLBACK_LINK:
            self.start_link_flow(profile)
            return

        if data == self.CALLBACK_ACCOUNT:
            self.handle_account(profile, TelegramCommand(name="/account", args=[], raw_text="/account"))
            return

        if data == self.CALLBACK_VERIFY_EMAIL:
            self.start_verify_email_flow(profile)
            return

        if data == self.CALLBACK_FORGOT_PASSWORD:
            self.start_forgot_password_flow(profile)
            return

        if data == self.CALLBACK_CREATE_USER:
            self.start_create_user_flow(profile)
            return

        if data == self.CALLBACK_WEBAPP:
            self.handle_webapp(profile, TelegramCommand(name="/webapp", args=[], raw_text="/webapp"))
            return

        if data == self.CALLBACK_HELP:
            self.client.send_message(
                profile.chat_id,
                self.help_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if data == self.CALLBACK_UNLINK_ASK:
            self.start_unlink_flow(profile)
            return

        if data == self.CALLBACK_UNLINK_CONFIRM:
            self.clear_action(profile.chat_id)
            self.handle_unlink(profile, TelegramCommand(name="/unlink", args=[], raw_text="/unlink"))
            return

        if data == self.CALLBACK_CANCEL:
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "canceled"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.client.send_message(
            profile.chat_id,
            self.unknown_command_text(profile),
            reply_markup=self.main_menu_keyboard(profile),
        )

    @staticmethod
    def parse_command(text: str) -> TelegramCommand | None:
        parts = text.split()
        if not parts or not parts[0].startswith("/"):
            return None

        name = parts[0].split("@", 1)[0].lower()
        return TelegramCommand(name=name, args=parts[1:], raw_text=text)

    @staticmethod
    def normalize_button_text(text: str) -> str:
        # Telegram sends ReplyKeyboard button text exactly, including emojis.
        # Normalize too so renamed/emoji-free buttons still work.
        cleaned = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
        return " ".join(cleaned.casefold().split())

    @classmethod
    def has_selected_language(cls, profile: TelegramProfile) -> bool:
        return getattr(profile, "bot_language", "") in cls.SUPPORTED_LANGUAGES

    @classmethod
    def lang(cls, profile: TelegramProfile | None = None) -> str:
        language = getattr(profile, "bot_language", "") if profile else ""
        return language if language in cls.SUPPORTED_LANGUAGES else cls.LANG_EN

    @classmethod
    def button(cls, profile: TelegramProfile | None, key: str) -> str:
        return cls.BUTTONS[cls.lang(profile)][key]

    @classmethod
    def all_button_texts(cls, key: str) -> set[str]:
        return {cls.normalize_button_text(labels[key]) for labels in cls.BUTTONS.values() if key in labels}

    @classmethod
    def t(cls, profile: TelegramProfile | None, key: str, **kwargs: Any) -> str:
        texts = {
            cls.LANG_EN: {
                "choose_language": "Please choose your language / لطفاً زبان خود را انتخاب کنید:",
                "language_saved": "Language saved. Choose an action:",
                "canceled": "Canceled.",
                "use_buttons": "Please use the menu buttons below.",
                "unknown": "Unknown action. Use the buttons below.",
                "private_only": "Please message me privately to manage your account.",
                "menu_linked": "Welcome back, <b>{name}</b>!\n\nChoose an action:",
                "menu_guest": "Welcome to Devixa bot.\n\nChoose an action:",
                "not_linked": "Your account is not linked yet. Tap <b>Link account</b> below.",
                "already_linked": "Your Telegram account is already linked.",
                "link_prompt": "Send your app account email address here.\n\nExample: <code>you@example.com</code>",
                "invalid_email": "That does not look like a valid email. Please send only your email address.",
                "link_code_sent": "If this email exists, I sent a 6-digit link code to it.\n\nNow send the 6-digit code here.",
                "code_only": "Please send the 6-digit code only. Example: <code>123456</code>",
                "invalid_link_code": "Invalid or expired link code. Try again, or cancel and request a new code.",
                "linked_success": "Your Telegram account is linked successfully.",
                "verify_already": "Your email is already verified.",
                "verify_sent": "I sent a 6-digit email verification code to your linked email. Send the code here.",
                "verify_success": "✅ Email verified successfully.",
                "verify_invalid": "Invalid or expired verification code. Try again or request a new code.",
                "forgot_prompt": "Send your account email address, and I will send a password recovery code if it exists.",
                "forgot_sent": "If this account exists, a password recovery code has been sent to the account email.\n\nFor security, do not send your new password in Telegram. Use the app/API reset form with the code.",
                "unlink_ask": "Are you sure you want to unlink this Telegram account?",
                "unlink_choose": "Choose <b>Yes, unlink</b> or <b>Cancel</b> from the keyboard below.",
                "unlinked": "Your Telegram account has been unlinked.",
                "webapp_missing": "Web app URL is not configured yet.",
                "webapp_open": "Open the app here: <a href=\"{url}\">Open app</a>",
                "admin_only": "Only a linked admin can create users from Telegram.",
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
            },
            cls.LANG_FA: {
                "choose_language": "لطفاً زبان ربات را انتخاب کنید:",
                "language_saved": "زبان ذخیره شد. یک گزینه را انتخاب کنید:",
                "canceled": "لغو شد.",
                "use_buttons": "لطفاً از دکمه‌های پایین استفاده کنید.",
                "unknown": "گزینه نامعتبر است. از دکمه‌های پایین استفاده کنید.",
                "private_only": "لطفاً برای مدیریت حساب، به صورت خصوصی به من پیام بدهید.",
                "menu_linked": "خوش برگشتی، <b>{name}</b>!\n\nیک گزینه را انتخاب کنید:",
                "menu_guest": "به ربات Devixa خوش آمدید.\n\nیک گزینه را انتخاب کنید:",
                "not_linked": "حساب شما هنوز متصل نشده است. دکمه <b>اتصال حساب</b> را بزنید.",
                "already_linked": "حساب تلگرام شما قبلاً متصل شده است.",
                "link_prompt": "ایمیل حساب کاربری خود را ارسال کنید.\n\nمثال: <code>you@example.com</code>",
                "invalid_email": "ایمیل وارد شده معتبر نیست. لطفاً فقط آدرس ایمیل را ارسال کنید.",
                "link_code_sent": "اگر این ایمیل وجود داشته باشد، کد ۶ رقمی اتصال برای آن ارسال شد.\n\nحالا کد ۶ رقمی را همین‌جا بفرستید.",
                "code_only": "لطفاً فقط کد ۶ رقمی را ارسال کنید. مثال: <code>123456</code>",
                "invalid_link_code": "کد اتصال نامعتبر است یا منقضی شده. دوباره تلاش کنید یا لغو کنید و کد جدید بگیرید.",
                "linked_success": "حساب تلگرام شما با موفقیت متصل شد.",
                "verify_already": "ایمیل شما قبلاً تأیید شده است.",
                "verify_sent": "کد ۶ رقمی تأیید ایمیل به ایمیل متصل‌شده ارسال شد. کد را همین‌جا بفرستید.",
                "verify_success": "✅ ایمیل با موفقیت تأیید شد.",
                "verify_invalid": "کد تأیید نامعتبر است یا منقضی شده. دوباره تلاش کنید یا کد جدید بگیرید.",
                "forgot_prompt": "ایمیل حساب خود را ارسال کنید تا در صورت وجود حساب، کد بازیابی رمز عبور ارسال شود.",
                "forgot_sent": "اگر این حساب وجود داشته باشد، کد بازیابی رمز عبور به ایمیل حساب ارسال شد.\n\nبرای امنیت، رمز جدید خود را در تلگرام ارسال نکنید. از فرم تغییر رمز برنامه/API با همین کد استفاده کنید.",
                "unlink_ask": "آیا مطمئن هستید که می‌خواهید اتصال تلگرام را حذف کنید؟",
                "unlink_choose": "از دکمه‌های پایین <b>بله، قطع اتصال</b> یا <b>لغو</b> را انتخاب کنید.",
                "unlinked": "اتصال حساب تلگرام شما حذف شد.",
                "webapp_missing": "آدرس برنامه وب هنوز تنظیم نشده است.",
                "webapp_open": "برنامه را از اینجا باز کنید: <a href=\"{url}\">باز کردن برنامه</a>",
                "admin_only": "فقط ادمین متصل‌شده می‌تواند از تلگرام کاربر بسازد.",
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
            },
        }
        template = texts[cls.lang(profile)].get(key, texts[cls.LANG_EN].get(key, key))
        return template.format(**kwargs) if kwargs else template

    def show_language_selection(self, profile: TelegramProfile) -> None:
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "choose_language"),
            reply_markup=self.language_keyboard(),
        )

    def set_bot_language(self, profile: TelegramProfile, language: str) -> None:
        if language not in self.SUPPORTED_LANGUAGES:
            self.show_language_selection(profile)
            return
        profile.bot_language = language
        profile.save(update_fields=["bot_language", "updated_at"])
        self.clear_action(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "language_saved"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_language_selection_text(self, profile: TelegramProfile, text: str) -> bool:
        normalized = self.normalize_button_text(text)
        if normalized in {self.normalize_button_text(self.LANGUAGE_BUTTONS[self.LANG_EN]), "english", "en"}:
            self.set_bot_language(profile, self.LANG_EN)
            return True
        if normalized in {self.normalize_button_text(self.LANGUAGE_BUTTONS[self.LANG_FA]), "فارسی", "farsi", "fa",
                          "persian"}:
            self.set_bot_language(profile, self.LANG_FA)
            return True
        return False

    @classmethod
    def language_keyboard(cls) -> dict[str, Any]:
        return cls.reply_keyboard(
            [[cls.LANGUAGE_BUTTONS[cls.LANG_FA], cls.LANGUAGE_BUTTONS[cls.LANG_EN]]],
            placeholder="Language / زبان",
        )

    @classmethod
    def is_cancel_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in {"cancel", "لغو"} | cls.all_button_texts("cancel")

    @classmethod
    def is_main_menu_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in {"main menu", "menu", "منوی اصلی"} | cls.all_button_texts("main_menu")

    @classmethod
    def is_yes_unlink_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in {"yes unlink", "yes", "unlink", "بله حذف اتصال",
                                                   "بله قطع اتصال"} | cls.all_button_texts("yes_unlink")

    def _handle_menu_button(self, profile: TelegramProfile, text: str) -> bool:
        normalized = self.normalize_button_text(text)

        action_by_key = {
            "link": self.start_link_flow,
            "account": lambda p: self.handle_account(p, TelegramCommand(name="/account", args=[], raw_text="/account")),
            "verify_email": self.start_verify_email_flow,
            "forgot_password": self.start_forgot_password_flow,
            "create_user": self.start_create_user_flow,
            "webapp": lambda p: self.handle_webapp(p, TelegramCommand(name="/webapp", args=[], raw_text="/webapp")),
            "language": self.show_language_selection,
            "unlink": self.start_unlink_flow,
            "help": lambda p: self.handle_help(p, TelegramCommand(name="/help", args=[], raw_text="/help")),
        }

        aliases = {
            "link": {"link account", "اتصال حساب"},
            "account": {"my account", "account", "حساب من"},
            "verify_email": {"verify email", "email verification", "تایید ایمیل", "تأیید ایمیل"},
            "forgot_password": {"forgot password", "فراموشی رمز عبور"},
            "create_user": {"create user", "ساخت کاربر"},
            "webapp": {"open app", "web app", "باز کردن برنامه"},
            "language": {"language", "زبان"},
            "unlink": {"unlink", "قطع اتصال"},
            "help": {"help", "راهنما"},
        }

        for key, handler in action_by_key.items():
            possible = self.all_button_texts(key) | {self.normalize_button_text(item) for item in aliases[key]}
            if normalized in possible:
                handler(profile)
                return True

        return False

    @staticmethod
    def _upsert_profile(*, chat_id: int, telegram_user: dict[str, Any]) -> TelegramProfile:
        # Keep Telegram metadata fresh, but do not overwrite bot_language because
        # it is the user's explicit menu-language choice.
        defaults = {
            "telegram_user_id": telegram_user.get("id"),
            "username": telegram_user.get("username") or "",
            "first_name": telegram_user.get("first_name") or "",
            "last_name": telegram_user.get("last_name") or "",
            "language_code": telegram_user.get("language_code") or "",
            "is_active": True,
        }
        profile, created = TelegramProfile.objects.get_or_create(chat_id=chat_id, defaults=defaults)
        if not created:
            changed_fields: list[str] = []
            for field, value in defaults.items():
                if getattr(profile, field) != value:
                    setattr(profile, field, value)
                    changed_fields.append(field)
            if changed_fields:
                changed_fields.append("updated_at")
                profile.save(update_fields=changed_fields)
        return profile

    @classmethod
    def action_cache_key(cls, chat_id: int) -> str:
        return f"telegram_bot_action:{chat_id}"

    @classmethod
    def set_action(cls, chat_id: int, action: str) -> None:
        cache.set(cls.action_cache_key(chat_id), action, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def get_action(cls, chat_id: int) -> str | None:
        return cache.get(cls.action_cache_key(chat_id))

    @classmethod
    def clear_action(cls, chat_id: int) -> None:
        cache.delete(cls.action_cache_key(chat_id))

    @classmethod
    def create_user_cache_key(cls, chat_id: int) -> str:
        return f"telegram_create_user:{chat_id}"

    @classmethod
    def get_create_user_data(cls, chat_id: int) -> dict[str, str]:
        data = cache.get(cls.create_user_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_create_user_data(cls, chat_id: int, data: dict[str, str]) -> None:
        cache.set(cls.create_user_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_create_user_data(cls, chat_id: int) -> None:
        cache.delete(cls.create_user_cache_key(chat_id))

    @staticmethod
    def normalize_iranian_phone_number(value: str) -> str:
        value = value.strip().replace(" ", "").replace("-", "")
        if value.startswith("+989") and len(value) == 13:
            return "0" + value[3:]
        if value.startswith("989") and len(value) == 12:
            return "0" + value[2:]
        return value

    @staticmethod
    def validation_message(error: Exception) -> str:
        detail = getattr(error, "detail", None)
        if detail is not None:
            return str(detail).strip("[]'")
        messages = getattr(error, "messages", None)
        if messages:
            return " ".join(str(message) for message in messages)
        return str(error)

    @staticmethod
    def is_admin_profile(profile: TelegramProfile) -> bool:
        if not profile.user_id or not profile.is_verified:
            return False
        user = profile.user
        role_symbol = getattr(getattr(user, "role", None), "symbol", "")
        return bool(user.is_superuser or user.is_staff or role_symbol == "admin")

    @staticmethod
    def ensure_default_user_role() -> None:
        if Role.objects.filter(symbol="user").exists():
            return

        role = Role.objects.filter(name__iexact="user").first()
        if role:
            role.symbol = "user"
            role.save(update_fields=["symbol", "updated_at"])
            return

        Role.objects.create(name="User", symbol="user")

    @staticmethod
    def is_valid_email(value: str) -> bool:
        try:
            validate_email(value)
        except ValidationError:
            return False
        return True

    def _handle_waiting_text(self, profile: TelegramProfile, text: str) -> bool:
        action = self.get_action(profile.chat_id)
        if not action:
            return False

        # Let regular commands like /start and /help work even while a flow is open.
        if text.startswith("/"):
            return False

        if action == self.STATE_LINK_EMAIL:
            self.handle_link_email_text(profile, text)
            return True

        if action == self.STATE_LINK_CODE:
            self.handle_link_code_text(profile, text)
            return True

        if action == self.STATE_VERIFY_EMAIL_CODE:
            self.handle_verify_email_code_text(profile, text)
            return True

        if action == self.STATE_FORGOT_PASSWORD_EMAIL:
            self.handle_forgot_password_email_text(profile, text)
            return True

        if action == self.STATE_CREATE_USERNAME:
            self.handle_create_username_text(profile, text)
            return True

        if action == self.STATE_CREATE_EMAIL:
            self.handle_create_email_text(profile, text)
            return True

        if action == self.STATE_CREATE_PHONE:
            self.handle_create_phone_text(profile, text)
            return True

        if action == self.STATE_CREATE_FIRST_NAME:
            self.handle_create_first_name_text(profile, text)
            return True

        if action == self.STATE_CREATE_LAST_NAME:
            self.handle_create_last_name_text(profile, text)
            return True

        if action == self.STATE_CREATE_CONFIRM:
            self.handle_create_confirm_text(profile, text)
            return True

        if action == self.STATE_UNLINK_CONFIRM:
            if self.is_yes_unlink_button(text):
                self.clear_action(profile.chat_id)
                self.handle_unlink(profile, TelegramCommand(name="/unlink", args=[], raw_text="/unlink"))
            else:
                self.client.send_message(
                    profile.chat_id,
                    self.t(profile, "unlink_choose"),
                    reply_markup=self.confirm_unlink_keyboard(profile),
                )
            return True

        self.clear_action(profile.chat_id)
        return False

    def start_link_flow(self, profile: TelegramProfile) -> None:
        if profile.user_id and profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "already_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_LINK_EMAIL)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_prompt"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_link_email_text(self, profile: TelegramProfile, email: str) -> None:
        email = email.strip()
        if not self.is_valid_email(email):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_email"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.link_service.send_link_code(email=email, chat_id=profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_LINK_CODE)

        # Always return the same response so the bot does not reveal which emails exist.
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_code_sent"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_link_code_text(self, profile: TelegramProfile, code: str) -> None:
        code = code.strip()
        if not code.isdigit() or len(code) != 6:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if not self.link_service.confirm_link_code(profile=profile, code=code):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_link_code"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.clear_action(profile.chat_id)
        profile.refresh_from_db(fields=["user", "is_verified"])
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "linked_success"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def start_forgot_password_flow(self, profile: TelegramProfile) -> None:
        if profile.user_id and profile.is_verified:
            self.handle_forgot_password(profile,
                                        TelegramCommand(name="/forgot_password", args=[], raw_text="/forgot_password"))
            return

        self.set_action(profile.chat_id, self.STATE_FORGOT_PASSWORD_EMAIL)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_prompt"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_forgot_password_email_text(self, profile: TelegramProfile, email: str) -> None:
        email = email.strip()
        if not self.is_valid_email(email):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_email"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.clear_action(profile.chat_id)
        self.handle_forgot_password(
            profile,
            TelegramCommand(name="/forgot_password", args=[email], raw_text=f"/forgot_password {email}"),
        )

    def start_create_user_flow(self, profile: TelegramProfile) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_only"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.clear_create_user_data(profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_CREATE_USERNAME)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "create_start"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_create_username_text(self, profile: TelegramProfile, username: str) -> None:
        username = username.strip()
        try:
            username = validate_english_username(username)
        except Exception as error:
            self.client.send_message(
                profile.chat_id,
                f"Invalid username: {html.escape(self.validation_message(error))}\n\nSend the username again.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(username__iexact=username).exists():
            self.client.send_message(
                profile.chat_id,
                "This username already exists. Send another username.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.set_create_user_data(profile.chat_id, {"username": username})
        self.set_action(profile.chat_id, self.STATE_CREATE_EMAIL)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "create_email"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_create_email_text(self, profile: TelegramProfile, email: str) -> None:
        email = email.strip().lower()
        try:
            email = validate_gmail_email(email)
        except Exception as error:
            self.client.send_message(
                profile.chat_id,
                f"Invalid email: {html.escape(self.validation_message(error))}\n\nSend a Gmail address again.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(email__iexact=email).exists():
            self.client.send_message(
                profile.chat_id,
                "This email already exists. Send another Gmail address.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        data = self.get_create_user_data(profile.chat_id)
        data["email"] = email
        self.set_create_user_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_CREATE_PHONE)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "create_phone"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_create_phone_text(self, profile: TelegramProfile, phone_number: str) -> None:
        phone_number = self.normalize_iranian_phone_number(phone_number)
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except Exception as error:
            self.client.send_message(
                profile.chat_id,
                f"Invalid phone number: {html.escape(self.validation_message(error))}\n\nSend the phone number again.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(phone_number=phone_number).exists():
            self.client.send_message(
                profile.chat_id,
                "This phone number already exists. Send another phone number.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        data = self.get_create_user_data(profile.chat_id)
        data["phone_number"] = phone_number
        self.set_create_user_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_CREATE_FIRST_NAME)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "create_first_name"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_create_first_name_text(self, profile: TelegramProfile, first_name: str) -> None:
        first_name = first_name.strip()
        try:
            first_name = validate_persian_text(first_name)
        except Exception as error:
            self.client.send_message(
                profile.chat_id,
                f"Invalid first name: {html.escape(self.validation_message(error))}\n\nSend the first name again.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        data = self.get_create_user_data(profile.chat_id)
        data["first_name"] = first_name
        self.set_create_user_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_CREATE_LAST_NAME)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "create_last_name"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_create_last_name_text(self, profile: TelegramProfile, last_name: str) -> None:
        last_name = last_name.strip()
        try:
            last_name = validate_persian_text(last_name)
        except Exception as error:
            self.client.send_message(
                profile.chat_id,
                f"Invalid last name: {html.escape(self.validation_message(error))}\n\nSend the last name again.",
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        data = self.get_create_user_data(profile.chat_id)
        data["last_name"] = last_name
        self.set_create_user_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_CREATE_CONFIRM)
        self.client.send_message(
            profile.chat_id,
            self.create_user_confirmation_text(profile, data),
            reply_markup=self.confirm_create_user_keyboard(profile),
        )

    def handle_create_confirm_text(self, profile: TelegramProfile, text: str) -> None:
        normalized = self.normalize_button_text(text)
        if normalized not in {"create user", "create", "yes create", "confirm", "تایید", "ساخت کاربر"}:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "create_choose"),
                reply_markup=self.confirm_create_user_keyboard(profile),
            )
            return

        data = self.get_create_user_data(profile.chat_id)
        required_fields = {"username", "email", "phone_number", "first_name", "last_name"}
        if not required_fields.issubset(data):
            self.clear_create_user_data(profile.chat_id)
            self.set_action(profile.chat_id, self.STATE_CREATE_USERNAME)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "create_expired"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        try:
            with transaction.atomic():
                self.ensure_default_user_role()
                user = User.objects.create_user(
                    username=data["username"],
                    email=data["email"],
                    password=None,
                    phone_number=data["phone_number"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    email_verified=False,
                    phone_number_verified=False,
                )
        except IntegrityError:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "create_duplicate"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            return
        except Exception as error:
            logger.exception("Failed to create Telegram user account")
            self.client.send_message(
                profile.chat_id,
                f"Could not create the user: {html.escape(str(error))}",
                reply_markup=self.main_menu_keyboard(profile),
            )
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            return

        try:
            AccountLogicRepository().send_verification_forget_password_code(user)
            follow_up = (
                self.t(profile, "create_done_followup")
            )
        except Exception:
            logger.exception("Failed to send password setup email for Telegram-created user")
            follow_up = (
                self.t(profile, "create_email_failed")
            )

        self.clear_action(profile.chat_id)
        self.clear_create_user_data(profile.chat_id)
        if self.lang(profile) == self.LANG_FA:
            success_text = (
                "✅ کاربر با موفقیت ساخته شد.\n\n"
                f"نام کاربری: <code>{html.escape(user.username)}</code>\n"
                f"ایمیل: <code>{html.escape(user.email)}</code>\n"
                f"موبایل: <code>{html.escape(user.phone_number)}</code>\n\n"
                f"{follow_up}"
            )
        else:
            success_text = (
                "✅ User created successfully.\n\n"
                f"Username: <code>{html.escape(user.username)}</code>\n"
                f"Email: <code>{html.escape(user.email)}</code>\n"
                f"Phone: <code>{html.escape(user.phone_number)}</code>\n\n"
                f"{follow_up}"
            )

        self.client.send_message(
            profile.chat_id,
            success_text,
            reply_markup=self.main_menu_keyboard(profile),
        )

    @classmethod
    def create_user_confirmation_text(cls, profile: TelegramProfile, data: dict[str, str]) -> str:
        if cls.lang(profile) == cls.LANG_FA:
            return (
                "لطفاً اطلاعات کاربر جدید را تأیید کنید:\n\n"
                f"نام کاربری: <code>{html.escape(data.get('username', '-'))}</code>\n"
                f"ایمیل: <code>{html.escape(data.get('email', '-'))}</code>\n"
                f"موبایل: <code>{html.escape(data.get('phone_number', '-'))}</code>\n"
                f"نام: <code>{html.escape(data.get('first_name', '-'))}</code>\n"
                f"نام خانوادگی: <code>{html.escape(data.get('last_name', '-'))}</code>\n\n"
                "هیچ رمزی در تلگرام ارسال نمی‌شود. کاربر رمز خود را با کد ایمیلی تنظیم می‌کند."
            )
        return (
            "Please confirm this new user:\n\n"
            f"Username: <code>{html.escape(data.get('username', '-'))}</code>\n"
            f"Email: <code>{html.escape(data.get('email', '-'))}</code>\n"
            f"Phone: <code>{html.escape(data.get('phone_number', '-'))}</code>\n"
            f"First name: <code>{html.escape(data.get('first_name', '-'))}</code>\n"
            f"Last name: <code>{html.escape(data.get('last_name', '-'))}</code>\n\n"
            "No password will be sent in Telegram. The user will set their password by email reset code."
        )

    def start_verify_email_flow(self, profile: TelegramProfile) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        user = profile.user
        if user.email_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "verify_already"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        AccountLogicRepository().send_verification_email_code(user)
        self.set_action(profile.chat_id, self.STATE_VERIFY_EMAIL_CODE)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "verify_sent"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_verify_email_code_text(self, profile: TelegramProfile, code: str) -> None:
        code = code.strip()
        if not code.isdigit() or len(code) != 6:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if not profile.user_id or not profile.is_verified:
            self.clear_action(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if not AccountLogicRepository().check_email_validation_code(profile.user, code):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "verify_invalid"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.clear_action(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "verify_success"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_start(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.clear_action(profile.chat_id)
        self.clear_create_user_data(profile.chat_id)
        if not self.has_selected_language(profile):
            self.show_language_selection(profile)
            return
        self.client.send_message(
            profile.chat_id,
            self.menu_text(profile),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_help(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.client.send_message(
            profile.chat_id,
            self.help_text(profile),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_language(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.show_language_selection(profile)

    def handle_verify_email(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if command.args and command.args[0].isdigit() and len(command.args[0]) == 6:
            self.handle_verify_email_code_text(profile, command.args[0])
            return
        self.start_verify_email_flow(profile)

    def handle_create_user(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.start_create_user_flow(profile)

    def handle_link(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if not command.args:
            self.start_link_flow(profile)
            return

        email = command.args[0].strip()
        if not self.is_valid_email(email):
            self.client.send_message(
                profile.chat_id,
                "Usage: <code>/link your-email@example.com</code>",
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.link_service.send_link_code(email=email, chat_id=profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_LINK_CODE)

        # Always return the same response so the bot does not reveal which emails exist.
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_code_sent"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_confirm(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if not command.args or not command.args[0].isdigit() or len(command.args[0]) != 6:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if not self.link_service.confirm_link_code(profile=profile, code=command.args[0]):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_link_code"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.clear_action(profile.chat_id)
        profile.refresh_from_db(fields=["user", "is_verified"])
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "linked_success"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def start_unlink_flow(self, profile: TelegramProfile) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_UNLINK_CONFIRM)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "unlink_ask"),
            reply_markup=self.confirm_unlink_keyboard(profile),
        )

    def handle_unlink(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        profile.user = None
        profile.is_verified = False
        profile.save(update_fields=["user", "is_verified", "updated_at"])
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "unlinked"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_account(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        user = profile.user
        if self.lang(profile) == self.LANG_FA:
            verified = "بله" if user.email_verified else "خیر"
            text = (
                "<b>حساب شما</b>\n"
                f"نام کاربری: <code>{html.escape(user.username or '-')}</code>\n"
                f"نام: <code>{html.escape(user.first_name or '-')}</code>\n"
                f"نام خانوادگی: <code>{html.escape(user.last_name or '-')}</code>\n"
                f"ایمیل: <code>{html.escape(user.email or '-')}</code>\n"
                f"موبایل: <code>{html.escape(user.phone_number or '-')}</code>\n"
                f"تأیید ایمیل: <code>{verified}</code>"
            )
        else:
            verified = "yes" if user.email_verified else "no"
            text = (
                "<b>Your account</b>\n"
                f"Username: <code>{html.escape(user.username or '-')}</code>\n"
                f"First name: <code>{html.escape(user.first_name or '-')}</code>\n"
                f"Last name: <code>{html.escape(user.last_name or '-')}</code>\n"
                f"Email: <code>{html.escape(user.email or '-')}</code>\n"
                f"Phone: <code>{html.escape(user.phone_number or '-')}</code>\n"
                f"Email verified: <code>{verified}</code>"
            )
        self.client.send_message(
            profile.chat_id,
            text,
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_forgot_password(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        email = command.args[0].strip() if command.args else ""
        user = None

        if email:
            user = User.objects.filter(email__iexact=email, is_active=True).first()
        elif profile.user_id and profile.is_verified:
            user = profile.user
        else:
            self.start_forgot_password_flow(profile)
            return

        if user:
            AccountLogicRepository().send_verification_forget_password_code(user)

        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_sent"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_webapp(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        web_app_url = self.web_app_url()
        if not web_app_url:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "webapp_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        safe_url = html.escape(web_app_url, quote=True)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "webapp_open", url=safe_url),
            reply_markup=self.main_menu_keyboard(profile),
        )

    @classmethod
    def help_text(cls, profile: TelegramProfile | None = None) -> str:
        if cls.lang(profile) == cls.LANG_FA:
            return (
                "<b>گزینه‌های موجود</b>\n"
                "از دکمه‌های پایین استفاده کنید و نیازی به تایپ دستور نیست.\n\n"
                "🔗 <b>اتصال حساب</b> - اتصال حساب برنامه به تلگرام\n"
                "👤 <b>حساب من</b> - نمایش اطلاعات حساب متصل‌شده\n"
                "✅ <b>تأیید ایمیل</b> - ارسال و بررسی کد تأیید ایمیل\n"
                "🔐 <b>فراموشی رمز عبور</b> - ارسال کد بازیابی رمز عبور\n"
                "➕ <b>ساخت کاربر</b> - فقط برای ادمین\n"
                "🌐 <b>باز کردن برنامه</b> - باز کردن برنامه وب\n"
                "🌍 <b>زبان</b> - تغییر زبان ربات\n"
                "🚪 <b>قطع اتصال</b> - حذف اتصال تلگرام"
            )
        return (
            "<b>Available actions</b>\n"
            "Use the bottom keyboard buttons instead of typing commands.\n\n"
            "🔗 <b>Link account</b> - connect your app account\n"
            "👤 <b>My account</b> - show linked account\n"
            "✅ <b>Verify email</b> - send and confirm email verification code\n"
            "🔐 <b>Forgot password</b> - send a recovery code\n"
            "➕ <b>Create user</b> - admin only, create an app user\n"
            "🌐 <b>Open app</b> - open the configured web app\n"
            "🌍 <b>Language</b> - change bot language\n"
            "🚪 <b>Unlink</b> - remove the Telegram link"
        )

    @classmethod
    def unknown_command_text(cls, profile: TelegramProfile | None = None) -> str:
        return cls.t(profile, "unknown")

    @classmethod
    def menu_text(cls, profile: TelegramProfile) -> str:
        if profile.user_id and profile.is_verified:
            fallback = "کاربر" if cls.lang(profile) == cls.LANG_FA else "there"
            user_name = html.escape(profile.user.first_name or profile.user.username or fallback)
            return cls.t(profile, "menu_linked", name=user_name)
        return cls.t(profile, "menu_guest")

    @classmethod
    def main_menu_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        is_linked = bool(profile and profile.user_id and profile.is_verified)
        rows: list[list[dict[str, Any] | str]] = []

        if is_linked:
            if profile and cls.is_admin_profile(profile):
                rows.append([cls.button(profile, "create_user")])
            if profile and profile.user and not profile.user.email_verified:
                rows.append([cls.button(profile, "verify_email")])
            rows.append([cls.button(profile, "account"), cls.button(profile, "forgot_password")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile)])
            rows.append([cls.button(profile, "language"), cls.button(profile, "help")])
            rows.append([cls.button(profile, "unlink")])
        else:
            rows.append([cls.button(profile, "link")])
            rows.append([cls.button(profile, "forgot_password")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile)])
            rows.append([cls.button(profile, "language"), cls.button(profile, "help")])

        placeholder = "یک گزینه را انتخاب کنید" if cls.lang(profile) == cls.LANG_FA else "Choose an action"
        return cls.reply_keyboard(rows, placeholder=placeholder)

    @classmethod
    def cancel_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = "مقدار خواسته‌شده را ارسال کنید یا لغو کنید" if cls.lang(
            profile) == cls.LANG_FA else "Send the requested value or cancel"
        return cls.reply_keyboard(
            [[cls.button(profile, "main_menu"), cls.button(profile, "cancel")]],
            placeholder=placeholder,
        )

    @classmethod
    def confirm_create_user_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = "تأیید یا لغو" if cls.lang(profile) == cls.LANG_FA else "Confirm or cancel"
        return cls.reply_keyboard(
            [[cls.button(profile, "confirm_create"), cls.button(profile, "cancel")]],
            placeholder=placeholder,
        )

    @classmethod
    def confirm_unlink_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = "تأیید یا لغو" if cls.lang(profile) == cls.LANG_FA else "Confirm or cancel"
        return cls.reply_keyboard(
            [[cls.button(profile, "yes_unlink"), cls.button(profile, "cancel")]],
            placeholder=placeholder,
        )

    @classmethod
    def reply_keyboard(
            cls,
            rows: list[list[dict[str, Any] | str]],
            *,
            placeholder: str | None = None,
    ) -> dict[str, Any]:
        keyboard: list[list[dict[str, Any]]] = []
        for row in rows:
            keyboard_row: list[dict[str, Any]] = []
            for button in row:
                if isinstance(button, str):
                    keyboard_row.append({"text": button})
                else:
                    keyboard_row.append(button)
            keyboard.append(keyboard_row)

        reply_markup: dict[str, Any] = {
            "keyboard": keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "is_persistent": True,
        }
        if placeholder:
            reply_markup["input_field_placeholder"] = placeholder
        return reply_markup

    @staticmethod
    def web_app_url() -> str:
        return getattr(settings, "TELEGRAM_WEBAPP_URL", "")

    @classmethod
    def web_app_button(cls, profile: TelegramProfile | None = None) -> str:
        return cls.button(profile, "webapp")
