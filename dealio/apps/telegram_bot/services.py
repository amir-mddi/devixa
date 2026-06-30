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
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.common.helpers.validators.account_validators import (
    validate_english_username,
    validate_gmail_email,
    validate_iranian_phone_number,
    validate_persian_text,
)
from dealio.apps.common.email_service import send_html_email_async
from dealio.apps.telegram_bot.models import TelegramProfile
from dealio.apps.telegram_bot.repositories.bot_cache_repository import TelegramBotCacheRepository
from dealio.apps.telegram_bot.repositories.profile_repository import TelegramProfileRepository
from dealio.apps.telegram_bot.repositories.user_role_repository import TelegramUserRoleRepository
from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.vo.commerce_bot_vo import (
    TelegramBotAliasVO,
    TelegramBotButtonTextVO,
    TelegramBotCallbackVO,
    TelegramBotLanguageVO,
    TelegramBotMessageTextVO,
    TelegramBotStateVO,
)
from dealio.apps.telegram_bot.repositories.logic import TelegramCommerceBotLogicRepository
from dealio.apps.telegram_bot.repositories.logic.channel_sync_logic import ChannelSyncLogicRepository
from dealio.apps.courses.enums import CourseLevelEnum, CourseStatusEnum, ReviewStatusEnum


logger = logging.getLogger("dealio")
User = get_user_model()


@dataclass(frozen=True)
class TelegramCommand:
    name: str
    args: list[str]
    raw_text: str


# TelegramBotClient moved to repositories.adapters.telegram_api_adapter and is imported above.
class TelegramAccountLinkService:
    LINK_CODE_EXPIRATION_MINUTES = 10

    @staticmethod
    def generate_code() -> str:
        return str(secrets.randbelow(900000) + 100000)

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @classmethod
    def link_cache_key(cls, chat_id: int, user_id: str, provider: str = "telegram") -> str:
        return f"{provider}_link:{chat_id}:{user_id}"

    @classmethod
    def pending_user_cache_key(cls, chat_id: int, provider: str = "telegram") -> str:
        return f"{provider}_pending_link:{chat_id}"

    @classmethod
    def send_link_code(cls, *, email: str, chat_id: int, provider: str = "telegram") -> bool:
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return False

        code = cls.generate_code()
        timeout_seconds = cls.LINK_CODE_EXPIRATION_MINUTES * 60

        TelegramBotCacheRepository.set_value(cls.pending_user_cache_key(chat_id, provider), str(user.id), timeout=timeout_seconds)
        TelegramBotCacheRepository.set_value(cls.link_cache_key(chat_id, str(user.id), provider), cls.hash_code(code), timeout=timeout_seconds)

        profile = TelegramProfile.objects.filter(messenger_provider=provider, chat_id=chat_id).only("bot_language").first()
        language = TelegramBotLanguageVO.FA if profile and profile.bot_language == TelegramBotLanguageVO.FA else TelegramBotLanguageVO.EN
        is_fa = language == TelegramBotLanguageVO.FA
        subject = TelegramBotMessageTextVO.LINK_EMAIL_SUBJECT[language]
        user_name = user.first_name or user.username or TelegramBotMessageTextVO.DEFAULT_USER_NAME[language]

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
        provider = getattr(profile, "messenger_provider", "telegram")
        user_id = TelegramBotCacheRepository.get_value(cls.pending_user_cache_key(profile.chat_id, provider))
        if not user_id:
            return False

        saved_hash = TelegramBotCacheRepository.get_value(cls.link_cache_key(profile.chat_id, user_id, provider))
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

        TelegramBotCacheRepository.delete_value(cls.pending_user_cache_key(profile.chat_id, provider))
        TelegramBotCacheRepository.delete_value(cls.link_cache_key(profile.chat_id, user_id, provider))
        return True


class TelegramBotService:
    MESSENGER_PROVIDER = "telegram"
    CACHE_PREFIX = "telegram"
    # Callback constants are kept so old inline buttons still work after deployment.
    CALLBACK_MAIN_MENU = TelegramBotCallbackVO.MAIN_MENU
    CALLBACK_LINK = TelegramBotCallbackVO.LINK
    CALLBACK_ACCOUNT = TelegramBotCallbackVO.ACCOUNT
    CALLBACK_VERIFY_EMAIL = TelegramBotCallbackVO.VERIFY_EMAIL
    CALLBACK_FORGOT_PASSWORD = TelegramBotCallbackVO.FORGOT_PASSWORD
    CALLBACK_CREATE_USER = TelegramBotCallbackVO.CREATE_USER
    CALLBACK_WEBAPP = TelegramBotCallbackVO.WEBAPP
    CALLBACK_LANGUAGE = TelegramBotCallbackVO.LANGUAGE
    CALLBACK_LANG_EN = TelegramBotCallbackVO.LANG_EN
    CALLBACK_LANG_FA = TelegramBotCallbackVO.LANG_FA
    CALLBACK_HELP = TelegramBotCallbackVO.HELP
    CALLBACK_CHANNELS = getattr(TelegramBotCallbackVO, "CHANNELS", "menu:channels")
    CALLBACK_COURSES = TelegramBotCallbackVO.COURSES
    CALLBACK_MY_COURSES = TelegramBotCallbackVO.MY_COURSES
    CALLBACK_MY_ORDERS = TelegramBotCallbackVO.MY_ORDERS
    CALLBACK_REVIEW_QUEUE = TelegramBotCallbackVO.REVIEW_QUEUE
    CALLBACK_UNLINK_ASK = TelegramBotCallbackVO.UNLINK_ASK
    CALLBACK_UNLINK_CONFIRM = TelegramBotCallbackVO.UNLINK_CONFIRM
    CALLBACK_CANCEL = TelegramBotCallbackVO.CANCEL

    LANG_EN = TelegramBotLanguageVO.EN
    LANG_FA = TelegramBotLanguageVO.FA
    SUPPORTED_LANGUAGES = TelegramBotLanguageVO.SUPPORTED

    LANGUAGE_BUTTONS = TelegramBotButtonTextVO.LANGUAGE_BUTTONS

    # English constants are kept for backward compatibility with old keyboards.
    BTN_LINK = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["link"]
    BTN_ACCOUNT = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["account"]
    BTN_VERIFY_EMAIL = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["verify_email"]
    BTN_FORGOT_PASSWORD = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["forgot_password"]
    BTN_CREATE_USER = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["create_user"]
    BTN_WEBAPP = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["webapp"]
    BTN_LANGUAGE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["language"]
    BTN_UNLINK = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["unlink"]
    BTN_HELP = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["help"]
    BTN_COURSES = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["courses"]
    BTN_MY_COURSES = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["my_courses"]
    BTN_MY_ORDERS = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["my_orders"]
    BTN_REVIEW_QUEUE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["review_queue"]
    BTN_ADMIN_COURSES = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["admin_courses"]
    BTN_CREATE_COURSE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["create_course"]
    BTN_MAIN_MENU = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["main_menu"]
    BTN_CANCEL = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["cancel"]
    BTN_YES_UNLINK = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["yes_unlink"]

    BUTTONS = TelegramBotButtonTextVO.BUTTONS

    STATE_LINK_EMAIL = TelegramBotStateVO.LINK_EMAIL
    STATE_LINK_CODE = TelegramBotStateVO.LINK_CODE
    STATE_VERIFY_EMAIL_CODE = TelegramBotStateVO.VERIFY_EMAIL_CODE
    STATE_FORGOT_PASSWORD_EMAIL = TelegramBotStateVO.FORGOT_PASSWORD_EMAIL
    STATE_CREATE_USERNAME = TelegramBotStateVO.CREATE_USERNAME
    STATE_CREATE_EMAIL = TelegramBotStateVO.CREATE_EMAIL
    STATE_CREATE_PHONE = TelegramBotStateVO.CREATE_PHONE
    STATE_CREATE_FIRST_NAME = TelegramBotStateVO.CREATE_FIRST_NAME
    STATE_CREATE_LAST_NAME = TelegramBotStateVO.CREATE_LAST_NAME
    STATE_CREATE_CONFIRM = TelegramBotStateVO.CREATE_CONFIRM
    STATE_UNLINK_CONFIRM = TelegramBotStateVO.UNLINK_CONFIRM
    STATE_REVIEW_RATING = TelegramBotStateVO.REVIEW_RATING
    STATE_REVIEW_TITLE = TelegramBotStateVO.REVIEW_TITLE
    STATE_REVIEW_COMMENT = TelegramBotStateVO.REVIEW_COMMENT
    STATE_COURSE_TITLE = TelegramBotStateVO.COURSE_TITLE
    STATE_COURSE_SHORT_DESCRIPTION = TelegramBotStateVO.COURSE_SHORT_DESCRIPTION
    STATE_COURSE_DESCRIPTION = TelegramBotStateVO.COURSE_DESCRIPTION
    STATE_COURSE_PRICE = TelegramBotStateVO.COURSE_PRICE
    STATE_COURSE_DURATION = TelegramBotStateVO.COURSE_DURATION
    STATE_COURSE_LEVEL = TelegramBotStateVO.COURSE_LEVEL
    STATE_COURSE_PUBLISH = TelegramBotStateVO.COURSE_PUBLISH
    STATE_LESSON_TITLE = TelegramBotStateVO.LESSON_TITLE
    STATE_LESSON_DESCRIPTION = TelegramBotStateVO.LESSON_DESCRIPTION
    STATE_LESSON_CONTENT = TelegramBotStateVO.LESSON_CONTENT
    STATE_LESSON_VIDEO_URL = TelegramBotStateVO.LESSON_VIDEO_URL
    STATE_LESSON_DURATION = TelegramBotStateVO.LESSON_DURATION
    STATE_LESSON_POSITION = TelegramBotStateVO.LESSON_POSITION
    STATE_LESSON_PREVIEW = TelegramBotStateVO.LESSON_PREVIEW

    ACTION_TIMEOUT_SECONDS = TelegramAccountLinkService.LINK_CODE_EXPIRATION_MINUTES * 60

    def __init__(self, client: TelegramBotClient | None = None):
        self.client = client or TelegramBotClient()
        self.link_service = TelegramAccountLinkService()
        self.commerce_logic = TelegramCommerceBotLogicRepository()
        self.channel_sync_logic = ChannelSyncLogicRepository()

    def handle_update(self, update: dict[str, Any]) -> None:
        channel_post = update.get("channel_post")
        if channel_post:
            self.channel_sync_logic.handle_telegram_channel_post(channel_post, is_edit=False)
            return

        edited_channel_post = update.get("edited_channel_post")
        if edited_channel_post:
            self.channel_sync_logic.handle_telegram_channel_post(edited_channel_post, is_edit=True)
            return

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
            self.client.send_message(chat_id, self.t(profile, "private_only"))
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
            self.clear_review_flow_data(profile.chat_id)
            self.clear_course_flow_data(profile.chat_id)
            self.clear_lesson_flow_data(profile.chat_id)
            self.client.send_message(
                chat_id,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if self.is_cancel_button(text):
            self.clear_action(profile.chat_id)
            self.clear_create_user_data(profile.chat_id)
            self.clear_review_flow_data(profile.chat_id)
            self.clear_course_flow_data(profile.chat_id)
            self.clear_lesson_flow_data(profile.chat_id)
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
            self.client.send_message(chat_id, self.t(profile, "private_only"))
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
            self.clear_review_flow_data(profile.chat_id)
            self.clear_course_flow_data(profile.chat_id)
            self.clear_lesson_flow_data(profile.chat_id)
            self.send_chain_message(
                profile,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
                message_id=message.get("message_id"),
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

        if data == getattr(self, "CALLBACK_CHANNELS", "menu:channels"):
            self.send_channels_invite(profile)
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
            self.clear_review_flow_data(profile.chat_id)
            self.clear_course_flow_data(profile.chat_id)
            self.clear_lesson_flow_data(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "canceled"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if self.handle_commerce_callback(profile, data, message_id=message.get("message_id")):
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
        texts = TelegramBotMessageTextVO.TEXTS
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
        if normalized in {
            self.normalize_button_text(self.LANGUAGE_BUTTONS[self.LANG_EN]),
            *TelegramBotAliasVO.LANGUAGE_EN_ALIASES,
        }:
            self.set_bot_language(profile, self.LANG_EN)
            return True
        if normalized in {
            self.normalize_button_text(self.LANGUAGE_BUTTONS[self.LANG_FA]),
            *TelegramBotAliasVO.LANGUAGE_FA_ALIASES,
        }:
            self.set_bot_language(profile, self.LANG_FA)
            return True
        return False

    @classmethod
    def language_keyboard(cls) -> dict[str, Any]:
        return cls.reply_keyboard(
            [[cls.LANGUAGE_BUTTONS[cls.LANG_FA], cls.LANGUAGE_BUTTONS[cls.LANG_EN]]],
            placeholder=cls.t(None, "placeholder_language"),
        )

    @classmethod
    def is_cancel_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in TelegramBotAliasVO.CANCEL_ALIASES | cls.all_button_texts("cancel")

    @classmethod
    def is_main_menu_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in TelegramBotAliasVO.MAIN_MENU_ALIASES | cls.all_button_texts("main_menu")

    @classmethod
    def is_yes_unlink_button(cls, text: str) -> bool:
        return cls.normalize_button_text(text) in TelegramBotAliasVO.YES_UNLINK_ALIASES | cls.all_button_texts("yes_unlink")

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
            "channels": lambda p: self.handle_channels(p, TelegramCommand(name="/channels", args=[], raw_text="/channels")),
            "courses": lambda p: self.send_course_list(p, page=1),
            "my_courses": self.send_my_courses,
            "my_orders": self.send_my_orders,
            "review_queue": self.send_review_queue,
            "admin_courses": lambda p: self.send_admin_course_list(p, page=1),
            "create_course": self.start_create_course_flow,
        }

        aliases = TelegramBotAliasVO.MENU_BUTTON_ALIASES

        for key, handler in action_by_key.items():
            possible = self.all_button_texts(key) | {self.normalize_button_text(item) for item in aliases[key]}
            if normalized in possible:
                handler(profile)
                return True

        return False

    @classmethod
    def _upsert_profile(cls, *, chat_id: int, telegram_user: dict[str, Any]) -> TelegramProfile:
        return TelegramProfileRepository.upsert(
            provider=cls.MESSENGER_PROVIDER,
            chat_id=chat_id,
            user_data=telegram_user,
        )

    @classmethod
    def action_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_bot_action:{chat_id}"

    @classmethod
    def set_action(cls, chat_id: int, action: str) -> None:
        TelegramBotCacheRepository.set_value(cls.action_cache_key(chat_id), action, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def get_action(cls, chat_id: int) -> str | None:
        return TelegramBotCacheRepository.get_value(cls.action_cache_key(chat_id))

    @classmethod
    def clear_action(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.action_cache_key(chat_id))

    @classmethod
    def create_user_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_create_user:{chat_id}"

    @classmethod
    def get_create_user_data(cls, chat_id: int) -> dict[str, str]:
        data = TelegramBotCacheRepository.get_value(cls.create_user_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_create_user_data(cls, chat_id: int, data: dict[str, str]) -> None:
        TelegramBotCacheRepository.set_value(cls.create_user_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_create_user_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.create_user_cache_key(chat_id))

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
        TelegramUserRoleRepository.ensure_default_user()

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

        if action == self.STATE_REVIEW_RATING:
            self.handle_review_rating_text(profile, text)
            return True

        if action == self.STATE_REVIEW_TITLE:
            self.handle_review_title_text(profile, text)
            return True

        if action == self.STATE_REVIEW_COMMENT:
            self.handle_review_comment_text(profile, text)
            return True


        if action == self.STATE_COURSE_TITLE:
            self.handle_course_title_text(profile, text)
            return True

        if action == self.STATE_COURSE_SHORT_DESCRIPTION:
            self.handle_course_short_description_text(profile, text)
            return True

        if action == self.STATE_COURSE_DESCRIPTION:
            self.handle_course_description_text(profile, text)
            return True

        if action == self.STATE_COURSE_PRICE:
            self.handle_course_price_text(profile, text)
            return True

        if action == self.STATE_COURSE_DURATION:
            self.handle_course_duration_text(profile, text)
            return True

        if action == self.STATE_COURSE_LEVEL:
            self.handle_course_level_text(profile, text)
            return True

        if action == self.STATE_COURSE_PUBLISH:
            self.handle_course_publish_text(profile, text)
            return True

        if action == self.STATE_LESSON_TITLE:
            self.handle_lesson_title_text(profile, text)
            return True

        if action == self.STATE_LESSON_DESCRIPTION:
            self.handle_lesson_description_text(profile, text)
            return True

        if action == self.STATE_LESSON_CONTENT:
            self.handle_lesson_content_text(profile, text)
            return True

        if action == self.STATE_LESSON_VIDEO_URL:
            self.handle_lesson_video_url_text(profile, text)
            return True

        if action == self.STATE_LESSON_DURATION:
            self.handle_lesson_duration_text(profile, text)
            return True

        if action == self.STATE_LESSON_POSITION:
            self.handle_lesson_position_text(profile, text)
            return True

        if action == self.STATE_LESSON_PREVIEW:
            self.handle_lesson_preview_text(profile, text)
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

        self.link_service.send_link_code(email=email, chat_id=profile.chat_id, provider=self.MESSENGER_PROVIDER)
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
                self.t(profile, "invalid_username_detail", error=html.escape(self.validation_message(error))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(username__iexact=username).exists():
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "username_exists"),
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
                self.t(profile, "invalid_create_email_detail", error=html.escape(self.validation_message(error))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(email__iexact=email).exists():
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "email_exists"),
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
                self.t(profile, "invalid_phone_detail", error=html.escape(self.validation_message(error))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if User.objects.filter(phone_number=phone_number).exists():
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "phone_exists"),
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
                self.t(profile, "invalid_first_name_detail", error=html.escape(self.validation_message(error))),
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
                self.t(profile, "invalid_last_name_detail", error=html.escape(self.validation_message(error))),
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
        if normalized not in TelegramBotAliasVO.CREATE_CONFIRM_ALIASES:
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
                self.t(profile, "create_failed", error=html.escape(str(error))),
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
        success_text = self.t(
            profile,
            "create_success",
            username=html.escape(user.username),
            email=html.escape(user.email),
            phone=html.escape(user.phone_number),
            follow_up=follow_up,
        )

        self.client.send_message(
            profile.chat_id,
            success_text,
            reply_markup=self.main_menu_keyboard(profile),
        )

    @classmethod
    def create_user_confirmation_text(cls, profile: TelegramProfile, data: dict[str, str]) -> str:
        return cls.t(
            profile,
            "create_confirm_text",
            username=html.escape(data.get("username", "-")),
            email=html.escape(data.get("email", "-")),
            phone=html.escape(data.get("phone_number", "-")),
            first_name=html.escape(data.get("first_name", "-")),
            last_name=html.escape(data.get("last_name", "-")),
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
        self.clear_review_flow_data(profile.chat_id)
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
                self.t(profile, "link_usage"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.link_service.send_link_code(email=email, chat_id=profile.chat_id, provider=self.MESSENGER_PROVIDER)
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
        verified = self.t(profile, "yes") if user.email_verified else self.t(profile, "no")
        text = self.t(
            profile,
            "account_text",
            username=html.escape(user.username or "-"),
            first_name=html.escape(user.first_name or "-"),
            last_name=html.escape(user.last_name or "-"),
            email=html.escape(user.email or "-"),
            phone=html.escape(user.phone_number or "-"),
            verified=verified,
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

    def handle_channels(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_channels_invite(profile)

    def send_channels_invite(self, profile: TelegramProfile) -> None:
        links = self.channel_invite_links(profile)
        if not links:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "channels_not_configured"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        keyboard = [[{"text": label, "url": url}] for label, url in links]
        keyboard.append([{"text": self.button(profile, "main_menu"), "callback_data": self.CALLBACK_MAIN_MENU}])
        self.send_chain_message(
            profile,
            self.t(profile, "channels_title"),
            reply_markup=self.inline_keyboard(keyboard),
        )

    def channel_invite_links(self, profile: TelegramProfile | None = None) -> list[tuple[str, str]]:
        values = [
            ("telegram_channel", os.environ.get("CHANNEL_INVITE_TELEGRAM_URL") or ""),
            ("bale_channel", os.environ.get("CHANNEL_INVITE_BALE_URL") or ""),
            ("rubika_channel", os.environ.get("CHANNEL_INVITE_RUBIKA_URL") or ""),
        ]
        return [(self.t(profile, key), url.strip()) for key, url in values if url.strip()]

    @classmethod
    def review_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_course_review:{chat_id}"

    @classmethod
    def get_review_flow_data(cls, chat_id: int) -> dict[str, Any]:
        data = TelegramBotCacheRepository.get_value(cls.review_flow_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_review_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.review_flow_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_review_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.review_flow_cache_key(chat_id))

    @staticmethod
    def compact_id(value: Any) -> str:
        return str(value)

    @staticmethod
    def parse_positive_int(value: str, default: int = 1) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return max(number, 1)

    @classmethod
    def chain_message_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_chain_message:{chat_id}"

    @classmethod
    def get_chain_message_id(cls, chat_id: int) -> int | None:
        value = TelegramBotCacheRepository.get_value(cls.chain_message_cache_key(chat_id))
        try:
            return int(value) if value else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def set_chain_message_id(cls, chat_id: int, message_id: int) -> None:
        TelegramBotCacheRepository.set_value(cls.chain_message_cache_key(chat_id), message_id, timeout=60 * 60 * 24)

    @classmethod
    def clear_chain_message_id(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.chain_message_cache_key(chat_id))

    def delete_chain_message(self, chat_id: int) -> None:
        message_id = self.get_chain_message_id(chat_id)
        if not message_id:
            return
        try:
            self.client.delete_message(chat_id, message_id)
        except Exception:
            logger.debug("Could not delete Telegram chain message", exc_info=True)
        self.clear_chain_message_id(chat_id)

    @staticmethod
    def telegram_message_id(response: dict[str, Any]) -> int | None:
        result = response.get("result") if isinstance(response, dict) else None
        if isinstance(result, dict):
            message_id = result.get("message_id")
            return int(message_id) if message_id else None
        return None

    def send_chain_message(
            self,
            profile: TelegramProfile,
            text: str,
            *,
            reply_markup: dict[str, Any] | None = None,
            message_id: int | None = None,
    ) -> None:
        """Replace the current commerce/admin navigation message instead of stacking bot messages.

        For inline callbacks Telegram can edit the clicked message. For reply-keyboard
        messages such as "My courses", the bot deletes the previous remembered chain
        message and sends one fresh message. This keeps related screens clean.
        """
        if message_id:
            try:
                self.client.edit_message_text(
                    profile.chat_id,
                    message_id,
                    text,
                    reply_markup=reply_markup,
                )
                self.set_chain_message_id(profile.chat_id, message_id)
                return
            except RuntimeError as error:
                message = str(error).lower()
                if "message is not modified" in message:
                    self.set_chain_message_id(profile.chat_id, message_id)
                    return
                logger.debug("Could not edit Telegram chain message; sending a new one", exc_info=True)

        previous_message_id = self.get_chain_message_id(profile.chat_id)
        if previous_message_id and previous_message_id != message_id:
            try:
                self.client.delete_message(profile.chat_id, previous_message_id)
            except Exception:
                logger.debug("Could not delete previous Telegram chain message", exc_info=True)

        response = self.client.send_message(profile.chat_id, text, reply_markup=reply_markup)
        sent_message_id = self.telegram_message_id(response)
        if sent_message_id:
            self.set_chain_message_id(profile.chat_id, sent_message_id)

    @classmethod
    def inline_keyboard(cls, rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
        return {"inline_keyboard": rows}

    @classmethod
    def inline_button(cls, text: str, callback_data: str) -> dict[str, str]:
        return {"text": text, "callback_data": callback_data}

    @classmethod
    def linked_user_or_none(cls, profile: TelegramProfile):
        if profile.user_id and profile.is_verified:
            return profile.user
        return None

    def require_linked_user(self, profile: TelegramProfile):
        user = self.linked_user_or_none(profile)
        if user:
            return user
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "course_login_required"),
            reply_markup=self.main_menu_keyboard(profile),
        )
        return None

    def handle_commerce_callback(self, profile: TelegramProfile, data: str, *, message_id: int | None = None) -> bool:
        if not data:
            return False

        parts = data.split(":")
        try:

            if len(parts) == 2 and parts[0] == "a" and parts[1] == "new":
                self.start_create_course_flow(profile)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "c":
                self.send_admin_course_list(profile, page=self.parse_positive_int(parts[2]), message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "d":
                self.send_admin_course_detail(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "p":
                self.update_course_status_from_bot(profile, course_id=parts[2], status=CourseStatusEnum.PUBLISHED.value, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "u":
                self.update_course_status_from_bot(profile, course_id=parts[2], status=CourseStatusEnum.DRAFT.value, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "x":
                self.update_course_status_from_bot(profile, course_id=parts[2], status=CourseStatusEnum.ARCHIVED.value, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "lc":
                self.start_lesson_flow(profile, parts[2])
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "l":
                self.send_course_list(profile, page=self.parse_positive_int(parts[2]), message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "d":
                self.send_course_detail(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "rv":
                self.send_course_reviews(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "ls":
                self.send_course_lessons(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "buy":
                self.checkout_course_from_bot(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "c" and parts[1] == "rr":
                self.start_course_review_flow(profile, parts[2])
                return True

            if data == "e:mine":
                self.send_my_courses(profile, message_id=message_id)
                return True

            if data == "o:mine":
                self.send_my_orders(profile, message_id=message_id)
                return True

            if data == "r:q":
                self.send_review_queue(profile, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "r" and parts[1] in {"a", "x"}:
                self.moderate_review_from_bot(profile, review_id=parts[2], approve=parts[1] == "a", message_id=message_id)
                return True
        except Exception as error:
            logger.exception("Telegram commerce callback failed")
            self.client.send_message(
                profile.chat_id,
                f"⚠️ {html.escape(self.validation_message(error))}",
                reply_markup=self.main_menu_keyboard(profile),
            )
            return True

        return False

    def send_course_list(self, profile: TelegramProfile, page: int = 1, *, message_id: int | None = None) -> None:
        courses, has_next = self.commerce_logic.list_courses(page=page, page_size=5)
        if not courses:
            self.send_chain_message(
                profile,
                self.t(profile, "courses_empty"),
                reply_markup=self.main_menu_keyboard(profile),
                message_id=message_id,
            )
            return

        lines = [self.t(profile, "courses_heading")]
        keyboard: list[list[dict[str, Any]]] = []
        for index, course in enumerate(courses, start=((page - 1) * 5) + 1):
            rating = getattr(course, "average_rating", None)
            rating_text = f" ⭐ {float(rating):.1f}" if rating else ""
            lines.append(
                self.t(
                    profile,
                    "course_list_item",
                    index=index,
                    title=html.escape(course.title),
                    rating=rating_text,
                    description=html.escape(course.short_description or ""),
                    price=self.format_money(course.price, course.currency),
                )
            )
            keyboard.append([
                self.inline_button(
                    self.t(profile, "view_course_button", title=course.title[:35]),
                    f"c:d:{self.compact_id(course.id)}",
                )
            ])

        nav_row: list[dict[str, Any]] = []
        if page > 1:
            nav_row.append(self.inline_button(self.t(profile, "prev_button"), f"c:l:{page - 1}"))
        if has_next:
            nav_row.append(self.inline_button(self.t(profile, "next_button"), f"c:l:{page + 1}"))
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])

        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard(keyboard),
            message_id=message_id,
        )

    def send_course_detail(self, profile: TelegramProfile, course_id_or_slug: str, *, message_id: int | None = None) -> None:
        course = self.commerce_logic.get_course(course_id_or_slug)
        rating = getattr(course, "average_rating", None)
        rating_text = f"⭐ {float(rating):.1f}" if rating else "⭐ -"
        lessons_count = course.lessons.count() if hasattr(course, "lessons") else 0
        text = self.t(
            profile,
            "course_detail_text",
            title=html.escape(course.title),
            description=html.escape(course.short_description or course.description or ""),
            level=html.escape(course.level),
            duration=course.duration_minutes,
            lessons=lessons_count,
            rating=rating_text,
            price=self.format_money(course.price, course.currency),
        )
        course_id = self.compact_id(course.id)
        keyboard = [
            [
                self.inline_button(self.t(profile, "lessons_button"), f"c:ls:{course_id}"),
                self.inline_button(self.t(profile, "reviews_button"), f"c:rv:{course_id}"),
            ],
            [self.inline_button(self.t(profile, "buy_button"), f"c:buy:{course_id}")],
            [self.inline_button(self.t(profile, "write_review_button"), f"c:rr:{course_id}")],
            [self.inline_button(self.t(profile, "courses_back_button"), "c:l:1")],
        ]
        self.send_chain_message(profile, text, reply_markup=self.inline_keyboard(keyboard), message_id=message_id)

    def send_course_lessons(self, profile: TelegramProfile, course_id_or_slug: str, *, message_id: int | None = None) -> None:
        course = self.commerce_logic.get_course(course_id_or_slug)
        user = self.linked_user_or_none(profile)
        is_enrolled = False
        if user:
            is_enrolled = any(enrollment.course_id == course.id for enrollment in self.commerce_logic.list_enrollments(user, limit=200))

        lines = [self.t(profile, "lessons_heading", title=html.escape(course.title))]
        lessons = list(course.lessons.all()[:20])
        if not lessons:
            lines.append(self.t(profile, "no_lessons"))
        for lesson in lessons:
            lock = "🔓" if lesson.is_preview or is_enrolled else "🔒"
            lines.append(
                self.t(
                    profile,
                    "lesson_item",
                    lock=lock,
                    position=lesson.position,
                    title=html.escape(lesson.title),
                    duration=lesson.duration_minutes,
                )
            )
            if lesson.is_preview or is_enrolled:
                description = lesson.description or lesson.content[:200]
                if description:
                    lines.append(html.escape(description))
                if lesson.video_url:
                    lines.append(self.t(profile, "video_line", url=html.escape(lesson.video_url)))
        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard([[self.inline_button(self.t(profile, "course_back_button"), f"c:d:{self.compact_id(course.id)}")]]),
            message_id=message_id,
        )

    def send_course_reviews(self, profile: TelegramProfile, course_id_or_slug: str, *, message_id: int | None = None) -> None:
        course = self.commerce_logic.get_course(course_id_or_slug)
        reviews = self.commerce_logic.list_reviews(course.id, limit=5)
        lines = [self.t(profile, "reviews_heading", title=html.escape(course.title))]
        if not reviews:
            lines.append(self.t(profile, "reviews_empty"))
        for review in reviews:
            reviewer_name = html.escape(review.user.first_name or review.user.username or TelegramBotMessageTextVO.DEFAULT_USER_NAME[self.lang(profile)])
            title = f" - {html.escape(review.title)}" if review.title else ""
            lines.append(
                self.t(
                    profile,
                    "review_item",
                    rating=review.rating,
                    title=title,
                    user=reviewer_name,
                    comment=html.escape(review.comment),
                )
            )
        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard([
                [self.inline_button(self.t(profile, "write_review_button"), f"c:rr:{self.compact_id(course.id)}")],
                [self.inline_button(self.t(profile, "course_back_button"), f"c:d:{self.compact_id(course.id)}")],
            ]),
            message_id=message_id,
        )

    def checkout_course_from_bot(self, profile: TelegramProfile, course_id: str, *, message_id: int | None = None) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        try:
            order, payment, paid_now = self.commerce_logic.checkout_course(user=user, course_id=course_id)
        except Exception as error:
            message = self.validation_message(error)
            if "already" in message.lower():
                message = self.t(profile, "course_already_owned")
            self.client.send_message(
                profile.chat_id,
                f"⚠️ {html.escape(message)}",
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if paid_now:
            message = self.t(profile, "payment_success")
        elif payment and payment.provider == "manual":
            message = self.t(profile, "payment_manual")
        else:
            message = self.t(profile, "payment_created")

        self.send_chain_message(
            profile,
            self.order_payment_text(profile, order, payment, message),
            reply_markup=self.inline_keyboard([
                [
                    self.inline_button(self.t(profile, "payment_my_courses_button"), "e:mine"),
                    self.inline_button(self.t(profile, "payment_my_orders_button"), "o:mine"),
                ],
                [self.inline_button(self.t(profile, "course_back_button"), f"c:d:{course_id}")],
            ]),
            message_id=message_id,
        )

    def send_my_courses(self, profile: TelegramProfile, *, message_id: int | None = None) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        enrollments = self.commerce_logic.list_enrollments(user=user, limit=10)
        if not enrollments:
            self.send_chain_message(
                profile,
                self.t(profile, "my_courses_empty"),
                reply_markup=self.main_menu_keyboard(profile),
                message_id=message_id,
            )
            return
        lines = [self.t(profile, "my_courses_heading")]
        keyboard: list[list[dict[str, Any]]] = []
        for enrollment in enrollments:
            course = enrollment.course
            lines.append(
                self.t(
                    profile,
                    "enrollment_item",
                    title=html.escape(course.title),
                    status=html.escape(enrollment.status),
                    enrolled_at=f"{enrollment.enrolled_at:%Y-%m-%d}",
                )
            )
            keyboard.append([self.inline_button(self.t(profile, "open_course_button", title=course.title[:30]), f"c:d:{self.compact_id(course.id)}")])
        self.send_chain_message(profile, "\n".join(lines), reply_markup=self.inline_keyboard(keyboard), message_id=message_id)

    def send_my_orders(self, profile: TelegramProfile, *, message_id: int | None = None) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        orders = self.commerce_logic.list_orders(user=user, limit=10)
        if not orders:
            self.send_chain_message(profile, self.t(profile, "orders_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        lines = [self.t(profile, "my_orders_heading")]
        for order in orders:
            course_titles = ", ".join(item.course_title for item in order.items.all()) or "-"
            lines.append(
                self.t(
                    profile,
                    "order_item",
                    order_number=html.escape(order.order_number),
                    courses=html.escape(course_titles),
                    status=html.escape(order.status),
                    total=self.format_money(order.total_amount, order.currency),
                )
            )
        self.send_chain_message(profile, "\n".join(lines), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)

    def start_course_review_flow(self, profile: TelegramProfile, course_id: str) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        self.set_review_flow_data(profile.chat_id, {"course_id": course_id})
        self.set_action(profile.chat_id, self.STATE_REVIEW_RATING)
        self.delete_chain_message(profile.chat_id)
        self.client.send_message(profile.chat_id, self.t(profile, "review_rating_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_review_rating_text(self, profile: TelegramProfile, text: str) -> None:
        try:
            rating = int(text.strip())
        except ValueError:
            rating = 0
        if rating < 1 or rating > 5:
            self.client.send_message(profile.chat_id, self.t(profile, "review_rating_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_review_flow_data(profile.chat_id)
        data["rating"] = rating
        data["title"] = ""
        self.set_review_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_REVIEW_COMMENT)
        self.client.send_message(profile.chat_id, self.t(profile, "review_comment_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_review_title_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_review_flow_data(profile.chat_id)
        title = "" if text.strip() == "-" else text.strip()[:180]
        data["title"] = title
        self.set_review_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_REVIEW_COMMENT)
        self.client.send_message(profile.chat_id, self.t(profile, "review_comment_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_review_comment_text(self, profile: TelegramProfile, text: str) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        data = self.get_review_flow_data(profile.chat_id)
        comment = text.strip()
        if len(comment) < 5:
            self.client.send_message(profile.chat_id, self.t(profile, "review_comment_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        try:
            review = self.commerce_logic.submit_review(
                user=user,
                course_id=data.get("course_id"),
                rating=int(data.get("rating", 0)),
                title=data.get("title", ""),
                comment=comment,
            )
        except Exception as error:
            logger.exception("Telegram review submission failed")
            self.client.send_message(
                profile.chat_id,
                f"⚠️ {html.escape(self.validation_message(error))}",
                reply_markup=self.main_menu_keyboard(profile),
            )
            self.clear_action(profile.chat_id)
            self.clear_review_flow_data(profile.chat_id)
            return

        self.clear_action(profile.chat_id)
        self.clear_review_flow_data(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "review_saved_with_id", message=self.t(profile, "review_pending"), review_id=html.escape(str(review.id))),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def send_review_queue(self, profile: TelegramProfile, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        reviews = self.commerce_logic.list_pending_reviews(limit=10)
        if not reviews:
            self.send_chain_message(profile, self.t(profile, "review_queue_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        lines = [self.t(profile, "review_queue_heading")]
        keyboard: list[list[dict[str, Any]]] = []
        for review in reviews:
            user_name = html.escape(review.user.first_name or review.user.username or TelegramBotMessageTextVO.DEFAULT_USER_NAME[self.lang(profile)])
            lines.append(
                self.t(
                    profile,
                    "pending_review_item",
                    course=html.escape(review.course.title),
                    user=user_name,
                    rating=review.rating,
                    comment=html.escape(review.comment[:250]),
                )
            )
            keyboard.append([
                self.inline_button(self.t(profile, "approve_button"), f"r:a:{self.compact_id(review.id)}"),
                self.inline_button(self.t(profile, "reject_button"), f"r:x:{self.compact_id(review.id)}"),
            ])
        keyboard.append([self.inline_button(self.t(profile, "refresh_button"), "r:q")])
        self.send_chain_message(profile, "\n".join(lines), reply_markup=self.inline_keyboard(keyboard), message_id=message_id)

    def moderate_review_from_bot(self, profile: TelegramProfile, *, review_id: str, approve: bool, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        status = ReviewStatusEnum.APPROVED.value if approve else ReviewStatusEnum.REJECTED.value
        review = self.commerce_logic.moderate_review(
            admin_user=profile.user,
            review_id=review_id,
            status=status,
            admin_note=self.t(profile, "admin_review_note"),
        )
        self.send_chain_message(
            profile,
            self.t(profile, "review_moderated", review_id=html.escape(str(review.id)), status=html.escape(status)),
            reply_markup=self.inline_keyboard([[self.inline_button(self.t(profile, "back_to_queue_button"), "r:q")]]),
            message_id=message_id,
        )

    @classmethod
    def format_money(cls, amount: Any, currency: str) -> str:
        return f"{amount:,.0f} {currency}" if str(currency).upper() == "IRR" else f"{amount:,.2f} {currency}"

    @classmethod
    def order_payment_text(cls, profile: TelegramProfile, order, payment, title: str) -> str:
        lines = [f"<b>{html.escape(title)}</b>"]
        lines.append(cls.t(profile, "order_payment_order", order_number=html.escape(order.order_number)))
        lines.append(cls.t(profile, "order_payment_status", status=html.escape(order.status)))
        lines.append(cls.t(profile, "order_payment_total", total=cls.format_money(order.total_amount, order.currency)))
        if payment:
            lines.append(cls.t(profile, "order_payment_payment", payment_number=html.escape(payment.payment_number)))
            lines.append(cls.t(profile, "order_payment_provider", provider=html.escape(payment.provider)))
            lines.append(cls.t(profile, "order_payment_payment_status", status=html.escape(payment.status)))
            if payment.payment_url:
                lines.append(cls.t(profile, "order_payment_url", url=html.escape(payment.payment_url)))
        return "\n".join(lines)

    def handle_courses(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_course_list(profile, page=1)

    def handle_my_courses(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_my_courses(profile)

    def handle_orders(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_my_orders(profile)

    def handle_my_orders(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_my_orders(profile)

    def handle_review_queue(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_review_queue(profile)


    @classmethod
    def course_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_admin_course:{chat_id}"

    @classmethod
    def get_course_flow_data(cls, chat_id: int) -> dict[str, Any]:
        data = TelegramBotCacheRepository.get_value(cls.course_flow_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_course_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.course_flow_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_course_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.course_flow_cache_key(chat_id))

    @classmethod
    def lesson_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_admin_lesson:{chat_id}"

    @classmethod
    def get_lesson_flow_data(cls, chat_id: int) -> dict[str, Any]:
        data = TelegramBotCacheRepository.get_value(cls.lesson_flow_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_lesson_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.lesson_flow_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_lesson_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.lesson_flow_cache_key(chat_id))

    @staticmethod
    def parse_decimal_amount(text: str) -> float | None:
        normalized = text.strip().replace(",", "")
        try:
            value = float(normalized)
        except ValueError:
            return None
        return value if value >= 0 else None

    @staticmethod
    def parse_optional_positive_int(text: str) -> int | None:
        value = text.strip()
        if value == "-":
            return None
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def parse_yes_no(text: str) -> bool | None:
        normalized = text.strip().casefold()
        if normalized in TelegramBotAliasVO.YES_ALIASES:
            return True
        if normalized in TelegramBotAliasVO.NO_ALIASES:
            return False
        return None

    def start_create_course_flow(self, profile: TelegramProfile) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_course_flow_data(profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_COURSE_TITLE)
        self.client.send_message(profile.chat_id, self.t(profile, "course_create_start"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_title_text(self, profile: TelegramProfile, text: str) -> None:
        title = text.strip()
        if len(title) < 3 or len(title) > 180:
            self.client.send_message(profile.chat_id, self.t(profile, "course_title_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        self.set_course_flow_data(profile.chat_id, {"title": title})
        self.set_action(profile.chat_id, self.STATE_COURSE_SHORT_DESCRIPTION)
        self.client.send_message(profile.chat_id, self.t(profile, "course_short_description_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_short_description_text(self, profile: TelegramProfile, text: str) -> None:
        short_description = text.strip()
        if len(short_description) > 300:
            self.client.send_message(profile.chat_id, self.t(profile, "course_short_description_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_course_flow_data(profile.chat_id)
        data["short_description"] = short_description
        self.set_course_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_COURSE_DESCRIPTION)
        self.client.send_message(profile.chat_id, self.t(profile, "course_description_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_description_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_course_flow_data(profile.chat_id)
        data["description"] = "" if text.strip() == "-" else text.strip()
        self.set_course_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_COURSE_PRICE)
        self.client.send_message(profile.chat_id, self.t(profile, "course_price_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_price_text(self, profile: TelegramProfile, text: str) -> None:
        price = self.parse_decimal_amount(text)
        if price is None:
            self.client.send_message(profile.chat_id, self.t(profile, "course_price_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_course_flow_data(profile.chat_id)
        data["price"] = price
        data["currency"] = "irr"
        self.set_course_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_COURSE_DURATION)
        self.client.send_message(profile.chat_id, self.t(profile, "course_duration_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_duration_text(self, profile: TelegramProfile, text: str) -> None:
        duration = self.parse_optional_positive_int(text)
        if duration is None and text.strip() != "0":
            self.client.send_message(profile.chat_id, self.t(profile, "course_duration_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_course_flow_data(profile.chat_id)
        data["duration_minutes"] = duration or 0
        self.set_course_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_COURSE_LEVEL)
        self.client.send_message(profile.chat_id, self.t(profile, "course_level_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_level_text(self, profile: TelegramProfile, text: str) -> None:
        level = text.strip().lower()
        allowed = {item.value for item in CourseLevelEnum}
        if level not in allowed:
            self.client.send_message(profile.chat_id, self.t(profile, "course_level_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_course_flow_data(profile.chat_id)
        data["level"] = level
        self.set_course_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_COURSE_PUBLISH)
        self.client.send_message(profile.chat_id, self.t(profile, "course_publish_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_course_publish_text(self, profile: TelegramProfile, text: str) -> None:
        should_publish = self.parse_yes_no(text)
        if should_publish is None:
            self.client.send_message(profile.chat_id, self.t(profile, "course_publish_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_course_flow_data(profile.chat_id)
        status = CourseStatusEnum.PUBLISHED.value if should_publish else CourseStatusEnum.DRAFT.value
        try:
            course = self.commerce_logic.create_course(
                admin_user=profile.user,
                title=data.get("title", ""),
                short_description=data.get("short_description", ""),
                description=data.get("description", ""),
                price=float(data.get("price", 0)),
                currency=data.get("currency", "irr"),
                level=data.get("level", CourseLevelEnum.ALL_LEVELS.value),
                duration_minutes=int(data.get("duration_minutes", 0)),
                status=status,
            )
        except Exception as error:
            logger.exception("Telegram course creation failed")
            self.client.send_message(profile.chat_id, f"⚠️ {html.escape(self.validation_message(error))}", reply_markup=self.main_menu_keyboard(profile))
            self.clear_action(profile.chat_id)
            self.clear_course_flow_data(profile.chat_id)
            return
        self.clear_action(profile.chat_id)
        self.clear_course_flow_data(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            f"{self.t(profile, 'course_created')}\n\n{self.admin_course_text(profile, course)}",
            reply_markup=self.admin_course_keyboard(profile, course),
        )

    def start_lesson_flow(self, profile: TelegramProfile, course_id: str) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_lesson_flow_data(profile.chat_id)
        self.set_lesson_flow_data(profile.chat_id, {"course_id": course_id})
        self.set_action(profile.chat_id, self.STATE_LESSON_TITLE)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_create_start"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_title_text(self, profile: TelegramProfile, text: str) -> None:
        title = text.strip()
        if len(title) < 2 or len(title) > 180:
            self.client.send_message(profile.chat_id, self.t(profile, "lesson_title_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_lesson_flow_data(profile.chat_id)
        data["title"] = title
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_DESCRIPTION)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_description_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_description_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_lesson_flow_data(profile.chat_id)
        data["description"] = "" if text.strip() == "-" else text.strip()
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_CONTENT)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_content_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_content_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_lesson_flow_data(profile.chat_id)
        data["content"] = "" if text.strip() == "-" else text.strip()
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_VIDEO_URL)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_video_url_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_video_url_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_lesson_flow_data(profile.chat_id)
        data["video_url"] = "" if text.strip() == "-" else text.strip()
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_DURATION)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_duration_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_duration_text(self, profile: TelegramProfile, text: str) -> None:
        duration = self.parse_optional_positive_int(text)
        if duration is None and text.strip() != "0":
            self.client.send_message(profile.chat_id, self.t(profile, "lesson_duration_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_lesson_flow_data(profile.chat_id)
        data["duration_minutes"] = duration or 0
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_POSITION)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_position_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_position_text(self, profile: TelegramProfile, text: str) -> None:
        position = self.parse_optional_positive_int(text)
        if position is None and text.strip() != "-":
            self.client.send_message(profile.chat_id, self.t(profile, "lesson_position_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_lesson_flow_data(profile.chat_id)
        data["position"] = position
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_PREVIEW)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_preview_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_preview_text(self, profile: TelegramProfile, text: str) -> None:
        is_preview = self.parse_yes_no(text)
        if is_preview is None:
            self.client.send_message(profile.chat_id, self.t(profile, "lesson_preview_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_lesson_flow_data(profile.chat_id)
        try:
            lesson = self.commerce_logic.create_lesson(
                admin_user=profile.user,
                course_id=data.get("course_id"),
                title=data.get("title", ""),
                description=data.get("description", ""),
                content=data.get("content", ""),
                video_url=data.get("video_url", ""),
                duration_minutes=int(data.get("duration_minutes", 0)),
                position=data.get("position"),
                is_preview=is_preview,
            )
        except Exception as error:
            logger.exception("Telegram lesson creation failed")
            self.client.send_message(profile.chat_id, f"⚠️ {html.escape(self.validation_message(error))}", reply_markup=self.main_menu_keyboard(profile))
            self.clear_action(profile.chat_id)
            self.clear_lesson_flow_data(profile.chat_id)
            return
        self.clear_action(profile.chat_id)
        self.clear_lesson_flow_data(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "lesson_created_detail", message=self.t(profile, "lesson_created"), title=html.escape(lesson.title), course=html.escape(lesson.course.title), position=lesson.position),
            reply_markup=self.admin_course_keyboard(profile, lesson.course),
        )

    def send_admin_course_list(self, profile: TelegramProfile, page: int = 1, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        courses, has_next = self.commerce_logic.list_admin_courses(page=page, page_size=5)
        if not courses:
            self.send_chain_message(
                profile,
                self.t(profile, "admin_courses_empty"),
                reply_markup=self.inline_keyboard([[self.inline_button(self.button(profile, "create_course"), "a:new")]]),
                message_id=message_id,
            )
            return
        lines = [self.t(profile, "admin_courses_heading")]
        keyboard: list[list[dict[str, Any]]] = []
        for index, course in enumerate(courses, start=((page - 1) * 5) + 1):
            lines.append(
                self.t(
                    profile,
                    "admin_course_list_item",
                    index=index,
                    title=html.escape(course.title),
                    status=html.escape(course.status),
                    price=self.format_money(course.price, course.currency),
                )
            )
            keyboard.append([self.inline_button(self.t(profile, "manage_course_button", title=course.title[:30]), f"a:d:{self.compact_id(course.id)}")])
        pagination_row: list[dict[str, Any]] = []
        if page > 1:
            pagination_row.append(self.inline_button(self.t(profile, "prev_button"), f"a:c:{page - 1}"))
        if has_next:
            pagination_row.append(self.inline_button(self.t(profile, "next_button"), f"a:c:{page + 1}"))
        if pagination_row:
            keyboard.append(pagination_row)
        keyboard.append([self.inline_button(self.button(profile, "create_course"), "a:new")])
        self.send_chain_message(profile, "\n".join(lines), reply_markup=self.inline_keyboard(keyboard), message_id=message_id)

    def send_admin_course_detail(self, profile: TelegramProfile, course_id_or_slug: str, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        course = self.commerce_logic.get_admin_course(course_id_or_slug)
        self.send_chain_message(profile, self.admin_course_text(profile, course), reply_markup=self.admin_course_keyboard(profile, course), message_id=message_id)

    def update_course_status_from_bot(self, profile: TelegramProfile, *, course_id: str, status: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            course = self.commerce_logic.update_course_status(admin_user=profile.user, course_id=course_id, status=status)
        except Exception as error:
            logger.exception("Telegram course status update failed")
            self.client.send_message(profile.chat_id, f"⚠️ {html.escape(self.validation_message(error))}", reply_markup=self.main_menu_keyboard(profile))
            return
        self.send_chain_message(
            profile,
            f"{self.t(profile, 'course_status_updated')}\n\n{self.admin_course_text(profile, course)}",
            reply_markup=self.admin_course_keyboard(profile, course),
            message_id=message_id,
        )

    def admin_course_text(self, profile: TelegramProfile, course) -> str:
        lessons_count = course.lessons.filter(is_deleted=False).count() if hasattr(course, "lessons") else 0
        return self.t(
            profile,
            "admin_course_text",
            title=html.escape(course.title),
            status=html.escape(course.status),
            slug=html.escape(course.slug),
            level=html.escape(course.level),
            duration=course.duration_minutes,
            lessons=lessons_count,
            price=self.format_money(course.price, course.currency),
            description=html.escape(course.short_description or ""),
        )

    def admin_course_keyboard(self, profile: TelegramProfile, course) -> dict[str, Any]:
        course_id = self.compact_id(course.id)
        rows: list[list[dict[str, Any]]] = []
        rows.append([self.inline_button(self.t(profile, "add_lesson_button"), f"a:lc:{course_id}")])
        if course.status != CourseStatusEnum.PUBLISHED.value:
            rows.append([self.inline_button(self.t(profile, "publish_button"), f"a:p:{course_id}")])
        else:
            rows.append([self.inline_button(self.t(profile, "unpublish_button"), f"a:u:{course_id}")])
        if course.status != CourseStatusEnum.ARCHIVED.value:
            rows.append([self.inline_button(self.t(profile, "archive_button"), f"a:x:{course_id}")])
        rows.append([
            self.inline_button(self.t(profile, "public_view_button"), f"c:d:{course_id}"),
            self.inline_button(self.t(profile, "all_courses_button"), "a:c:1"),
        ])
        return self.inline_keyboard(rows)

    def handle_admin_courses(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_admin_course_list(profile, page=1)

    def handle_create_course(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.start_create_course_flow(profile)

    @classmethod
    def help_text(cls, profile: TelegramProfile | None = None) -> str:
        return cls.t(profile, "help_text")

    @classmethod
    def unknown_command_text(cls, profile: TelegramProfile | None = None) -> str:
        return cls.t(profile, "unknown")

    @classmethod
    def menu_text(cls, profile: TelegramProfile) -> str:
        if profile.user_id and profile.is_verified:
            fallback = TelegramBotMessageTextVO.DEFAULT_USER_NAME[cls.lang(profile)]
            user_name = html.escape(profile.user.first_name or profile.user.username or fallback)
            return cls.t(profile, "menu_linked", name=user_name)
        return cls.t(profile, "menu_guest")

    @classmethod
    def main_menu_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        is_linked = bool(profile and profile.user_id and profile.is_verified)
        rows: list[list[dict[str, Any] | str]] = []

        if is_linked:
            rows.append([cls.button(profile, "courses"), cls.button(profile, "my_courses")])
            rows.append([cls.button(profile, "my_orders")])
            if profile and cls.is_admin_profile(profile):
                rows.append([cls.button(profile, "admin_courses"), cls.button(profile, "create_course")])
                rows.append([cls.button(profile, "create_user"), cls.button(profile, "review_queue")])
            if profile and profile.user and not profile.user.email_verified:
                rows.append([cls.button(profile, "verify_email")])
            rows.append([cls.button(profile, "account"), cls.button(profile, "forgot_password")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile)])
            rows.append([cls.button(profile, "channels"), cls.button(profile, "help")])
            rows.append([cls.button(profile, "language")])
            rows.append([cls.button(profile, "unlink")])
        else:
            rows.append([cls.button(profile, "courses")])
            rows.append([cls.button(profile, "link")])
            rows.append([cls.button(profile, "forgot_password")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile)])
            rows.append([cls.button(profile, "channels"), cls.button(profile, "help")])
            rows.append([cls.button(profile, "language")])

        placeholder = cls.t(profile, "placeholder_main_menu")
        return cls.reply_keyboard(rows, placeholder=placeholder)

    @classmethod
    def cancel_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = cls.t(profile, "placeholder_cancel")
        return cls.reply_keyboard(
            [[cls.button(profile, "main_menu"), cls.button(profile, "cancel")]],
            placeholder=placeholder,
        )

    @classmethod
    def confirm_create_user_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = cls.t(profile, "placeholder_confirm")
        return cls.reply_keyboard(
            [[cls.button(profile, "confirm_create"), cls.button(profile, "cancel")]],
            placeholder=placeholder,
        )

    @classmethod
    def confirm_unlink_keyboard(cls, profile: TelegramProfile | None = None) -> dict[str, Any]:
        placeholder = cls.t(profile, "placeholder_confirm")
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
        return os.environ.get("TELEGRAM_WEBAPP_URL") or ""

    @classmethod
    def web_app_button(cls, profile: TelegramProfile | None = None) -> str:
        return cls.button(profile, "webapp")
