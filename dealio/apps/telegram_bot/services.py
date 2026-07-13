import html
import json
from dealio.apps.common.utils.common_utils import CommonUtils
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from dealio.apps.accounts.dtos.password_recovery_dto import (
    SendPasswordRecoveryCodeDTO,
    SendSmsPasswordRecoveryCodeDTO,
)
from dealio.apps.accounts.dtos.phone_verification_dto import (
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberByTelegramDTO,
    VerifyPhoneNumberDTO,
)
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.accounts.repositories.adapters.verification_code_cache_adapter import VerificationCodeCacheAdapter
from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationErrorCodeVO,
)
from dealio.apps.common.helpers.validators.account_validators import (
    validate_english_username,
    validate_gmail_email,
    validate_iranian_phone_number,
    validate_persian_text,
)
from dealio.apps.common.email_service import send_html_email_async
from dealio.apps.common.project_config import get_project_name
from dealio.apps.telegram_bot.dtos.account_link_dtos import (
    ConfirmBotAccountLinkCodeDTO,
    SendBotAccountLinkCodeDTO,
)
from dealio.apps.telegram_bot.dtos.profile_dtos import DisconnectMessengerProfileDTO
from dealio.apps.telegram_bot.logic.profile_logic import MessengerProfileLogic
from dealio.apps.telegram_bot.models import BotSupportTicket, TelegramProfile
from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.bot_cache_repository import TelegramBotCacheRepository
from dealio.apps.telegram_bot.repositories.profile_repository import TelegramProfileRepository
from dealio.apps.telegram_bot.repositories.user_role_repository import TelegramUserRoleRepository
from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.vo.commerce_bot_vo import (
    TelegramBotAliasVO,
    TelegramBotButtonTextVO,
    TelegramBotCallbackVO,
    TelegramBotIconKeyVO,
    TelegramBotIconVO,
    TelegramBotLanguageVO,
    TelegramBotMessageTextVO,
    TelegramBotStateVO,
    TelegramCommerceFeatureVO,
)
from dealio.apps.telegram_bot.repositories.logic import TelegramCommerceBotLogicRepository
from dealio.apps.telegram_bot.repositories.logic.account_link_logic import (
    BotAccountLinkLogicRepository,
)
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider, BotSettingLogicRepository
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import BotNotificationLogicRepository
from dealio.apps.telegram_bot.repositories.logic.bot_support_logic import BotSupportLogicRepository
from dealio.apps.telegram_bot.vo.account_link_vo import BotAccountLinkVO
from dealio.apps.telegram_bot.vo.bot_setting_vo import BotSettingRegistryVO
from dealio.apps.telegram_bot.interfaces.commerce_bot_logic_interface import CommerceBotLogicInterface
from dealio.apps.telegram_bot.repositories.logic.channel_sync_logic import ChannelSyncLogicRepository
from dealio.apps.courses.enums import CourseLevelEnum, CourseStatusEnum, ReviewStatusEnum
from dealio.apps.billing.enums import CurrencyEnum, PaymentProviderEnum, PaymentReceiptStatusEnum, PaymentStatusEnum


logger = CommonUtils.get_project_logger(__name__)
User = get_user_model()


@dataclass(frozen=True)
class TelegramCommand:
    name: str
    args: list[str]
    raw_text: str


# TelegramBotClient moved to repositories.adapters.telegram_api_adapter and is imported above.
class TelegramBotService:
    MESSENGER_PROVIDER = "telegram"
    CACHE_PREFIX = "telegram"
    # Callback constants are kept so old inline buttons still work after deployment.
    CALLBACK_MAIN_MENU = TelegramBotCallbackVO.MAIN_MENU
    CALLBACK_LINK = TelegramBotCallbackVO.LINK
    CALLBACK_ACCOUNT = TelegramBotCallbackVO.ACCOUNT
    CALLBACK_VERIFY_EMAIL = TelegramBotCallbackVO.VERIFY_EMAIL
    CALLBACK_VERIFY_PHONE = TelegramBotCallbackVO.VERIFY_PHONE
    CALLBACK_FORGOT_PASSWORD = TelegramBotCallbackVO.FORGOT_PASSWORD
    CALLBACK_CREATE_USER = TelegramBotCallbackVO.CREATE_USER
    CALLBACK_WEBAPP = TelegramBotCallbackVO.WEBAPP
    CALLBACK_LANGUAGE = TelegramBotCallbackVO.LANGUAGE
    CALLBACK_LANG_EN = TelegramBotCallbackVO.LANG_EN
    CALLBACK_LANG_FA = TelegramBotCallbackVO.LANG_FA
    CALLBACK_HELP = TelegramBotCallbackVO.HELP
    CALLBACK_CHANNELS = getattr(TelegramBotCallbackVO, "CHANNELS", "menu:channels")
    CALLBACK_BOT_SETTINGS = getattr(TelegramBotCallbackVO, "BOT_SETTINGS", "bs:menu")
    CALLBACK_ADMIN_NOTIFICATION = getattr(TelegramBotCallbackVO, "ADMIN_NOTIFICATION", "ntf:menu")
    CALLBACK_ADMIN_NOTIFICATION_START = getattr(TelegramBotCallbackVO, "ADMIN_NOTIFICATION_START", "ntf:start")
    CALLBACK_ADMIN_NOTIFICATION_CONFIRM = getattr(TelegramBotCallbackVO, "ADMIN_NOTIFICATION_CONFIRM", "ntf:confirm")
    CALLBACK_ADMIN_NOTIFICATION_CONFIRM_NOW = getattr(TelegramBotCallbackVO, "ADMIN_NOTIFICATION_CONFIRM_NOW", "ntf:confirm_now")
    CALLBACK_ADMIN_NOTIFICATION_SCHEDULE = getattr(TelegramBotCallbackVO, "ADMIN_NOTIFICATION_SCHEDULE", "ntf:schedule")
    CALLBACK_DISCOUNTS = getattr(TelegramBotCallbackVO, "DISCOUNTS", "dsc:menu")
    CALLBACK_DISCOUNT_CREATE = getattr(TelegramBotCallbackVO, "DISCOUNT_CREATE", "dsc:create")
    CALLBACK_DISCOUNT_TYPE_PERCENT = getattr(TelegramBotCallbackVO, "DISCOUNT_TYPE_PERCENT", "dsc:type:percent")
    CALLBACK_DISCOUNT_TYPE_AMOUNT = getattr(TelegramBotCallbackVO, "DISCOUNT_TYPE_AMOUNT", "dsc:type:amount")
    CALLBACK_DISCOUNT_SCOPE_ALL = getattr(TelegramBotCallbackVO, "DISCOUNT_SCOPE_ALL", "dsc:scope:all")
    CALLBACK_DISCOUNT_USAGE_LIMIT_UNLIMITED = getattr(TelegramBotCallbackVO, "DISCOUNT_USAGE_LIMIT_UNLIMITED", "dsc:limit:none")
    CALLBACK_DISCOUNT_USAGE_LIMIT_CUSTOM = getattr(TelegramBotCallbackVO, "DISCOUNT_USAGE_LIMIT_CUSTOM", "dsc:limit:set")
    CALLBACK_SUPPORT = getattr(TelegramBotCallbackVO, "SUPPORT", "sup:menu")
    CALLBACK_SUPPORT_NEW = getattr(TelegramBotCallbackVO, "SUPPORT_NEW", "sup:new")
    CALLBACK_SUPPORT_QUEUE = getattr(TelegramBotCallbackVO, "SUPPORT_QUEUE", "sup:q")
    CALLBACK_COURSES = TelegramBotCallbackVO.COURSES
    CALLBACK_MY_COURSES = TelegramBotCallbackVO.MY_COURSES
    CALLBACK_MY_ORDERS = TelegramBotCallbackVO.MY_ORDERS
    CALLBACK_REVIEW_QUEUE = TelegramBotCallbackVO.REVIEW_QUEUE
    CALLBACK_PAYMENT_QUEUE = TelegramBotCallbackVO.PAYMENT_QUEUE
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
    BTN_VERIFY_PHONE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["verify_phone"]
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
    BTN_PAYMENT_QUEUE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["payment_queue"]
    BTN_ADMIN_COURSES = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["admin_courses"]
    BTN_BOT_SETTINGS = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["bot_settings"]
    BTN_ADMIN_NOTIFICATION = TelegramBotButtonTextVO.BUTTONS[LANG_EN].get("admin_notification", "Send notification")
    BTN_CREATE_COURSE = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["create_course"]
    BTN_MAIN_MENU = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["main_menu"]
    BTN_CANCEL = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["cancel"]
    BTN_YES_UNLINK = TelegramBotButtonTextVO.BUTTONS[LANG_EN]["yes_unlink"]

    BUTTONS = TelegramBotButtonTextVO.BUTTONS
    ICONS = TelegramBotIconVO
    COMMERCE_FEATURE = TelegramCommerceFeatureVO

    STATE_LINK_METHOD = TelegramBotStateVO.LINK_METHOD
    STATE_LINK_EMAIL = TelegramBotStateVO.LINK_EMAIL
    STATE_LINK_PHONE = TelegramBotStateVO.LINK_PHONE
    STATE_LINK_CODE = TelegramBotStateVO.LINK_CODE
    STATE_VERIFY_EMAIL_CODE = TelegramBotStateVO.VERIFY_EMAIL_CODE
    STATE_VERIFY_PHONE_METHOD = TelegramBotStateVO.VERIFY_PHONE_METHOD
    STATE_VERIFY_PHONE_CODE = TelegramBotStateVO.VERIFY_PHONE_CODE
    STATE_FORGOT_PASSWORD_METHOD = TelegramBotStateVO.FORGOT_PASSWORD_METHOD
    STATE_FORGOT_PASSWORD_EMAIL = TelegramBotStateVO.FORGOT_PASSWORD_EMAIL
    STATE_FORGOT_PASSWORD_PHONE = TelegramBotStateVO.FORGOT_PASSWORD_PHONE
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
    STATE_PAYMENT_RECEIPT_TRACKING = TelegramBotStateVO.PAYMENT_RECEIPT_TRACKING
    STATE_BOT_SETTING_VALUE = getattr(TelegramBotStateVO, "BOT_SETTING_VALUE", "bot_setting_value")
    STATE_BOT_SETTING_EMAIL_CODE = getattr(TelegramBotStateVO, "BOT_SETTING_EMAIL_CODE", "bot_setting_email_code")
    STATE_COURSE_EDIT_VALUE = getattr(TelegramBotStateVO, "COURSE_EDIT_VALUE", "admin_course_edit_value")
    STATE_ADMIN_NOTIFICATION_MESSAGE = getattr(TelegramBotStateVO, "ADMIN_NOTIFICATION_MESSAGE", "admin_notification_message")
    STATE_ADMIN_NOTIFICATION_EMAIL_CODE = getattr(TelegramBotStateVO, "ADMIN_NOTIFICATION_EMAIL_CODE", "admin_notification_email_code")
    STATE_ADMIN_NOTIFICATION_SCHEDULE_AT = getattr(TelegramBotStateVO, "ADMIN_NOTIFICATION_SCHEDULE_AT", "admin_notification_schedule_at")
    STATE_SUPPORT_MESSAGE = getattr(TelegramBotStateVO, "SUPPORT_MESSAGE", "support_message")
    STATE_SUPPORT_REPLY = getattr(TelegramBotStateVO, "SUPPORT_REPLY", "support_reply")
    STATE_DISCOUNT_CREATE = getattr(TelegramBotStateVO, "DISCOUNT_CREATE", "discount_create")
    STATE_DISCOUNT_CODE = getattr(TelegramBotStateVO, "DISCOUNT_CODE", "discount_code")
    STATE_DISCOUNT_VALUE = getattr(TelegramBotStateVO, "DISCOUNT_VALUE", "discount_value")
    STATE_DISCOUNT_USAGE_LIMIT = getattr(TelegramBotStateVO, "DISCOUNT_USAGE_LIMIT", "discount_usage_limit")
    STATE_CHECKOUT_DISCOUNT_CODE = getattr(TelegramBotStateVO, "CHECKOUT_DISCOUNT_CODE", "checkout_discount_code")

    BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES = 5
    ADMIN_NOTIFICATION_CONFIRM_CODE_EXPIRATION_MINUTES = 5
    ADMIN_NOTIFICATION_MAX_LENGTH = getattr(TelegramCommerceFeatureVO, "ADMIN_NOTIFICATION_MAX_LENGTH", 3500)
    ACTION_TIMEOUT_SECONDS = BotAccountLinkVO.CODE_EXPIRATION_MINUTES * 60
    MIN_REVIEW_COMMENT_CHARACTERS = 2

    def __init__(
        self,
        client: TelegramBotClient | None = None,
        *,
        commerce_logic: CommerceBotLogicInterface | None = None,
        channel_sync_logic: ChannelSyncLogicRepository | None = None,
        notification_logic: BotNotificationLogicRepository | None = None,
        support_logic: BotSupportLogicRepository | None = None,
        account_logic: AccountLogicRepository | None = None,
        account_link_logic: BotAccountLinkLogicRepository | None = None,
        messenger_profile_logic: MessengerProfileLogic | None = None,
    ):
        self.client = client or TelegramBotClient()
        self.account_link_logic = account_link_logic or BotAccountLinkLogicRepository()
        self.commerce_logic = commerce_logic or TelegramCommerceBotLogicRepository()
        self.channel_sync_logic = channel_sync_logic or ChannelSyncLogicRepository()
        self.notification_logic = notification_logic or BotNotificationLogicRepository()
        self.support_logic = support_logic or BotSupportLogicRepository()
        self.account_logic = account_logic or AccountLogicRepository()
        self.messenger_profile_logic = messenger_profile_logic or MessengerProfileLogic()

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

        if message.get("contact") and self._handle_waiting_contact(
            profile,
            message=message,
            telegram_user=telegram_user,
        ):
            return

        if not text and self._handle_waiting_attachment(profile, message):
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
            self.clear_all_flow_data(profile.chat_id)
            self.client.send_message(
                chat_id,
                self.menu_text(profile),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if self.is_cancel_button(text):
            self.clear_all_flow_data(profile.chat_id)
            self.client.send_message(
                chat_id,
                self.t(profile, "canceled"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        # Active step-by-step flows must own the next text message.
        # Otherwise a normal review comment such as a short Persian word can be
        # reinterpreted as a menu action or repeatedly prompt the same step.
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
            self.clear_all_flow_data(profile.chat_id)
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

        if data == self.CALLBACK_VERIFY_PHONE:
            self.start_verify_phone_flow(profile)
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

        if data == self.CALLBACK_BOT_SETTINGS:
            self.send_bot_settings_overview(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_ADMIN_NOTIFICATION:
            self.send_admin_notification_menu(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_ADMIN_NOTIFICATION_START:
            self.start_admin_notification_flow(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_ADMIN_NOTIFICATION_CONFIRM:
            self.start_admin_notification_email_confirmation(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_ADMIN_NOTIFICATION_CONFIRM_NOW:
            self.start_admin_notification_email_confirmation(profile, mode="now", message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_ADMIN_NOTIFICATION_SCHEDULE:
            self.start_admin_notification_schedule_flow(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_DISCOUNTS:
            self.send_discount_menu(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_DISCOUNT_CREATE:
            self.start_discount_create_flow(profile, message_id=message.get("message_id"))
            return

        if data.startswith("dsc:type:"):
            self.select_discount_type_from_bot(profile, discount_type=data.rsplit(":", 1)[-1], message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_DISCOUNT_SCOPE_ALL:
            self.select_discount_scope_from_bot(profile, course_id=None, message_id=message.get("message_id"))
            return

        if data.startswith("dsc:scope:c:"):
            self.select_discount_scope_from_bot(profile, course_id=data.split(":", 3)[3], message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_DISCOUNT_USAGE_LIMIT_UNLIMITED:
            self.finalize_discount_create_from_bot(profile, usage_limit=None, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_DISCOUNT_USAGE_LIMIT_CUSTOM:
            self.start_discount_usage_limit_text_flow(profile, message_id=message.get("message_id"))
            return

        if data.startswith("dsc:del:"):
            self.delete_discount_from_bot(profile, discount_id=data.split(":", 2)[2], message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_SUPPORT:
            if self.is_admin_profile(profile):
                self.send_support_queue(profile, message_id=message.get("message_id"))
            else:
                self.send_support_menu(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_SUPPORT_NEW:
            self.start_support_ticket_flow(profile, message_id=message.get("message_id"))
            return

        if data == self.CALLBACK_SUPPORT_QUEUE:
            self.send_support_queue(profile, message_id=message.get("message_id"))
            return

        if data == "sup:mine":
            self.send_user_support_tickets(profile, message_id=message.get("message_id"))
            return

        if data.startswith("sup:ur:"):
            self.start_user_support_reply_flow(profile, ticket_id=data.split(":", 2)[2], message_id=message.get("message_id"))
            return

        if data.startswith("sup:d:"):
            self.send_support_ticket_detail(profile, ticket_id=data.split(":", 2)[2], message_id=message.get("message_id"))
            return

        if data.startswith("sup:r:"):
            self.start_support_reply_flow(profile, ticket_id=data.split(":", 2)[2], message_id=message.get("message_id"))
            return

        if data.startswith("sup:c:"):
            self.close_support_ticket_from_bot(profile, ticket_id=data.split(":", 2)[2], message_id=message.get("message_id"))
            return

        if data.startswith("bs:p:"):
            provider = data.split(":", 2)[2].strip()
            if provider:
                self.send_bot_provider_settings(profile, provider, message_id=message.get("message_id"))
                return

        if data.startswith("bs:k:"):
            parts = data.split(":")
            if len(parts) == 4:
                provider = parts[2].strip()
                key_index = self.safe_int(parts[3], default=-1)
                self.send_bot_setting_edit_options(
                    profile,
                    provider=provider,
                    key_index=key_index,
                    message_id=message.get("message_id"),
                )
                return

        if data.startswith("bs:w:"):
            parts = data.split(":")
            if len(parts) == 5:
                provider = parts[2].strip()
                key_index = self.safe_int(parts[3], default=-1)
                write_target = parts[4].strip()
                self.start_bot_setting_edit_flow(
                    profile,
                    provider=provider,
                    key_index=key_index,
                    write_target=write_target,
                    message_id=message.get("message_id"),
                )
                return

        if data.startswith("bs:v:"):
            parts = data.split(":")
            if len(parts) == 5:
                self.choose_bot_setting_choice_value(
                    profile,
                    provider=parts[2].strip(),
                    key_index=self.safe_int(parts[3], default=-1),
                    choice_index=self.safe_int(parts[4], default=-1),
                    message_id=message.get("message_id"),
                )
                return

        if data.startswith("bs:delc:"):
            parts = data.split(":")
            if len(parts) == 4:
                self.delete_bot_setting_database_value(
                    profile,
                    provider=parts[2].strip(),
                    key_index=self.safe_int(parts[3], default=-1),
                    message_id=message.get("message_id"),
                )
                return

        if data.startswith("bs:del:"):
            parts = data.split(":")
            if len(parts) == 4:
                self.confirm_delete_bot_setting_database_value(
                    profile,
                    provider=parts[2].strip(),
                    key_index=self.safe_int(parts[3], default=-1),
                    message_id=message.get("message_id"),
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
            self.clear_all_flow_data(profile.chat_id)
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
        class _SafeFormatDict(dict):
            def __missing__(self, missing_key):
                return "{" + str(missing_key) + "}"

        texts = TelegramBotMessageTextVO.TEXTS
        template = texts[cls.lang(profile)].get(key, texts[cls.LANG_EN].get(key, key))
        kwargs.setdefault("project_name", get_project_name())
        return template.format_map(_SafeFormatDict(kwargs))

    @classmethod
    def icon(cls, key: str) -> str:
        return cls.ICONS.get(key)

    @classmethod
    def with_icon(cls, key: str, text: str, *, separator: str = " ") -> str:
        return cls.ICONS.prefix(key, text, separator=separator)

    @classmethod
    def warning_text(cls, text: str) -> str:
        return cls.with_icon(TelegramBotIconKeyVO.WARNING, text)

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
            "verify_phone": self.start_verify_phone_flow,
            "forgot_password": self.start_forgot_password_flow,
            "create_user": self.start_create_user_flow,
            "webapp": lambda p: self.handle_webapp(p, TelegramCommand(name="/webapp", args=[], raw_text="/webapp")),
            "language": self.show_language_selection,
            "unlink": self.start_unlink_flow,
            "help": lambda p: self.handle_help(p, TelegramCommand(name="/help", args=[], raw_text="/help")),
            "channels": lambda p: self.handle_channels(p, TelegramCommand(name="/channels", args=[], raw_text="/channels")),
            "bot_settings": self.send_bot_settings_overview,
            "admin_notification": self.send_admin_notification_menu,
            "discounts": self.send_discount_menu,
            "support": (lambda p: self.send_support_queue(p) if self.is_admin_profile(p) else self.send_support_menu(p)),
            "support_queue": self.send_support_queue,
            "courses": lambda p: self.send_course_list(p, page=1),
            "my_courses": self.send_my_courses,
            "my_orders": self.send_my_orders,
            "review_queue": self.send_review_queue,
            "payment_queue": self.send_payment_receipt_queue,
            "admin_courses": lambda p: self.send_admin_course_list(p, page=1),
            "create_course": self.start_create_course_flow,
        }

        aliases = TelegramBotAliasVO.MENU_BUTTON_ALIASES

        for key, handler in action_by_key.items():
            possible = self.all_button_texts(key) | {self.normalize_button_text(item) for item in aliases[key]}
            if normalized in possible:
                self.clear_all_flow_data(profile.chat_id)
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
    def clear_all_flow_data(cls, chat_id: int) -> None:
        cls.clear_action(chat_id)
        cls.clear_create_user_data(chat_id)
        cls.clear_review_flow_data(chat_id)
        cls.clear_course_flow_data(chat_id)
        cls.clear_course_edit_flow_data(chat_id)
        cls.clear_lesson_flow_data(chat_id)
        cls.clear_payment_receipt_flow_data(chat_id)
        cls.clear_bot_setting_edit_data(chat_id)
        cls.clear_bot_setting_email_code(chat_id)
        cls.clear_admin_notification_data(chat_id)
        cls.clear_admin_notification_email_code(chat_id)
        cls.clear_support_flow_data(chat_id)
        cls.clear_discount_flow_data(chat_id)
        cls.clear_checkout_flow_data(chat_id)

    @classmethod
    def bot_setting_edit_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_bot_setting_edit:{chat_id}"

    @classmethod
    def set_bot_setting_edit_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(
            cls.bot_setting_edit_cache_key(chat_id),
            json.dumps(data, ensure_ascii=False),
            timeout=cls.ACTION_TIMEOUT_SECONDS,
        )

    @classmethod
    def get_bot_setting_edit_data(cls, chat_id: int) -> dict[str, Any]:
        raw_data = TelegramBotCacheRepository.get_value(cls.bot_setting_edit_cache_key(chat_id))
        if not raw_data:
            return {}
        if isinstance(raw_data, dict):
            return raw_data
        try:
            value = json.loads(str(raw_data))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def clear_bot_setting_edit_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.bot_setting_edit_cache_key(chat_id))

    @classmethod
    def bot_setting_email_code_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_bot_setting_email_code:{chat_id}"

    @classmethod
    def set_bot_setting_email_code(cls, chat_id: int, code: str) -> bool:
        return VerificationCodeCacheAdapter().store_code_if_absent(
            cache_key=cls.bot_setting_email_code_cache_key(chat_id),
            code=code,
            timeout_seconds=cls.BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES * 60,
        )

    @classmethod
    def verify_bot_setting_email_code(cls, chat_id: int, code: str) -> bool:
        return VerificationCodeCacheAdapter().verify_code(
            cache_key=cls.bot_setting_email_code_cache_key(chat_id),
            code=code,
            timeout_seconds=cls.BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES * 60,
        )

    @classmethod
    def clear_bot_setting_email_code(cls, chat_id: int) -> None:
        VerificationCodeCacheAdapter().delete_code(
            cache_key=cls.bot_setting_email_code_cache_key(chat_id),
        )

    @classmethod
    def admin_notification_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_admin_notification:{chat_id}"

    @classmethod
    def set_admin_notification_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(
            cls.admin_notification_cache_key(chat_id),
            json.dumps(data, ensure_ascii=False),
            timeout=cls.ACTION_TIMEOUT_SECONDS,
        )

    @classmethod
    def get_admin_notification_data(cls, chat_id: int) -> dict[str, Any]:
        raw_data = TelegramBotCacheRepository.get_value(cls.admin_notification_cache_key(chat_id))
        if not raw_data:
            return {}
        if isinstance(raw_data, dict):
            return raw_data
        try:
            value = json.loads(str(raw_data))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def clear_admin_notification_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.admin_notification_cache_key(chat_id))

    @classmethod
    def admin_notification_email_code_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_admin_notification_email_code:{chat_id}"

    @classmethod
    def set_admin_notification_email_code(cls, chat_id: int, code: str) -> bool:
        return VerificationCodeCacheAdapter().store_code_if_absent(
            cache_key=cls.admin_notification_email_code_cache_key(chat_id),
            code=code,
            timeout_seconds=cls.ADMIN_NOTIFICATION_CONFIRM_CODE_EXPIRATION_MINUTES * 60,
        )

    @classmethod
    def verify_admin_notification_email_code(cls, chat_id: int, code: str) -> bool:
        return VerificationCodeCacheAdapter().verify_code(
            cache_key=cls.admin_notification_email_code_cache_key(chat_id),
            code=code,
            timeout_seconds=cls.ADMIN_NOTIFICATION_CONFIRM_CODE_EXPIRATION_MINUTES * 60,
        )

    @classmethod
    def clear_admin_notification_email_code(cls, chat_id: int) -> None:
        VerificationCodeCacheAdapter().delete_code(
            cache_key=cls.admin_notification_email_code_cache_key(chat_id),
        )


    @classmethod
    def support_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_support_flow:{chat_id}"

    @classmethod
    def set_support_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.support_flow_cache_key(chat_id), json.dumps(data, ensure_ascii=False), timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def get_support_flow_data(cls, chat_id: int) -> dict[str, Any]:
        raw_data = TelegramBotCacheRepository.get_value(cls.support_flow_cache_key(chat_id))
        if isinstance(raw_data, dict):
            return raw_data
        if not raw_data:
            return {}
        try:
            value = json.loads(str(raw_data))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def clear_support_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.support_flow_cache_key(chat_id))

    @classmethod
    def discount_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_discount_flow:{chat_id}"

    @classmethod
    def set_discount_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.discount_flow_cache_key(chat_id), json.dumps(data, ensure_ascii=False), timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def update_discount_flow_data(cls, chat_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        data = cls.get_discount_flow_data(chat_id)
        data.update(updates)
        cls.set_discount_flow_data(chat_id, data)
        return data

    @classmethod
    def get_discount_flow_data(cls, chat_id: int) -> dict[str, Any]:
        raw_data = TelegramBotCacheRepository.get_value(cls.discount_flow_cache_key(chat_id))
        if isinstance(raw_data, dict):
            return raw_data
        if not raw_data:
            return {}
        try:
            value = json.loads(str(raw_data))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def clear_discount_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.discount_flow_cache_key(chat_id))

    @classmethod
    def checkout_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_checkout_flow:{chat_id}"

    @classmethod
    def set_checkout_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.checkout_flow_cache_key(chat_id), json.dumps(data, ensure_ascii=False), timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def get_checkout_flow_data(cls, chat_id: int) -> dict[str, Any]:
        raw_data = TelegramBotCacheRepository.get_value(cls.checkout_flow_cache_key(chat_id))
        if isinstance(raw_data, dict):
            return raw_data
        if not raw_data:
            return {}
        try:
            value = json.loads(str(raw_data))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def clear_checkout_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.checkout_flow_cache_key(chat_id))

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

        if action == self.STATE_LINK_METHOD:
            self.handle_link_method_text(profile, text)
            return True

        if action == self.STATE_LINK_EMAIL:
            self.handle_link_email_text(profile, text)
            return True

        if action == self.STATE_LINK_PHONE:
            self.handle_link_phone_text(profile, text)
            return True

        if action == self.STATE_LINK_CODE:
            self.handle_link_code_text(profile, text)
            return True

        if action == self.STATE_VERIFY_EMAIL_CODE:
            self.handle_verify_email_code_text(profile, text)
            return True

        if action == self.STATE_VERIFY_PHONE_METHOD:
            self.handle_verify_phone_method_text(profile, text)
            return True

        if action == self.STATE_VERIFY_PHONE_CODE:
            self.handle_verify_phone_code_text(profile, text)
            return True

        if action == self.STATE_FORGOT_PASSWORD_METHOD:
            self.handle_forgot_password_method_text(profile, text)
            return True

        if action == self.STATE_FORGOT_PASSWORD_EMAIL:
            self.handle_forgot_password_email_text(profile, text)
            return True

        if action == self.STATE_FORGOT_PASSWORD_PHONE:
            self.handle_forgot_password_phone_text(profile, text)
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

        if action == self.STATE_PAYMENT_RECEIPT_TRACKING:
            self.handle_payment_receipt_tracking_text(profile, text)
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

        if action == self.STATE_COURSE_EDIT_VALUE:
            self.handle_course_edit_value_text(profile, text)
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

        if action == self.STATE_BOT_SETTING_VALUE:
            self.handle_bot_setting_value_text(profile, text)
            return True

        if action == self.STATE_BOT_SETTING_EMAIL_CODE:
            self.handle_bot_setting_email_code_text(profile, text)
            return True

        if action == self.STATE_ADMIN_NOTIFICATION_MESSAGE:
            self.handle_admin_notification_message_text(profile, text)
            return True

        if action == self.STATE_ADMIN_NOTIFICATION_EMAIL_CODE:
            self.handle_admin_notification_email_code_text(profile, text)
            return True

        if action == self.STATE_ADMIN_NOTIFICATION_SCHEDULE_AT:
            self.handle_admin_notification_schedule_text(profile, text)
            return True

        if action == self.STATE_SUPPORT_MESSAGE:
            self.handle_support_message_text(profile, text)
            return True

        if action == self.STATE_SUPPORT_REPLY:
            self.handle_support_reply_text(profile, text)
            return True

        if action == self.STATE_DISCOUNT_CODE:
            self.handle_discount_code_text(profile, text)
            return True

        if action == self.STATE_DISCOUNT_VALUE:
            self.handle_discount_value_text(profile, text)
            return True

        if action == self.STATE_DISCOUNT_USAGE_LIMIT:
            self.handle_discount_usage_limit_text(profile, text)
            return True

        if action == self.STATE_DISCOUNT_CREATE:
            self.handle_discount_create_text(profile, text)
            return True

        if action == self.STATE_CHECKOUT_DISCOUNT_CODE:
            self.handle_checkout_discount_code_text(profile, text)
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

    def _handle_waiting_contact(
        self,
        profile: TelegramProfile,
        *,
        message: dict[str, Any],
        telegram_user: dict[str, Any],
    ) -> bool:
        if self.MESSENGER_PROVIDER != "telegram":
            return False
        if self.get_action(profile.chat_id) != self.STATE_VERIFY_PHONE_METHOD:
            return False

        self.handle_verify_phone_contact(
            profile,
            contact=message.get("contact") or {},
            sender_user_id=telegram_user.get("id"),
        )
        return True

    def _handle_waiting_attachment(self, profile: TelegramProfile, message: dict[str, Any]) -> bool:
        action = self.get_action(profile.chat_id)
        if action != self.STATE_PAYMENT_RECEIPT_TRACKING:
            return False
        self.handle_payment_receipt_file_message(profile, message)
        return True

    @staticmethod
    def telegram_receipt_attachment(message: dict[str, Any]) -> dict[str, Any]:
        photos = message.get("photo") or []
        if photos:
            selected = max(photos, key=lambda item: int(item.get("file_size") or 0))
            return {
                "file_id": str(selected.get("file_id") or ""),
                "kind": "photo",
                "filename": "telegram-receipt.jpg",
                "mime_type": "image/jpeg",
                "file_size": int(selected.get("file_size") or 0),
                "caption": str(message.get("caption") or "").strip(),
            }

        document = message.get("document") or {}
        if document:
            return {
                "file_id": str(document.get("file_id") or ""),
                "kind": "document",
                "filename": str(document.get("file_name") or "telegram-receipt"),
                "mime_type": str(document.get("mime_type") or ""),
                "file_size": int(document.get("file_size") or 0),
                "caption": str(message.get("caption") or "").strip(),
            }
        return {}

    def handle_payment_receipt_file_message(self, profile: TelegramProfile, message: dict[str, Any]) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return

        attachment = self.telegram_receipt_attachment(message)
        file_id = attachment.get("file_id")
        if not file_id or not self._valid_receipt_attachment_metadata(attachment):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "payment_receipt_unsupported_file"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        downloader = getattr(self.client, "download_file", None)
        if not callable(downloader):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "payment_receipt_unsupported_file"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        data = self.get_payment_receipt_flow_data(profile.chat_id)
        try:
            downloaded = downloader(file_id, filename=attachment.get("filename", ""))
            receipt_file = ContentFile(downloaded.content, name=downloaded.filename)
            receipt_file.content_type = downloaded.content_type
        except Exception:
            logger.warning("Payment receipt provider download failed.", exc_info=True)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "payment_receipt_unsupported_file"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        caption = str(attachment.get("caption") or "").strip()[:500]
        tracking_code = caption[:120] if self._is_safe_tracking_code(caption) else ""
        note_parts = ["Registered from bot.", f"provider={self.MESSENGER_PROVIDER}"]
        if caption and not tracking_code:
            note_parts.append(f"caption={caption}")

        try:
            receipt = self.commerce_logic.upload_payment_receipt(
                user=user,
                payment_id=data.get("payment_id"),
                tracking_code=tracking_code,
                receipt_file=receipt_file,
                note=" | ".join(note_parts),
            )
        except Exception as error:
            logger.exception("Payment receipt file registration failed")
            self.clear_all_flow_data(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.warning_text(html.escape(self.validation_message(error))),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.clear_all_flow_data(profile.chat_id)
        self.notify_admins_about_payment_receipt(receipt)
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "payment_receipt_saved_with_id",
                message=self.t(profile, "payment_receipt_saved"),
                receipt_id=html.escape(str(receipt.id)),
            ),
            reply_markup=self.main_menu_keyboard(profile),
        )

    @staticmethod
    def _is_safe_tracking_code(value: str) -> bool:
        return bool(value) and len(value) <= 120 and all(
            character.isalnum() or character in "-_/ ." for character in value
        )

    @staticmethod
    def _valid_receipt_attachment_metadata(attachment: dict[str, Any]) -> bool:
        max_bytes = int(getattr(settings, "PAYMENT_RECEIPT_MAX_BYTES", 5 * 1024 * 1024))
        file_size = int(attachment.get("file_size") or 0)
        if file_size and file_size > max_bytes:
            return False
        filename = str(attachment.get("filename") or "").lower()
        mime_type = str(attachment.get("mime_type") or "").lower()
        allowed_extensions = (".jpg", ".jpeg", ".png", ".pdf")
        allowed_mime_types = {"", "image/jpeg", "image/png", "application/pdf"}
        return filename.endswith(allowed_extensions) and mime_type in allowed_mime_types

    def start_link_flow(self, profile: TelegramProfile) -> None:
        if profile.user_id and profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "already_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_LINK_METHOD)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_choose"),
            reply_markup=self.link_method_keyboard(profile),
        )

    def handle_link_method_text(
        self,
        profile: TelegramProfile,
        text: str,
    ) -> None:
        normalized = self.normalize_button_text(text)

        email_choices = self.all_button_texts("link_by_email") | {
            self.normalize_button_text(value)
            for value in TelegramBotAliasVO.MENU_BUTTON_ALIASES["link_by_email"]
        }
        if normalized in email_choices:
            self.set_action(profile.chat_id, self.STATE_LINK_EMAIL)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "link_email_prompt"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        phone_choices = self.all_button_texts("link_by_phone") | {
            self.normalize_button_text(value)
            for value in TelegramBotAliasVO.MENU_BUTTON_ALIASES["link_by_phone"]
        }
        if normalized in phone_choices:
            self.set_action(profile.chat_id, self.STATE_LINK_PHONE)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "link_phone_prompt"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_choose"),
            reply_markup=self.link_method_keyboard(profile),
        )

    def handle_link_email_text(
        self,
        profile: TelegramProfile,
        email: str,
    ) -> None:
        email = email.strip()
        if not self.is_valid_email(email):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_email"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self._send_account_link_code_by_email(profile, email)

    def handle_link_phone_text(
        self,
        profile: TelegramProfile,
        phone_number: str,
    ) -> None:
        phone_number = self.normalize_iranian_phone_number(phone_number)
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except (ValidationError, DRFValidationError, ValueError):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "invalid_link_phone"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self._send_account_link_code_by_phone(profile, phone_number)

    def _send_account_link_code_by_email(
        self,
        profile: TelegramProfile,
        email: str,
    ) -> None:
        self.account_link_logic.send_code_by_email(
            SendBotAccountLinkCodeDTO(
                provider=self.MESSENGER_PROVIDER,
                chat_id=str(profile.chat_id),
                identifier=email,
                language=self.lang(profile),
            )
        )
        self.set_action(profile.chat_id, self.STATE_LINK_CODE)

        # Keep the response account-enumeration safe. It is intentionally the
        # same for a missing account, a newly sent code, and an active code.
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_email_code_sent"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def _send_account_link_code_by_phone(
        self,
        profile: TelegramProfile,
        phone_number: str,
    ) -> None:
        self.account_link_logic.send_code_by_phone(
            SendBotAccountLinkCodeDTO(
                provider=self.MESSENGER_PROVIDER,
                chat_id=str(profile.chat_id),
                identifier=phone_number,
                language=self.lang(profile),
            )
        )
        self.set_action(profile.chat_id, self.STATE_LINK_CODE)

        # Keep the response account-enumeration safe.
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "link_phone_code_sent"),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_link_code_text(
        self,
        profile: TelegramProfile,
        code: str,
    ) -> None:
        code = code.strip()
        if not code.isdigit() or len(code) != BotAccountLinkVO.CODE_LENGTH:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if not self.account_link_logic.confirm_code(
            ConfirmBotAccountLinkCodeDTO(
                provider=self.MESSENGER_PROVIDER,
                chat_id=str(profile.chat_id),
                profile_id=profile.id,
                code=code,
            )
        ):
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
        self.set_action(profile.chat_id, self.STATE_FORGOT_PASSWORD_METHOD)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_choose"),
            reply_markup=self.forgot_password_method_keyboard(profile),
        )

    def handle_forgot_password_method_text(
        self,
        profile: TelegramProfile,
        text: str,
    ) -> None:
        normalized = self.normalize_button_text(text)

        if normalized in self.all_button_texts("forgot_by_email"):
            if profile.user_id and profile.is_verified:
                self._send_forgot_password_email(profile, profile.user.email)
                return

            self.set_action(profile.chat_id, self.STATE_FORGOT_PASSWORD_EMAIL)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "forgot_email_prompt"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if normalized in self.all_button_texts("forgot_by_phone"):
            if profile.user_id and profile.is_verified:
                user = profile.user
                if not user.phone_number or not user.phone_number_verified:
                    self.client.send_message(
                        profile.chat_id,
                        self.t(profile, "forgot_phone_unavailable"),
                        reply_markup=self.forgot_password_method_keyboard(profile),
                    )
                    return
                self._send_forgot_password_sms(profile, user.phone_number)
                return

            self.set_action(profile.chat_id, self.STATE_FORGOT_PASSWORD_PHONE)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "forgot_phone_prompt"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_choose"),
            reply_markup=self.forgot_password_method_keyboard(profile),
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

        self._send_forgot_password_email(profile, email)

    def handle_forgot_password_phone_text(
        self,
        profile: TelegramProfile,
        phone_number: str,
    ) -> None:
        phone_number = self.normalize_iranian_phone_number(phone_number)
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except (ValidationError, DRFValidationError, ValueError):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "forgot_invalid_phone"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self._send_forgot_password_sms(profile, phone_number)

    def _send_forgot_password_email(
        self,
        profile: TelegramProfile,
        email: str,
    ) -> None:
        self.account_logic.send_forget_password_code_by_email(
            SendPasswordRecoveryCodeDTO(email=email),
        )
        self.clear_action(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_email_sent"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def _send_forgot_password_sms(
        self,
        profile: TelegramProfile,
        phone_number: str,
    ) -> None:
        self.account_logic.send_forget_password_code_by_sms(
            SendSmsPasswordRecoveryCodeDTO(phone_number=phone_number),
        )
        self.clear_action(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "forgot_phone_sent"),
            reply_markup=self.main_menu_keyboard(profile),
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
            self.account_logic.send_verification_forget_password_code(user)
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

        code_issued = self.account_logic.send_verification_email_code(user)
        self.set_action(profile.chat_id, self.STATE_VERIFY_EMAIL_CODE)
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "verify_sent" if code_issued else "verify_code_active",
            ),
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

        if not self.account_logic.check_email_validation_code(profile.user, code):
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

    def start_verify_phone_flow(self, profile: TelegramProfile) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        user = profile.user
        if not user.is_active:
            self._send_phone_verification_error(
                profile,
                AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT,
            )
            return
        if user.phone_number_verified:
            self._send_phone_verification_error(
                profile,
                AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED,
            )
            return

        if self.MESSENGER_PROVIDER == "telegram":
            self.set_action(profile.chat_id, self.STATE_VERIFY_PHONE_METHOD)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "phone_verify_choose"),
                reply_markup=self.phone_verification_method_keyboard(profile),
            )
            return

        self._send_phone_verification_sms(profile)

    def handle_verify_phone_method_text(
        self,
        profile: TelegramProfile,
        text: str,
    ) -> None:
        normalized = self.normalize_button_text(text)
        if normalized in self.all_button_texts("verify_phone_sms"):
            self._send_phone_verification_sms(profile)
            return

        if normalized in self.all_button_texts("verify_phone_telegram"):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "phone_verify_share_prompt"),
                reply_markup=self.phone_verification_method_keyboard(profile),
            )
            return

        self.client.send_message(
            profile.chat_id,
            self.t(profile, "phone_verify_choose"),
            reply_markup=self.phone_verification_method_keyboard(profile),
        )

    def _send_phone_verification_sms(self, profile: TelegramProfile) -> None:
        result = self.account_logic.send_phone_verification_code(
            dto=SendPhoneVerificationCodeDTO(user_id=str(profile.user_id)),
        )
        if not result.is_success:
            self._send_phone_verification_error(profile, result.error_code)
            return

        self.set_action(profile.chat_id, self.STATE_VERIFY_PHONE_CODE)
        message_key = (
            "phone_verify_sent"
            if result.code_issued
            else "phone_verify_code_active"
        )
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                message_key,
                phone=html.escape(profile.user.phone_number or "-"),
            ),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_verify_phone_contact(
        self,
        profile: TelegramProfile,
        *,
        contact: dict[str, Any],
        sender_user_id: int | str | None,
    ) -> None:
        if not profile.user_id or not profile.is_verified:
            self.clear_action(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        contact_user_id = contact.get("user_id")
        if (
            sender_user_id is None
            or contact_user_id is None
            or str(contact_user_id) != str(sender_user_id)
        ):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "phone_verify_contact_not_own"),
                reply_markup=self.phone_verification_method_keyboard(profile),
            )
            return

        phone_number = self.normalize_iranian_phone_number(
            str(contact.get("phone_number") or ""),
        )
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except (ValidationError, DRFValidationError, ValueError):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "phone_verify_contact_invalid"),
                reply_markup=self.phone_verification_method_keyboard(profile),
            )
            return

        result = self.account_logic.verify_phone_number_by_telegram(
            dto=VerifyPhoneNumberByTelegramDTO(
                user_id=str(profile.user_id),
                phone_number=phone_number,
            ),
        )
        if not result.is_success:
            self._send_phone_verification_error(profile, result.error_code)
            return

        self.clear_action(profile.chat_id)
        profile.user.phone_number = phone_number
        profile.user.phone_number_verified = True
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "phone_verify_success"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_verify_phone_code_text(self, profile: TelegramProfile, code: str) -> None:
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

        result = self.account_logic.verify_phone_number(
            dto=VerifyPhoneNumberDTO(
                user_id=str(profile.user_id),
                code=code,
            ),
        )
        if not result.is_success:
            self._send_phone_verification_error(profile, result.error_code)
            return

        self.clear_action(profile.chat_id)
        profile.user.phone_number_verified = True
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "phone_verify_success"),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def _send_phone_verification_error(
        self,
        profile: TelegramProfile,
        error_code: AccountPhoneVerificationErrorCodeVO | None,
    ) -> None:
        message_key = {
            AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED: "phone_verify_already",
            AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED: "phone_verify_required",
            AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT: "phone_verify_inactive",
            AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND: "not_linked",
            AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE: "phone_verify_invalid",
            AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE: "phone_verify_phone_in_use",
        }.get(error_code, "phone_verify_invalid")

        if (
            error_code == AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED
            and profile.user_id
        ):
            profile.user.phone_number_verified = True

        keep_flow_open = (
            error_code == AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE
        )
        if not keep_flow_open:
            self.clear_action(profile.chat_id)

        self.client.send_message(
            profile.chat_id,
            self.t(profile, message_key),
            reply_markup=(
                self.cancel_keyboard(profile)
                if keep_flow_open
                else self.main_menu_keyboard(profile)
            ),
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

    def handle_verify_phone(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if command.args and command.args[0].isdigit() and len(command.args[0]) == 6:
            self.handle_verify_phone_code_text(profile, command.args[0])
            return
        self.start_verify_phone_flow(profile)

    def handle_create_user(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.start_create_user_flow(profile)

    def handle_link(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if not command.args:
            self.start_link_flow(profile)
            return

        identifier = command.args[0].strip()
        if self.is_valid_email(identifier):
            self._send_account_link_code_by_email(profile, identifier)
            return

        phone_number = self.normalize_iranian_phone_number(identifier)
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except (ValidationError, DRFValidationError, ValueError):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "link_usage"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self._send_account_link_code_by_phone(profile, phone_number)

    def handle_confirm(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if (
            not command.args
            or not command.args[0].isdigit()
            or len(command.args[0]) != BotAccountLinkVO.CODE_LENGTH
        ):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.handle_link_code_text(profile, command.args[0])

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
        if not profile.user_id:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "not_linked"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        result = self.messenger_profile_logic.disconnect(
            DisconnectMessengerProfileDTO(
                profile_id=profile.id,
                user_id=profile.user_id,
            )
        )
        message_key = "unlinked" if result.is_success else "not_linked"
        self.client.send_message(
            profile.chat_id,
            self.t(profile, message_key),
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
        text = self.t(
            profile,
            "account_text",
            username=html.escape(user.username or "-"),
            first_name=html.escape(user.first_name or "-"),
            last_name=html.escape(user.last_name or "-"),
            email=html.escape(user.email or "-"),
            phone=html.escape(user.phone_number or "-"),
            email_verified=(
                self.t(profile, "yes")
                if user.email_verified
                else self.t(profile, "no")
            ),
            phone_verified=(
                self.t(profile, "yes")
                if user.phone_number_verified
                else self.t(profile, "no")
            ),
        )
        self.client.send_message(
            profile.chat_id,
            text,
            reply_markup=self.main_menu_keyboard(profile),
        )

    def handle_forgot_password(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        if not command.args:
            self.start_forgot_password_flow(profile)
            return

        identifier = command.args[0].strip()
        if self.is_valid_email(identifier):
            self._send_forgot_password_email(profile, identifier)
            return

        phone_number = self.normalize_iranian_phone_number(identifier)
        try:
            phone_number = validate_iranian_phone_number(phone_number)
        except (ValidationError, DRFValidationError, ValueError):
            self.start_forgot_password_flow(profile)
            return

        self._send_forgot_password_sms(profile, phone_number)

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

    def handle_admin_notification(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_admin_notification_menu(profile)

    def send_admin_notification_menu(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        recipient_count = self.notification_logic.linked_recipient_count(provider=self.MESSENGER_PROVIDER)
        text = "\n".join([
            self.t(profile, "admin_notification_title"),
            "",
            self.t(
                profile,
                "admin_notification_hint",
                count=recipient_count,
                max_length=self.ADMIN_NOTIFICATION_MAX_LENGTH,
            ),
        ])
        keyboard = self.inline_keyboard([
            [self.inline_button(self.t(profile, "admin_notification_start_button"), self.CALLBACK_ADMIN_NOTIFICATION_START)],
            [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
        ])
        self.send_chain_message(profile, text, reply_markup=keyboard, message_id=message_id)

    def start_admin_notification_flow(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        self.clear_all_flow_data(profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_ADMIN_NOTIFICATION_MESSAGE)
        self.send_chain_message(
            profile,
            self.t(profile, "admin_notification_prompt"),
            reply_markup=self.cancel_keyboard(profile),
            message_id=message_id,
        )

    def handle_admin_notification_message_text(self, profile: TelegramProfile, text: str) -> None:
        if not self.is_admin_profile(profile):
            self.clear_admin_notification_data(profile.chat_id)
            self.clear_admin_notification_email_code(profile.chat_id)
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        notification_text = (text or "").strip()
        if not notification_text:
            self.client.send_message(profile.chat_id, self.t(profile, "admin_notification_empty"), reply_markup=self.cancel_keyboard(profile))
            return

        if len(notification_text) > self.ADMIN_NOTIFICATION_MAX_LENGTH:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_too_long", max_length=self.ADMIN_NOTIFICATION_MAX_LENGTH),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        recipient_count = self.notification_logic.linked_recipient_count(provider=self.MESSENGER_PROVIDER)
        self.set_admin_notification_data(profile.chat_id, {"message": notification_text})
        self.clear_action(profile.chat_id)

        keyboard = self.inline_keyboard([
            [self.inline_button(self.t(profile, "admin_notification_send_now_button"), self.CALLBACK_ADMIN_NOTIFICATION_CONFIRM_NOW)],
            [self.inline_button(self.t(profile, "admin_notification_schedule_button"), self.CALLBACK_ADMIN_NOTIFICATION_SCHEDULE)],
            [self.inline_button(self.t(profile, "admin_notification_edit_button"), self.CALLBACK_ADMIN_NOTIFICATION_START)],
            [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
        ])
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "admin_notification_preview",
                count=recipient_count,
                message=html.escape(notification_text),
            ),
            reply_markup=keyboard,
        )

    def start_admin_notification_email_confirmation(self, profile: TelegramProfile, mode: str = "now", message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        pending_data = self.get_admin_notification_data(profile.chat_id)
        notification_text = str(pending_data.get("message") or "").strip()
        if not notification_text:
            self.clear_admin_notification_data(profile.chat_id)
            self.clear_admin_notification_email_code(profile.chat_id)
            self.clear_action(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_pending_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        pending_data["mode"] = mode
        self.set_admin_notification_data(profile.chat_id, pending_data)

        user = profile.user if profile.user_id else None
        if not user or not getattr(user, "email", ""):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_notification_email_missing"), reply_markup=self.main_menu_keyboard(profile))
            return

        try:
            self.send_admin_notification_confirmation_email(profile)
        except Exception as exc:
            logger.exception("Failed to send admin notification confirmation email.")
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_email_send_failed", error=html.escape(self.validation_message(exc))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_ADMIN_NOTIFICATION_EMAIL_CODE)
        self.send_chain_message(
            profile,
            self.t(
                profile,
                "admin_notification_email_code_sent",
                email=html.escape(self.mask_email(user.email)),
                minutes=self.ADMIN_NOTIFICATION_CONFIRM_CODE_EXPIRATION_MINUTES,
            ),
            reply_markup=self.cancel_keyboard(profile),
            message_id=message_id,
        )

    def handle_admin_notification_email_code_text(self, profile: TelegramProfile, code: str) -> None:
        if not self.is_admin_profile(profile):
            self.clear_admin_notification_data(profile.chat_id)
            self.clear_admin_notification_email_code(profile.chat_id)
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        pending_data = self.get_admin_notification_data(profile.chat_id)
        notification_text = str(pending_data.get("message") or "").strip()
        if not notification_text:
            self.clear_admin_notification_data(profile.chat_id)
            self.clear_admin_notification_email_code(profile.chat_id)
            self.clear_action(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_pending_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if not self.verify_admin_notification_email_code(profile.chat_id, code):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_email_code_invalid"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        delivery_text = self.t(
            profile,
            "admin_notification_delivery_text",
            message=html.escape(notification_text),
        )
        mode = str(pending_data.get("mode") or "now")
        if mode == "schedule":
            scheduled_at_value = pending_data.get("scheduled_at")
            scheduled_at = self.parse_schedule_datetime(str(scheduled_at_value or ""))
            if not scheduled_at:
                self.client.send_message(profile.chat_id, self.t(profile, "admin_notification_schedule_invalid"), reply_markup=self.cancel_keyboard(profile))
                return
            scheduled = self.notification_logic.schedule_notification(
                provider=self.MESSENGER_PROVIDER,
                message=delivery_text,
                scheduled_at=scheduled_at,
                created_by=profile.user if profile.user_id else None,
            )
            self.clear_admin_notification_data(profile.chat_id)
            self.clear_admin_notification_email_code(profile.chat_id)
            self.clear_action(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "admin_notification_scheduled_result", id=scheduled.id, scheduled_at=scheduled.scheduled_at.strftime("%Y-%m-%d %H:%M"), count=scheduled.recipient_count),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        result = self.notification_logic.broadcast_to_linked_recipients(
            client=self.client,
            provider=self.MESSENGER_PROVIDER,
            message=delivery_text,
        )

        self.clear_admin_notification_data(profile.chat_id)
        self.clear_admin_notification_email_code(profile.chat_id)
        self.clear_action(profile.chat_id)
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "admin_notification_sent_result",
                total=result.total_count,
                success=result.success_count,
                failed=result.failed_count,
            ),
            reply_markup=self.main_menu_keyboard(profile),
        )


    def start_admin_notification_schedule_flow(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        pending_data = self.get_admin_notification_data(profile.chat_id)
        if not str(pending_data.get("message") or "").strip():
            self.client.send_message(profile.chat_id, self.t(profile, "admin_notification_pending_missing"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.set_action(profile.chat_id, self.STATE_ADMIN_NOTIFICATION_SCHEDULE_AT)
        self.send_chain_message(profile, self.t(profile, "admin_notification_schedule_prompt"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_admin_notification_schedule_text(self, profile: TelegramProfile, text: str) -> None:
        scheduled_at = self.parse_schedule_datetime(text)
        if not scheduled_at:
            self.client.send_message(profile.chat_id, self.t(profile, "admin_notification_schedule_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        pending_data = self.get_admin_notification_data(profile.chat_id)
        pending_data["scheduled_at"] = scheduled_at.strftime("%Y-%m-%d %H:%M")
        pending_data["mode"] = "schedule"
        self.set_admin_notification_data(profile.chat_id, pending_data)
        self.start_admin_notification_email_confirmation(profile, mode="schedule")

    @staticmethod
    def parse_schedule_datetime(value: str):
        try:
            dt = datetime.strptime((value or "").strip(), "%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            return None
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        if dt <= timezone.now():
            return None
        return dt

    def send_admin_notification_confirmation_email(self, profile: TelegramProfile) -> None:
        user = profile.user
        code = VerificationCodeCacheAdapter.generate_code()
        if not self.set_admin_notification_email_code(profile.chat_id, code):
            return False
        subject = self.t(profile, "admin_notification_email_subject")
        send_html_email_async(
            subject=subject,
            template_name="emails/fa_verification_code.html" if self.lang(profile) == self.LANG_FA else "emails/verification_code.html",
            context={
                "subject": subject,
                "app_name": get_project_name(),
                "user_name": user.first_name or user.username or TelegramBotMessageTextVO.DEFAULT_USER_NAME[self.lang(profile)],
                "code": code,
                "expiration_minutes": self.ADMIN_NOTIFICATION_CONFIRM_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )
        return True


    def send_discount_menu(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            discounts, has_next, total_count = self.commerce_logic.list_discount_codes(page=1, page_size=10)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return

        lines = [
            self.t(profile, "discounts_title"),
            "",
            self.t(profile, "discounts_hint"),
            self.t(profile, "discounts_list_count", count=total_count),
            "",
        ]
        if not discounts:
            lines.append(self.t(profile, "discounts_empty"))

        keyboard_rows = [[self.inline_button(self.t(profile, "discounts_create_button"), self.CALLBACK_DISCOUNT_CREATE)]]
        for discount in discounts:
            lines.append(self.format_discount_for_admin(profile, discount))
            keyboard_rows.append([
                self.inline_button(f"{discount.code} - {self.t(profile, 'discounts_delete_button')}", f"dsc:del:{discount.id}")
            ])
        keyboard_rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(keyboard_rows), message_id=message_id)

    def format_discount_for_admin(self, profile: TelegramProfile, discount) -> str:
        value = f"{discount.value:g}" if hasattr(discount.value, "__format__") else str(discount.value)
        usage_limit = discount.usage_limit if discount.usage_limit is not None else "∞"
        scope = self.t(profile, "discounts_scope_all_button") if getattr(discount, "applies_to_all_courses", False) else self.discount_course_scope_label(discount)
        return self.t(
            profile,
            "discounts_item_text",
            code=html.escape(str(discount.code)),
            discount_type=html.escape(str(discount.discount_type)),
            value=html.escape(str(value)),
            scope=html.escape(str(scope)),
            used=getattr(discount, "used_count", 0),
            limit=usage_limit,
        )

    @staticmethod
    def discount_course_scope_label(discount) -> str:
        try:
            courses = list(discount.courses.all()[:2])
        except Exception:
            courses = []
        if not courses:
            return "selected course"
        return ", ".join(str(course.title) for course in courses)

    def start_discount_create_flow(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_all_flow_data(profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_DISCOUNT_CODE)
        self.set_discount_flow_data(profile.chat_id, {})
        self.send_chain_message(profile, self.t(profile, "discounts_create_prompt"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_discount_code_text(self, profile: TelegramProfile, text: str) -> None:
        if not self.is_admin_profile(profile):
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        code = (text or "").strip().upper()
        is_valid = 2 <= len(code) <= 60 and all(char.isalnum() or char in {"-", "_"} for char in code)
        if not is_valid:
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_code_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        self.update_discount_flow_data(profile.chat_id, {"code": code})
        self.clear_action(profile.chat_id)
        rows = [
            [self.inline_button(self.t(profile, "discounts_type_percent_button"), self.CALLBACK_DISCOUNT_TYPE_PERCENT)],
            [self.inline_button(self.t(profile, "discounts_type_amount_button"), self.CALLBACK_DISCOUNT_TYPE_AMOUNT)],
            [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
        ]
        self.client.send_message(profile.chat_id, self.t(profile, "discounts_type_prompt", code=html.escape(code)), reply_markup=self.inline_keyboard(rows))

    def select_discount_type_from_bot(self, profile: TelegramProfile, *, discount_type: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        discount_type = (discount_type or "").strip().lower()
        if discount_type not in {"percent", "amount"}:
            self.send_chain_message(profile, self.t(profile, "discounts_invalid_format"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)
            return
        data = self.update_discount_flow_data(profile.chat_id, {"discount_type": discount_type})
        code = data.get("code")
        if not code:
            self.send_chain_message(profile, self.t(profile, "discounts_session_expired"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        self.set_action(profile.chat_id, self.STATE_DISCOUNT_VALUE)
        text_key = "discounts_value_prompt_percent" if discount_type == "percent" else "discounts_value_prompt_amount"
        self.send_chain_message(profile, self.t(profile, text_key, code=html.escape(code)), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_discount_value_text(self, profile: TelegramProfile, text: str) -> None:
        if not self.is_admin_profile(profile):
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        data = self.get_discount_flow_data(profile.chat_id)
        code = data.get("code")
        discount_type = data.get("discount_type")
        if not code or not discount_type:
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_session_expired"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            value = Decimal((text or "").strip())
        except Exception:
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_value_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        if value <= 0 or (discount_type == "percent" and value > 100):
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_value_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        self.update_discount_flow_data(profile.chat_id, {"value": str(value)})
        self.clear_action(profile.chat_id)
        self.send_discount_scope_selector(profile)

    def send_discount_scope_selector(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        rows = [[self.inline_button(self.t(profile, "discounts_scope_all_button"), self.CALLBACK_DISCOUNT_SCOPE_ALL)]]
        try:
            courses, has_next = self.commerce_logic.list_admin_courses(page=1, page_size=8)
        except Exception:
            courses = []
        for course in courses:
            title = str(getattr(course, "title", ""))[:45] or str(course.id)
            rows.append([self.inline_button(self.t(profile, "discounts_scope_course_button", title=title), f"dsc:scope:c:{course.id}")])
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(profile, self.t(profile, "discounts_scope_prompt"), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def select_discount_scope_from_bot(self, profile: TelegramProfile, *, course_id: str | None, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        data = self.get_discount_flow_data(profile.chat_id)
        if not data.get("code") or not data.get("discount_type") or not data.get("value"):
            self.send_chain_message(profile, self.t(profile, "discounts_session_expired"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        self.update_discount_flow_data(profile.chat_id, {"course_id": str(course_id) if course_id else None})
        rows = [
            [self.inline_button(self.t(profile, "discounts_usage_unlimited_button"), self.CALLBACK_DISCOUNT_USAGE_LIMIT_UNLIMITED)],
            [self.inline_button(self.t(profile, "discounts_usage_custom_button"), self.CALLBACK_DISCOUNT_USAGE_LIMIT_CUSTOM)],
            [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
        ]
        self.send_chain_message(profile, self.t(profile, "discounts_usage_limit_prompt", code=html.escape(str(data.get("code")))), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def start_discount_usage_limit_text_flow(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        if not self.get_discount_flow_data(profile.chat_id).get("code"):
            self.send_chain_message(profile, self.t(profile, "discounts_session_expired"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        self.set_action(profile.chat_id, self.STATE_DISCOUNT_USAGE_LIMIT)
        self.send_chain_message(profile, self.t(profile, "discounts_usage_custom_prompt"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_discount_usage_limit_text(self, profile: TelegramProfile, text: str) -> None:
        try:
            usage_limit = int((text or "").strip())
        except Exception:
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_usage_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        if usage_limit <= 0:
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_usage_invalid"), reply_markup=self.cancel_keyboard(profile))
            return
        self.finalize_discount_create_from_bot(profile, usage_limit=usage_limit)

    def finalize_discount_create_from_bot(self, profile: TelegramProfile, *, usage_limit: int | None, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        data = self.get_discount_flow_data(profile.chat_id)
        code = data.get("code")
        discount_type = data.get("discount_type")
        value = data.get("value")
        if not code or not discount_type or value is None:
            self.clear_action(profile.chat_id)
            self.clear_discount_flow_data(profile.chat_id)
            self.send_chain_message(profile, self.t(profile, "discounts_session_expired"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        try:
            discount = self.commerce_logic.create_discount_code(
                profile.user,
                code=code,
                discount_type=discount_type,
                value=Decimal(str(value)),
                course_id=data.get("course_id"),
                usage_limit=usage_limit,
            )
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_action(profile.chat_id)
        self.clear_discount_flow_data(profile.chat_id)
        scope = self.t(profile, "discounts_scope_all_button") if getattr(discount, "applies_to_all_courses", False) else self.discount_course_scope_label(discount)
        self.send_chain_message(
            profile,
            self.t(
                profile,
                "discounts_created",
                code=html.escape(discount.code),
                discount_type=html.escape(discount.discount_type),
                value=discount.value,
                scope=html.escape(str(scope)),
                usage_limit=discount.usage_limit if discount.usage_limit is not None else "∞",
            ),
            reply_markup=self.main_menu_keyboard(profile),
            message_id=message_id,
        )

    def handle_discount_create_text(self, profile: TelegramProfile, text: str) -> None:
        """Legacy one-line parser kept for old cached sessions during deployment."""
        if not self.is_admin_profile(profile):
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        parts = (text or "").strip().split()
        if len(parts) < 4:
            self.client.send_message(profile.chat_id, self.t(profile, "discounts_invalid_format"), reply_markup=self.cancel_keyboard(profile))
            return
        code, discount_type, raw_value, raw_course = parts[:4]
        raw_limit = parts[4] if len(parts) > 4 else ""
        try:
            value = Decimal(raw_value)
            usage_limit = int(raw_limit) if raw_limit else None
            course_id = None if raw_course.lower() == "all" else raw_course
            discount = self.commerce_logic.create_discount_code(
                profile.user,
                code=code,
                discount_type=discount_type,
                value=value,
                course_id=course_id,
                usage_limit=usage_limit,
            )
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.cancel_keyboard(profile))
            return
        self.clear_action(profile.chat_id)
        self.clear_discount_flow_data(profile.chat_id)
        scope = self.t(profile, "discounts_scope_all_button") if getattr(discount, "applies_to_all_courses", False) else self.discount_course_scope_label(discount)
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "discounts_created",
                code=html.escape(discount.code),
                discount_type=html.escape(discount.discount_type),
                value=discount.value,
                scope=html.escape(str(scope)),
                usage_limit=discount.usage_limit if discount.usage_limit is not None else "∞",
            ),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def delete_discount_from_bot(self, profile: TelegramProfile, discount_id: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            discount = self.commerce_logic.delete_discount_code(profile.user, discount_id=discount_id)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return
        self.send_chain_message(profile, self.t(profile, "discounts_deleted", code=html.escape(discount.code)), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)

    def start_checkout_discount_flow(self, profile: TelegramProfile, course_id, message_id: int | None = None) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        self.clear_all_flow_data(profile.chat_id)
        self.set_checkout_flow_data(profile.chat_id, {"course_id": str(course_id)})
        self.set_action(profile.chat_id, self.STATE_CHECKOUT_DISCOUNT_CODE)
        self.send_chain_message(profile, self.t(profile, "checkout_discount_prompt"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_checkout_discount_code_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_checkout_flow_data(profile.chat_id)
        course_id = data.get("course_id")
        if not course_id:
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "courses_empty"), reply_markup=self.main_menu_keyboard(profile))
            return
        discount_code = "" if (text or "").strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else (text or "").strip()
        try:
            self.checkout_course_from_bot(profile, course_id, discount_code=discount_code)
        except Exception as exc:
            if discount_code:
                self.client.send_message(profile.chat_id, self.t(profile, "checkout_discount_invalid", error=html.escape(self.validation_message(exc))), reply_markup=self.cancel_keyboard(profile))
                return
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_checkout_flow_data(profile.chat_id)
        self.clear_action(profile.chat_id)

    def send_support_menu(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(profile.chat_id, self.t(profile, "not_linked"), reply_markup=self.main_menu_keyboard(profile))
            return
        if self.is_admin_profile(profile):
            self.send_support_queue(profile, message_id=message_id)
            return
        rows = [
            [self.inline_button(self.t(profile, "support_new_button"), self.CALLBACK_SUPPORT_NEW)],
            [self.inline_button(self.t(profile, "support_my_tickets_button"), "sup:mine")],
        ]
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        text = "\n".join([self.t(profile, "support_title"), "", self.t(profile, "support_hint")])
        self.send_chain_message(profile, text, reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def start_support_ticket_flow(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(profile.chat_id, self.t(profile, "not_linked"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.clear_all_flow_data(profile.chat_id)
        self.set_action(profile.chat_id, self.STATE_SUPPORT_MESSAGE)
        self.send_chain_message(profile, self.t(profile, "support_prompt"), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_support_message_text(self, profile: TelegramProfile, text: str) -> None:
        message_text = (text or "").strip()
        if not message_text:
            self.client.send_message(profile.chat_id, self.t(profile, "support_empty"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_support_flow_data(profile.chat_id)
        ticket_id = data.get("ticket_id")
        try:
            if ticket_id:
                ticket, msg = self.support_logic.add_user_message(provider=self.MESSENGER_PROVIDER, ticket_id=ticket_id, profile=profile, message=message_text)
            else:
                ticket = self.support_logic.create_ticket(provider=self.MESSENGER_PROVIDER, profile=profile, message=message_text)
                self.notify_admins_about_support_ticket(profile, ticket, message_text)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.cancel_keyboard(profile))
            return
        self.clear_support_flow_data(profile.chat_id)
        self.clear_action(profile.chat_id)
        self.client.send_message(profile.chat_id, self.t(profile, "support_created", ticket_id=ticket.id), reply_markup=self.main_menu_keyboard(profile))


    def send_user_support_tickets(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not profile.user_id or not profile.is_verified:
            self.client.send_message(profile.chat_id, self.t(profile, "not_linked"), reply_markup=self.main_menu_keyboard(profile))
            return
        tickets = self.support_logic.list_user_tickets(provider=self.MESSENGER_PROVIDER, profile=profile, limit=10)
        if not tickets:
            self.send_chain_message(profile, self.t(profile, "support_admin_queue_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        rows = []
        lines = [self.t(profile, "support_my_tickets_button"), ""]
        for ticket in tickets:
            lines.append(f"#{ticket.id} | <code>{html.escape(ticket.status)}</code> | {html.escape(ticket.subject[:120])}")
            rows.append([self.inline_button(f"#{ticket.id}", f"sup:d:{ticket.id}")])
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def start_user_support_reply_flow(self, profile: TelegramProfile, ticket_id: str, message_id: int | None = None) -> None:
        self.set_support_flow_data(profile.chat_id, {"ticket_id": str(ticket_id)})
        self.set_action(profile.chat_id, self.STATE_SUPPORT_MESSAGE)
        self.send_chain_message(profile, self.t(profile, "support_user_reply_prompt", ticket_id=ticket_id), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def send_support_queue(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        tickets = self.support_logic.list_admin_tickets(provider=self.MESSENGER_PROVIDER, status=BotSupportTicket.STATUS_OPEN, limit=10)
        if not tickets:
            self.send_chain_message(profile, self.t(profile, "support_admin_queue_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        rows = []
        lines = [self.t(profile, "support_queue_button"), ""]
        for ticket in tickets:
            user_label = ticket.user.email if ticket.user_id and ticket.user.email else ticket.profile.username or ticket.profile.chat_id
            last_message = ticket.messages.last().message if ticket.messages.exists() else ticket.subject
            lines.append(f"#{ticket.id} | {html.escape(user_label)} | {html.escape(ticket.status)}\n{html.escape(last_message[:120])}")
            rows.append([self.inline_button(f"#{ticket.id}", f"sup:d:{ticket.id}")])
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def send_support_ticket_detail(self, profile: TelegramProfile, ticket_id: str, message_id: int | None = None) -> None:
        try:
            ticket = self.support_logic.get_ticket(provider=self.MESSENGER_PROVIDER, ticket_id=ticket_id)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return
        if not self.is_admin_profile(profile) and ticket.profile_id != profile.id:
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        lines = [f"Ticket <code>{ticket.id}</code> | <code>{html.escape(ticket.status)}</code>", ""]
        for msg in ticket.messages.all()[:10]:
            sender = "Admin" if msg.sender_type == "admin" else "User"
            lines.append(f"<b>{sender}</b>: {html.escape(msg.message)}")
        rows = []
        if self.is_admin_profile(profile) and ticket.status != BotSupportTicket.STATUS_CLOSED:
            rows.append([self.inline_button(self.t(profile, "support_admin_reply_button"), f"sup:r:{ticket.id}")])
            rows.append([self.inline_button(self.t(profile, "support_admin_close_button"), f"sup:c:{ticket.id}")])
        elif ticket.profile_id == profile.id and ticket.status != BotSupportTicket.STATUS_CLOSED:
            rows.append([self.inline_button(self.t(profile, "support_admin_reply_button"), f"sup:ur:{ticket.id}")])
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def start_support_reply_flow(self, profile: TelegramProfile, ticket_id: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.set_support_flow_data(profile.chat_id, {"ticket_id": str(ticket_id)})
        self.set_action(profile.chat_id, self.STATE_SUPPORT_REPLY)
        self.send_chain_message(profile, self.t(profile, "support_admin_reply_prompt", ticket_id=ticket_id), reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_support_reply_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_support_flow_data(profile.chat_id)
        ticket_id = data.get("ticket_id")
        if not ticket_id:
            self.clear_action(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "support_admin_queue_empty"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            ticket, msg = self.support_logic.reply(ticket_id=ticket_id, admin_user=profile.user, message=text)
            self.client.send_message(
                ticket.profile.chat_id,
                self.t(ticket.profile, "support_user_notification", ticket_id=ticket.id, message=html.escape(text)),
            )
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.cancel_keyboard(profile))
            return
        self.clear_support_flow_data(profile.chat_id)
        self.clear_action(profile.chat_id)
        self.client.send_message(profile.chat_id, self.t(profile, "support_admin_replied"), reply_markup=self.main_menu_keyboard(profile))

    def close_support_ticket_from_bot(self, profile: TelegramProfile, ticket_id: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            self.support_logic.close(ticket_id=ticket_id, admin_user=profile.user)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return
        self.send_chain_message(profile, self.t(profile, "support_closed"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)

    def notify_admins_about_support_ticket(self, profile: TelegramProfile, ticket, message_text: str) -> None:
        try:
            admins = TelegramProfile.objects.filter(messenger_provider=self.MESSENGER_PROVIDER, is_active=True, is_verified=True, user__isnull=False).filter(Q(user__is_staff=True) | Q(user__is_superuser=True)).exclude(chat_id=profile.chat_id)
            user_label = profile.user.email if profile.user_id and profile.user.email else profile.username or profile.chat_id
            for admin_profile in admins[:20]:
                self.client.send_message(
                    admin_profile.chat_id,
                    self.t(admin_profile, "support_admin_new_ticket_notice", ticket_id=ticket.id, user=html.escape(str(user_label)), message=html.escape(message_text)),
                    reply_markup=self.inline_keyboard([[self.inline_button(self.t(admin_profile, "support_admin_reply_button"), f"sup:r:{ticket.id}")]]),
                )
        except Exception:
            logger.debug("Failed to notify admins about support ticket", exc_info=True)

    def send_bot_settings_overview(self, profile: TelegramProfile, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        groups = BotSettingLogicRepository().list_all()
        lines = [self.t(profile, "bot_settings_title"), "", self.t(profile, "bot_settings_hint")]
        keyboard: list[list[dict[str, Any]]] = []
        for group in groups:
            provider = group.get("provider", "")
            settings_count = len(group.get("settings", []))
            configured_count = sum(1 for item in group.get("settings", []) if item.get("is_configured"))
            lines.append(f"• <b>{html.escape(provider)}</b>: {configured_count}/{settings_count}")
            keyboard.append([self.inline_button(provider, f"bs:p:{provider}")])

        keyboard.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard(keyboard),
            message_id=message_id,
        )

    def send_bot_provider_settings(self, profile: TelegramProfile, provider: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        try:
            group = BotSettingLogicRepository().provider_settings(provider)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return

        lines = [self.t(profile, "bot_settings_provider_title", provider=html.escape(provider)), ""]
        not_configured = self.t(profile, "bot_settings_not_configured")
        for item in group.get("settings", []):
            label = html.escape(str(item.get("label") or item.get("key") or ""))
            source = html.escape(str(item.get("source") or ""))
            value = item.get("value") if item.get("is_configured") else not_configured
            value = html.escape(str(value or not_configured))
            lines.append(f"• <b>{label}</b>: <code>{value}</code> ({source})")

        lines.extend(["", self.t(profile, "bot_settings_choose_key")])

        keyboard: list[list[dict[str, Any]]] = []
        for index, item in enumerate(group.get("settings", [])):
            key = str(item.get("key") or "")
            label = str(item.get("label") or key)
            button_text = self.with_icon(TelegramBotIconKeyVO.EDIT, label)
            keyboard.append([self.inline_button(button_text, f"bs:k:{provider}:{index}")])

        keyboard.extend(
            [
                [self.inline_button(self.button(profile, "bot_settings"), self.CALLBACK_BOT_SETTINGS)],
                [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
            ]
        )
        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard(keyboard),
            message_id=message_id,
        )

    def send_bot_setting_edit_options(
        self,
        profile: TelegramProfile,
        *,
        provider: str,
        key_index: int,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        definition = self.bot_setting_definition_by_index(provider, key_index)
        if definition is None:
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        try:
            presentation = BotSettingLogicRepository().presentation(definition)
        except Exception as exc:
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(exc))), reply_markup=self.main_menu_keyboard(profile))
            return

        not_configured = self.t(profile, "bot_settings_not_configured")
        value = presentation.value if presentation.is_configured else not_configured
        lines = [
            self.t(profile, "bot_settings_edit_title"),
            "",
            f"<b>{html.escape(presentation.label)}</b>",
            f"Provider: <code>{html.escape(provider)}</code>",
            f"Key: <code>{html.escape(definition.key)}</code>",
            f"Env fallback: <code>{html.escape(definition.env_name)}</code>",
            f"{self.t(profile, 'bot_settings_current_value')}: <code>{html.escape(str(value or not_configured))}</code>",
            f"{self.t(profile, 'bot_settings_source')}: <code>{html.escape(str(presentation.source))}</code>",
            f"{self.t(profile, 'bot_settings_type')}: <code>{html.escape(str(definition.value_type))}</code>",
        ]
        if definition.choices:
            choices = ", ".join(html.escape(choice) for choice in definition.choices)
            lines.append(f"{self.t(profile, 'bot_settings_choices')}: <code>{choices}</code>")
        if definition.help_text:
            lines.extend(["", html.escape(definition.help_text)])

        lines.extend(["", self.t(profile, "bot_settings_db_only_notice")])
        keyboard: list[list[dict[str, Any]]] = []
        if definition.choices:
            for choice_index, choice in enumerate(definition.choices):
                keyboard.append([self.inline_button(self.with_icon(TelegramBotIconKeyVO.SUCCESS, choice), f"bs:v:{provider}:{key_index}:{choice_index}")])
            keyboard.append([self.inline_button(self.t(profile, "bot_settings_custom_value_button"), f"bs:w:{provider}:{key_index}:db")])
        else:
            keyboard.append([self.inline_button(self.t(profile, "bot_settings_edit_value_button"), f"bs:w:{provider}:{key_index}:db")])
        keyboard.extend([
            [self.inline_button(self.t(profile, "bot_settings_delete_db_value_button"), f"bs:del:{provider}:{key_index}")],
            [self.inline_button(self.t(profile, "bot_settings_provider_title", provider=provider), f"bs:p:{provider}")],
            [self.inline_button(self.button(profile, "bot_settings"), self.CALLBACK_BOT_SETTINGS)],
        ])
        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.inline_keyboard(keyboard),
            message_id=message_id,
        )

    def start_bot_setting_edit_flow(
        self,
        profile: TelegramProfile,
        *,
        provider: str,
        key_index: int,
        write_target: str,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        definition = self.bot_setting_definition_by_index(provider, key_index)
        if definition is None:
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        if write_target != "db":
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_env_write_disabled"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.set_bot_setting_edit_data(
            profile.chat_id,
            {
                "provider": provider,
                "key": definition.key,
                "key_index": key_index,
                "write_target": "db",
            },
        )
        self.set_action(profile.chat_id, self.STATE_BOT_SETTING_VALUE)

        lines = [
            self.t(
                profile,
                "bot_settings_send_value_prompt",
                label=html.escape(definition.label),
                env_name=html.escape(definition.env_name),
            )
        ]
        if definition.choices:
            choices = ", ".join(f"<code>{html.escape(choice)}</code>" for choice in definition.choices)
            lines.extend(["", f"{self.t(profile, 'bot_settings_choices')}: {choices}"])

        self.send_chain_message(
            profile,
            "\n".join(lines),
            reply_markup=self.cancel_keyboard(profile),
            message_id=message_id,
        )

    def handle_bot_setting_value_text(self, profile: TelegramProfile, text: str) -> None:
        if not self.is_admin_profile(profile):
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        pending_data = self.get_bot_setting_edit_data(profile.chat_id)
        provider = str(pending_data.get("provider") or "")
        key = str(pending_data.get("key") or "")
        if not provider or not key:
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_pending_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        definition = BotSettingRegistryVO.definition(provider, key)
        if definition is None:
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        raw_value = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()
        try:
            value = BotSettingLogicRepository.normalize_value(definition=definition, raw_value=raw_value)
        except Exception as exc:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_invalid_value", error=html.escape(self.validation_message(exc))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        user = profile.user if profile.user_id else None
        if not user or not getattr(user, "email", ""):
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_email_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        pending_data.update({"value": value, "write_target": "db"})
        self.set_bot_setting_edit_data(profile.chat_id, pending_data)

        try:
            self.send_bot_setting_confirmation_email(profile, definition)
        except Exception as exc:
            logger.exception("Failed to send bot setting confirmation email.")
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_email_send_failed", error=html.escape(self.validation_message(exc))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_BOT_SETTING_EMAIL_CODE)
        self.client.send_message(
            profile.chat_id,
            self.t(
                profile,
                "bot_settings_email_code_sent",
                email=html.escape(self.mask_email(user.email)),
                minutes=self.BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES,
            ),
            reply_markup=self.cancel_keyboard(profile),
        )

    def handle_bot_setting_email_code_text(self, profile: TelegramProfile, code: str) -> None:
        code = code.strip()
        if not code.isdigit() or len(code) != 6:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "code_only"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        if not self.is_admin_profile(profile):
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        pending_data = self.get_bot_setting_edit_data(profile.chat_id)
        provider = str(pending_data.get("provider") or "")
        key = str(pending_data.get("key") or "")
        value = pending_data.get("value")
        is_delete_operation = bool(pending_data.get("delete"))
        if not provider or not key or (value is None and not is_delete_operation):
            self.clear_action(profile.chat_id)
            self.clear_bot_setting_edit_data(profile.chat_id)
            self.clear_bot_setting_email_code(profile.chat_id)
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_pending_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if not self.verify_bot_setting_email_code(profile.chat_id, code):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_email_code_invalid"),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        try:
            if is_delete_operation:
                result = BotSettingLogicRepository().delete_provider_setting(
                    provider=provider,
                    key=key,
                    user=profile.user,
                )
            else:
                BotSettingLogicRepository().update_provider_settings(
                    provider=provider,
                    raw_settings={key: value},
                    user=profile.user,
                    write_to_database=True,
                    write_to_env=False,
                )
                result = {"deleted": False}
        except Exception as exc:
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_invalid_value", error=html.escape(self.validation_message(exc))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.clear_action(profile.chat_id)
        self.clear_bot_setting_edit_data(profile.chat_id)
        self.clear_bot_setting_email_code(profile.chat_id)
        if is_delete_operation:
            message_key = "bot_settings_db_value_deleted" if result.get("deleted") else "bot_settings_db_value_not_found"
            self.client.send_message(
                profile.chat_id,
                self.t(profile, message_key, provider=html.escape(provider), key=html.escape(key)),
                reply_markup=self.main_menu_keyboard(profile),
            )
        else:
            self.client.send_message(
                profile.chat_id,
                self.t(
                    profile,
                    "bot_settings_value_saved",
                    provider=html.escape(provider),
                    key=html.escape(key),
                    target=html.escape(self.bot_setting_target_label(profile, "db")),
                ),
                reply_markup=self.main_menu_keyboard(profile),
            )
        self.send_bot_provider_settings(profile, provider)


    def choose_bot_setting_choice_value(
        self,
        profile: TelegramProfile,
        *,
        provider: str,
        key_index: int,
        choice_index: int,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        definition = self.bot_setting_definition_by_index(provider, key_index)
        if definition is None or not definition.choices or choice_index < 0 or choice_index >= len(definition.choices):
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        self.set_bot_setting_edit_data(
            profile.chat_id,
            {
                "provider": provider,
                "key": definition.key,
                "key_index": key_index,
                "write_target": "db",
            },
        )
        self.set_action(profile.chat_id, self.STATE_BOT_SETTING_VALUE)
        self.handle_bot_setting_value_text(profile, str(definition.choices[choice_index]))

    def confirm_delete_bot_setting_database_value(
        self,
        profile: TelegramProfile,
        *,
        provider: str,
        key_index: int,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        definition = self.bot_setting_definition_by_index(provider, key_index)
        if definition is None:
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        text = self.t(
            profile,
            "bot_settings_delete_confirm",
            label=html.escape(definition.label),
            provider=html.escape(provider),
            key=html.escape(definition.key),
        )
        keyboard = self.inline_keyboard(
            [
                [self.inline_button(self.t(profile, "confirm_delete_button"), f"bs:delc:{provider}:{key_index}")],
                [self.inline_button(self.t(profile, "bot_settings_provider_title", provider=provider), f"bs:p:{provider}")],
            ]
        )
        self.send_chain_message(profile, text, reply_markup=keyboard, message_id=message_id)

    def delete_bot_setting_database_value(
        self,
        profile: TelegramProfile,
        *,
        provider: str,
        key_index: int,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        definition = self.bot_setting_definition_by_index(provider, key_index)
        if definition is None:
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return

        user = profile.user if profile.user_id else None
        if not user or not getattr(user, "email", ""):
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_email_missing"),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.set_bot_setting_edit_data(
            profile.chat_id,
            {
                "provider": provider,
                "key": definition.key,
                "key_index": key_index,
                "write_target": "db",
                "delete": True,
            },
        )
        try:
            self.send_bot_setting_confirmation_email(profile, definition)
        except Exception as exc:
            logger.exception("Failed to send bot setting delete confirmation email.")
            self.client.send_message(
                profile.chat_id,
                self.t(profile, "bot_settings_email_send_failed", error=html.escape(self.validation_message(exc))),
                reply_markup=self.cancel_keyboard(profile),
            )
            return

        self.set_action(profile.chat_id, self.STATE_BOT_SETTING_EMAIL_CODE)
        self.send_chain_message(
            profile,
            self.t(
                profile,
                "bot_settings_delete_email_code_sent",
                email=html.escape(self.mask_email(user.email)),
                minutes=self.BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES,
            ),
            reply_markup=self.cancel_keyboard(profile),
            message_id=message_id,
        )

    def send_bot_setting_confirmation_email(self, profile: TelegramProfile, definition) -> bool:
        user = profile.user
        code = VerificationCodeCacheAdapter.generate_code()
        if not self.set_bot_setting_email_code(profile.chat_id, code):
            return False
        send_html_email_async(
            subject="تایید تغییر تنظیمات بات",
            template_name="emails/fa_verification_code.html",
            context={
                "subject": "کد تایید تغییر تنظیمات بات",
                "app_name": get_project_name(),
                "user_name": user.first_name or user.username or "there",
                "code": code,
                "expiration_minutes": self.BOT_SETTING_CONFIRM_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )
        return True

    @staticmethod
    def mask_email(email: str) -> str:
        value = str(email or "").strip()
        if "@" not in value:
            return value
        local, domain = value.split("@", 1)
        if len(local) <= 2:
            masked_local = local[:1] + "*"
        else:
            masked_local = local[:2] + "*" * max(len(local) - 2, 1)
        return f"{masked_local}@{domain}"

    @staticmethod
    def bot_setting_definition_by_index(provider: str, key_index: int):
        definitions = BotSettingRegistryVO.definitions(provider)
        if key_index < 0 or key_index >= len(definitions):
            return None
        return definitions[key_index]

    def bot_setting_target_label(self, profile: TelegramProfile, write_target: str) -> str:
        return self.t(profile, "bot_settings_target_db")

    @staticmethod
    def bot_setting_target_flags(write_target: str) -> tuple[bool, bool]:
        return True, False

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
            ("telegram_channel", BotRuntimeConfigProvider.get_env("CHANNEL_INVITE_TELEGRAM_URL")),
            ("bale_channel", BotRuntimeConfigProvider.get_env("CHANNEL_INVITE_BALE_URL")),
            ("rubika_channel", BotRuntimeConfigProvider.get_env("CHANNEL_INVITE_RUBIKA_URL")),
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
    def safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def parse_positive_int(value: str, default: int = 1) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return max(number, 1)

    @staticmethod
    def configured_list_page_size(default: int = 5, maximum: int = 20) -> int:
        value = BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "list_page_size", str(default))
        try:
            page_size = int(value)
        except (TypeError, ValueError):
            page_size = default
        return max(1, min(page_size, maximum))

    @staticmethod
    def total_pages(total_count: int, page_size: int) -> int:
        if page_size <= 0:
            return 1
        return max(1, ((max(total_count, 0) - 1) // page_size) + 1)

    def queue_navigation_rows(self, profile: TelegramProfile, *, page: int, has_next: bool, callback_prefix: str) -> list[list[dict[str, Any]]]:
        refresh_button = self.inline_button(self.t(profile, "refresh_button"), f"{callback_prefix}:{page}")
        main_menu_button = self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)

        if page > 1 and has_next:
            return [
                [
                    self.inline_button(self.t(profile, "prev_button"), f"{callback_prefix}:{page - 1}"),
                    self.inline_button(self.t(profile, "next_button"), f"{callback_prefix}:{page + 1}"),
                ],
                [refresh_button, main_menu_button],
            ]
        if page > 1:
            return [[self.inline_button(self.t(profile, "prev_button"), f"{callback_prefix}:{page - 1}"), refresh_button]]
        if has_next:
            return [[refresh_button, self.inline_button(self.t(profile, "next_button"), f"{callback_prefix}:{page + 1}")]]
        return [[refresh_button, main_menu_button]]

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

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "e":
                self.send_course_edit_fields(profile, parts[2], message_id=message_id)
                return True

            if len(parts) == 4 and parts[0] == "a" and parts[1] == "ef":
                self.start_course_edit_field_flow(profile, course_id=parts[2], field=parts[3], message_id=message_id)
                return True

            if len(parts) == 5 and parts[0] == "a" and parts[1] == "ev":
                self.update_course_field_from_bot(profile, course_id=parts[2], field=parts[3], raw_value=parts[4], message_id=message_id)
                return True

            if len(parts) == 4 and parts[0] == "a" and parts[1] == "cv":
                self.handle_course_create_choice_callback(profile, field=parts[2], raw_value=parts[3], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "del":
                self.confirm_delete_course_from_bot(profile, course_id=parts[2], message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "a" and parts[1] == "delc":
                self.delete_course_from_bot(profile, course_id=parts[2], message_id=message_id)
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
                self.start_checkout_discount_flow(profile, parts[2], message_id=message_id)
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

            if len(parts) == 3 and parts[0] == "p" and parts[1] == "r":
                self.start_payment_receipt_flow(profile, parts[2])
                return True

            if data == "pay:q":
                self.send_payment_receipt_queue(profile, page=1, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "pay" and parts[1] == "q":
                self.send_payment_receipt_queue(profile, page=self.parse_positive_int(parts[2]), message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "pay" and parts[1] in {"a", "x"}:
                self.review_payment_receipt_from_bot(profile, receipt_id=parts[2], approve=parts[1] == "a", message_id=message_id)
                return True

            if data == "r:q":
                self.send_review_queue(profile, page=1, message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "r" and parts[1] == "q":
                self.send_review_queue(profile, page=self.parse_positive_int(parts[2]), message_id=message_id)
                return True

            if len(parts) == 3 and parts[0] == "r" and parts[1] in {"a", "x"}:
                self.moderate_review_from_bot(profile, review_id=parts[2], approve=parts[1] == "a", message_id=message_id)
                return True
        except Exception as error:
            logger.exception("Telegram commerce callback failed")
            self.client.send_message(
                profile.chat_id,
                self.warning_text(html.escape(self.validation_message(error))),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return True

        return False

    def send_course_list(self, profile: TelegramProfile, page: int = 1, *, message_id: int | None = None) -> None:
        courses, has_next = self.commerce_logic.list_courses(page=page, page_size=self.COMMERCE_FEATURE.PUBLIC_LIST_PAGE_SIZE)
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
            rating_text = f" {self.icon(TelegramBotIconKeyVO.STAR)} {float(rating):.1f}" if rating else ""
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
        rating_text = f"{self.icon(TelegramBotIconKeyVO.STAR)} {float(rating):.1f}" if rating else f"{self.icon(TelegramBotIconKeyVO.STAR)} -"
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
            lock = self.icon(TelegramBotIconKeyVO.UNLOCKED) if lesson.is_preview or is_enrolled else self.icon(TelegramBotIconKeyVO.LOCKED)
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

    def checkout_course_from_bot(self, profile: TelegramProfile, course_id: str, *, discount_code: str = "", message_id: int | None = None) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        try:
            order, payment, paid_now = self.commerce_logic.checkout_course(user=user, course_id=course_id, discount_code=discount_code)
        except Exception as error:
            message = self.validation_message(error)
            if "already" in message.lower():
                message = self.t(profile, "course_already_owned")
            self.client.send_message(
                profile.chat_id,
                self.warning_text(html.escape(message)),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        if paid_now:
            message = self.t(profile, "payment_success")
        elif payment and payment.provider in {PaymentProviderEnum.MANUAL.value, PaymentProviderEnum.CARD_TO_CARD.value}:
            message = self.t(profile, "payment_manual")
        else:
            message = self.t(profile, "payment_created")

        self.send_chain_message(
            profile,
            self.order_payment_text(profile, order, payment, message),
            reply_markup=self.inline_keyboard(self.payment_action_keyboard(profile, payment, course_id)),
            message_id=message_id,
        )

    @classmethod
    def payment_receipt_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_payment_receipt:{chat_id}"

    @classmethod
    def get_payment_receipt_flow_data(cls, chat_id: int) -> dict[str, Any]:
        data = TelegramBotCacheRepository.get_value(cls.payment_receipt_flow_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_payment_receipt_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.payment_receipt_flow_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_payment_receipt_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.payment_receipt_flow_cache_key(chat_id))

    def start_payment_receipt_flow(self, profile: TelegramProfile, payment_id: str) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        self.set_payment_receipt_flow_data(profile.chat_id, {"payment_id": payment_id})
        self.set_action(profile.chat_id, self.STATE_PAYMENT_RECEIPT_TRACKING)
        self.delete_chain_message(profile.chat_id)
        self.client.send_message(profile.chat_id, self.t(profile, "payment_receipt_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_payment_receipt_tracking_text(self, profile: TelegramProfile, text: str) -> None:
        user = self.require_linked_user(profile)
        if not user:
            return
        tracking_code = text.strip()
        if len(tracking_code) < 3:
            self.client.send_message(profile.chat_id, self.t(profile, "payment_receipt_prompt"), reply_markup=self.cancel_keyboard(profile))
            return
        data = self.get_payment_receipt_flow_data(profile.chat_id)
        try:
            receipt = self.commerce_logic.upload_payment_receipt(
                user=user,
                payment_id=data.get("payment_id"),
                tracking_code=tracking_code,
                note="Registered from bot.",
            )
        except Exception as error:
            logger.exception("Telegram payment receipt registration failed")
            self.client.send_message(
                profile.chat_id,
                self.warning_text(html.escape(self.validation_message(error))),
                reply_markup=self.main_menu_keyboard(profile),
            )
            self.clear_all_flow_data(profile.chat_id)
            return

        self.clear_all_flow_data(profile.chat_id)
        self.notify_admins_about_payment_receipt(receipt)
        self.client.send_message(
            profile.chat_id,
            self.t(profile, "payment_receipt_saved_with_id", message=self.t(profile, "payment_receipt_saved"), receipt_id=html.escape(str(receipt.id))),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def payment_action_keyboard(self, profile: TelegramProfile, payment, course_id: str) -> list[list[dict[str, Any]]]:
        keyboard = [
            [
                self.inline_button(self.t(profile, "payment_my_courses_button"), "e:mine"),
                self.inline_button(self.t(profile, "payment_my_orders_button"), "o:mine"),
            ]
        ]
        if payment and payment.provider in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value} and payment.status in {PaymentStatusEnum.PENDING_RECEIPT.value, PaymentStatusEnum.RECEIPT_REJECTED.value}:
            keyboard.append([self.inline_button(self.t(profile, "payment_receipt_button"), f"p:r:{self.compact_id(payment.id)}")])
        if payment and payment.payment_url:
            keyboard.append([{"text": self.t(profile, "order_payment_url", url="").replace(": ", "").strip() or "Open payment", "url": payment.payment_url}])
        keyboard.append([self.inline_button(self.t(profile, "course_back_button"), f"c:d:{course_id}")])
        return keyboard

    def send_payment_receipt_queue(self, profile: TelegramProfile, page: int = 1, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        page_size = self.configured_list_page_size()
        receipts, has_next, total_count = self.commerce_logic.list_pending_payment_receipts(page=page, page_size=page_size)
        if not receipts:
            self.send_chain_message(profile, self.t(profile, "payment_queue_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return

        total_pages = self.total_pages(total_count, page_size)
        lines = [
            self.t(profile, "payment_queue_heading"),
            self.t(profile, "list_page_indicator", page=page, total_pages=total_pages, total_count=total_count),
        ]
        keyboard: list[list[dict[str, Any]]] = []
        start_index = ((page - 1) * page_size) + 1
        for index, receipt in enumerate(receipts, start=start_index):
            lines.append(self.payment_receipt_admin_text(profile, receipt, index=index))
            receipt_id = self.compact_id(receipt.id)
            keyboard.append([
                self.inline_button(self.t(profile, "approve_button"), f"pay:a:{receipt_id}"),
                self.inline_button(self.t(profile, "reject_button"), f"pay:x:{receipt_id}"),
            ])
        keyboard.extend(self.queue_navigation_rows(profile, page=page, has_next=has_next, callback_prefix="pay:q"))
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(keyboard), message_id=message_id)
    def payment_receipt_admin_text(self, profile: TelegramProfile, receipt, *, index: int | None = None) -> str:
        payment = receipt.payment
        order = payment.order
        user_name = html.escape(receipt.user.first_name or receipt.user.username or receipt.user.email or "-")
        text = self.t(
            profile,
            "pending_payment_receipt_item",
            order=html.escape(order.order_number),
            user=user_name,
            payment=html.escape(payment.payment_number),
            amount=self.format_money(payment.amount, payment.currency),
            tracking=html.escape(receipt.tracking_code or "-"),
            source=html.escape(receipt.source or "-"),
        )
        prefix = f"<b>#{index}</b>\n" if index is not None else ""
        receipt_url = self.receipt_visible_url(receipt)
        if receipt_url:
            link = f'<a href="{html.escape(receipt_url, quote=True)}">{html.escape(self.t(profile, "view_receipt_button"))}</a>'
            return f"{prefix}{text}\n{link}"
        return f"{prefix}{text}"

    @staticmethod
    def receipt_visible_url(receipt) -> str:
        if receipt.receipt_file_url:
            return receipt.receipt_file_url
        receipt_file = getattr(receipt, "receipt_file", None)
        if receipt_file:
            try:
                return receipt_file.url
            except Exception:
                return ""
        return ""

    @staticmethod
    def telegram_receipt_file_metadata_from_note(note: str) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for item in (note or "").split("|"):
            key, separator, value = item.strip().partition("=")
            if separator and key:
                metadata[key.strip()] = value.strip()
        return metadata

    def send_receipt_media_to_admin(self, admin_profile: TelegramProfile, receipt) -> None:
        metadata = self.telegram_receipt_file_metadata_from_note(receipt.note)
        file_id = metadata.get("telegram_file_id")
        if not file_id:
            return

        caption = self.t(admin_profile, "payment_receipt_admin_notified")
        kind = metadata.get("telegram_file_kind")
        if kind == "photo":
            self.client.send_photo(admin_profile.chat_id, file_id, caption=caption)
            return
        self.client.send_document(admin_profile.chat_id, file_id, caption=caption)

    def review_payment_receipt_from_bot(self, profile: TelegramProfile, *, receipt_id: str, approve: bool, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return

        note_key = "admin_payment_approve_note" if approve else "admin_payment_reject_note"
        try:
            receipt, _payment = self.commerce_logic.review_payment_receipt(
                admin_user=profile.user,
                receipt_id=receipt_id,
                approve=approve,
                admin_note=self.t(profile, note_key),
            )
        except Exception as error:
            logger.exception("Telegram payment receipt moderation failed")
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.main_menu_keyboard(profile))
            return

        self.send_chain_message(
            profile,
            self.t(
                profile,
                "payment_receipt_moderated",
                receipt_id=html.escape(str(receipt.id)),
                status=html.escape(PaymentReceiptStatusEnum.APPROVED.value if approve else PaymentReceiptStatusEnum.REJECTED.value),
            ),
            reply_markup=self.inline_keyboard([[
                self.inline_button(self.t(profile, "back_to_payment_queue_button"), "pay:q"),
                self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU),
            ]]),
            message_id=message_id,
        )

    def notify_admins_about_payment_receipt(self, receipt) -> None:
        for admin_profile in self.admin_payment_profiles():
            try:
                self.send_receipt_media_to_admin(admin_profile, receipt)
                keyboard: list[list[dict[str, Any]]] = []
                receipt_url = self.receipt_visible_url(receipt)
                keyboard.append([
                    self.inline_button(self.t(admin_profile, "approve_button"), f"pay:a:{self.compact_id(receipt.id)}"),
                    self.inline_button(self.t(admin_profile, "reject_button"), f"pay:x:{self.compact_id(receipt.id)}"),
                ])
                if receipt_url:
                    keyboard.append([
                        {"text": self.t(admin_profile, "view_receipt_button"), "url": receipt_url},
                        self.inline_button(self.t(admin_profile, "back_to_payment_queue_button"), "pay:q"),
                    ])
                else:
                    keyboard.append([
                        self.inline_button(self.t(admin_profile, "back_to_payment_queue_button"), "pay:q"),
                        self.inline_button(self.t(admin_profile, "main_menu_button"), self.CALLBACK_MAIN_MENU),
                    ])
                self.client.send_message(
                    admin_profile.chat_id,
                    f"{self.t(admin_profile, 'payment_receipt_admin_notified')}\n{self.payment_receipt_admin_text(admin_profile, receipt)}",
                    reply_markup=self.inline_keyboard(keyboard),
                )
            except Exception:
                logger.debug("Could not notify Telegram admin about payment receipt", exc_info=True)

    def admin_payment_profiles(self):
        return (
            TelegramProfile.objects.select_related("user", "user__role")
            .filter(messenger_provider=self.MESSENGER_PROVIDER, is_verified=True, is_active=True, user__is_active=True)
            .filter(Q(user__is_staff=True) | Q(user__is_superuser=True) | Q(user__role__symbol="admin"))
            .order_by("chat_id")
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
        title = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()[:180]
        data["title"] = title
        self.set_review_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_REVIEW_COMMENT)
        self.client.send_message(profile.chat_id, self.t(profile, "review_comment_prompt"), reply_markup=self.cancel_keyboard(profile))

    @classmethod
    def is_valid_review_comment(cls, comment: str) -> bool:
        compact_comment = "".join(comment.split())
        return len(compact_comment) >= cls.MIN_REVIEW_COMMENT_CHARACTERS

    def handle_review_comment_text(self, profile: TelegramProfile, text: str) -> None:
        user = self.require_linked_user(profile)
        if not user:
            self.clear_all_flow_data(profile.chat_id)
            return

        data = self.get_review_flow_data(profile.chat_id)
        if not data.get("course_id") or not data.get("rating"):
            self.clear_all_flow_data(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "canceled"), reply_markup=self.main_menu_keyboard(profile))
            return

        comment = text.strip()
        if not self.is_valid_review_comment(comment):
            self.client.send_message(profile.chat_id, self.t(profile, "review_comment_too_short"), reply_markup=self.cancel_keyboard(profile))
            return

        # Clear the flow before the write. If Telegram retries the same update or
        # the user sends another message quickly, the bot will not keep asking for
        # the same comment step after a valid review text such as "عالی".
        self.clear_all_flow_data(profile.chat_id)

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
                self.warning_text(html.escape(self.validation_message(error))),
                reply_markup=self.main_menu_keyboard(profile),
            )
            return

        self.client.send_message(
            profile.chat_id,
            self.t(profile, "review_saved_with_id", message=self.t(profile, "review_pending"), review_id=html.escape(str(review.id))),
            reply_markup=self.main_menu_keyboard(profile),
        )

    def send_review_queue(self, profile: TelegramProfile, page: int = 1, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        page_size = self.configured_list_page_size()
        reviews, has_next, total_count = self.commerce_logic.list_pending_reviews(page=page, page_size=page_size)
        if not reviews:
            self.send_chain_message(profile, self.t(profile, "review_queue_empty"), reply_markup=self.main_menu_keyboard(profile), message_id=message_id)
            return
        total_pages = self.total_pages(total_count, page_size)
        lines = [
            self.t(profile, "review_queue_heading"),
            self.t(profile, "list_page_indicator", page=page, total_pages=total_pages, total_count=total_count),
        ]
        keyboard: list[list[dict[str, Any]]] = []
        start_index = ((page - 1) * page_size) + 1
        for index, review in enumerate(reviews, start=start_index):
            user_name = html.escape(review.user.first_name or review.user.username or TelegramBotMessageTextVO.DEFAULT_USER_NAME[self.lang(profile)])
            lines.append(
                f"<b>#{index}</b>\n" + self.t(
                    profile,
                    "pending_review_item",
                    course=html.escape(review.course.title),
                    user=user_name,
                    rating=review.rating,
                    comment=html.escape(review.comment[:220]),
                )
            )
            keyboard.append([
                self.inline_button(self.t(profile, "approve_button"), f"r:a:{self.compact_id(review.id)}"),
                self.inline_button(self.t(profile, "reject_button"), f"r:x:{self.compact_id(review.id)}"),
            ])
        keyboard.extend(self.queue_navigation_rows(profile, page=page, has_next=has_next, callback_prefix="r:q"))
        self.send_chain_message(profile, "\n\n".join(lines), reply_markup=self.inline_keyboard(keyboard), message_id=message_id)
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
            reply_markup=self.inline_keyboard([[
                self.inline_button(self.t(profile, "back_to_queue_button"), "r:q"),
                self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU),
            ]]),
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
            if payment.provider in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}:
                card = html.escape(str(payment.response_payload.get("card_number", "")))
                account = html.escape(str(payment.response_payload.get("account_number", "")))
                holder = html.escape(str(payment.response_payload.get("card_holder", "")))
                bank = html.escape(str(payment.response_payload.get("bank_name", "")))
                iban = html.escape(str(payment.response_payload.get("iban", "")))
                if card or account or holder or bank or iban:
                    lines.append(
                        cls.t(
                            profile,
                            "order_payment_card_info",
                            card=card or "-",
                            account=account or "-",
                            holder=holder or "-",
                            bank=bank or "-",
                            iban=iban or "-",
                        )
                    )
                lines.append(cls.t(profile, "order_payment_receipt_hint"))
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

    def handle_payment_queue(self, profile: TelegramProfile, command: TelegramCommand) -> None:
        self.send_payment_receipt_queue(profile)


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
    def course_edit_flow_cache_key(cls, chat_id: int) -> str:
        return f"{cls.CACHE_PREFIX}_admin_course_edit:{chat_id}"

    @classmethod
    def get_course_edit_flow_data(cls, chat_id: int) -> dict[str, Any]:
        data = TelegramBotCacheRepository.get_value(cls.course_edit_flow_cache_key(chat_id))
        return data if isinstance(data, dict) else {}

    @classmethod
    def set_course_edit_flow_data(cls, chat_id: int, data: dict[str, Any]) -> None:
        TelegramBotCacheRepository.set_value(cls.course_edit_flow_cache_key(chat_id), data, timeout=cls.ACTION_TIMEOUT_SECONDS)

    @classmethod
    def clear_course_edit_flow_data(cls, chat_id: int) -> None:
        TelegramBotCacheRepository.delete_value(cls.course_edit_flow_cache_key(chat_id))

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
        if value == TelegramCommerceFeatureVO.CLEAR_VALUE_MARKER:
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
        data["description"] = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()
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
        self.client.send_message(profile.chat_id, self.t(profile, "course_level_prompt"), reply_markup=self.course_level_create_keyboard(profile))

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
        self.client.send_message(profile.chat_id, self.t(profile, "course_publish_prompt"), reply_markup=self.course_publish_create_keyboard(profile))

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
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.main_menu_keyboard(profile))
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


    @classmethod
    def course_editable_fields(cls) -> list[str]:
        return list(cls.COMMERCE_FEATURE.EDITABLE_FIELDS)

    def course_field_label(self, profile: TelegramProfile, field: str) -> str:
        return self.t(profile, self.COMMERCE_FEATURE.field_text_key(field))

    @classmethod
    def course_field_choices(cls, field: str) -> list[str]:
        if field == cls.COMMERCE_FEATURE.FIELD_LEVEL:
            return [item.value for item in CourseLevelEnum]
        if field == cls.COMMERCE_FEATURE.FIELD_CURRENCY:
            return [item.value for item in CurrencyEnum]
        if field == cls.COMMERCE_FEATURE.FIELD_STATUS:
            return [item.value for item in CourseStatusEnum]
        if field == cls.COMMERCE_FEATURE.FIELD_IS_FEATURED:
            return [cls.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE, cls.COMMERCE_FEATURE.BOOLEAN_FALSE_VALUE]
        return []

    def course_level_create_keyboard(self, profile: TelegramProfile) -> dict[str, Any]:
        rows = [[self.inline_button(level.value, f"a:cv:{self.COMMERCE_FEATURE.CREATE_LEVEL_FIELD}:{level.value}")] for level in CourseLevelEnum]
        rows.append([self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)])
        return self.inline_keyboard(rows)

    def course_publish_create_keyboard(self, profile: TelegramProfile) -> dict[str, Any]:
        return self.inline_keyboard(
            [
                [self.inline_button(self.t(profile, "publish_button"), f"a:cv:{self.COMMERCE_FEATURE.CREATE_PUBLISH_FIELD}:{self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE}")],
                [self.inline_button(self.t(profile, "unpublish_button"), f"a:cv:{self.COMMERCE_FEATURE.CREATE_PUBLISH_FIELD}:{self.COMMERCE_FEATURE.BOOLEAN_FALSE_VALUE}")],
                [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
            ]
        )

    def lesson_preview_create_keyboard(self, profile: TelegramProfile) -> dict[str, Any]:
        return self.inline_keyboard(
            [
                [self.inline_button(self.t(profile, "yes"), f"a:cv:{self.COMMERCE_FEATURE.CREATE_PREVIEW_FIELD}:{self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE}")],
                [self.inline_button(self.t(profile, "no"), f"a:cv:{self.COMMERCE_FEATURE.CREATE_PREVIEW_FIELD}:{self.COMMERCE_FEATURE.BOOLEAN_FALSE_VALUE}")],
                [self.inline_button(self.t(profile, "main_menu_button"), self.CALLBACK_MAIN_MENU)],
            ]
        )

    def course_edit_choice_keyboard(self, profile: TelegramProfile, *, course_id: str, field: str) -> dict[str, Any]:
        rows: list[list[dict[str, Any]]] = []
        for value in self.course_field_choices(field):
            label = value
            if field == self.COMMERCE_FEATURE.FIELD_IS_FEATURED:
                label = self.t(profile, "yes") if value == self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE else self.t(profile, "no")
            rows.append([self.inline_button(label, f"a:ev:{course_id}:{field}:{value}")])
        rows.append([self.inline_button(self.t(profile, "course_edit_back_button"), f"a:e:{course_id}")])
        return self.inline_keyboard(rows)

    def send_course_edit_fields(self, profile: TelegramProfile, course_id: str, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        course = self.commerce_logic.get_admin_course(course_id)
        compact_course_id = self.compact_id(course.id)
        lines = [self.t(profile, "course_edit_title", title=html.escape(course.title)), "", self.admin_course_text(profile, course)]
        rows: list[list[dict[str, Any]]] = []
        for field in self.course_editable_fields():
            rows.append([self.inline_button(self.with_icon(TelegramBotIconKeyVO.EDIT, self.course_field_label(profile, field)), f"a:ef:{compact_course_id}:{field}")])
        rows.extend(
            [
                [self.inline_button(self.t(profile, "delete_course_button"), f"a:del:{compact_course_id}")],
                [self.inline_button(self.t(profile, "course_back_button"), f"a:d:{compact_course_id}")],
                [self.inline_button(self.t(profile, "all_courses_button"), "a:c:1")],
            ]
        )
        self.send_chain_message(profile, "\n".join(lines), reply_markup=self.inline_keyboard(rows), message_id=message_id)

    def start_course_edit_field_flow(
        self,
        profile: TelegramProfile,
        *,
        course_id: str,
        field: str,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        if field not in self.course_editable_fields():
            self.client.send_message(profile.chat_id, self.t(profile, "unknown"), reply_markup=self.main_menu_keyboard(profile))
            return
        course = self.commerce_logic.get_admin_course(course_id)
        compact_course_id = self.compact_id(course.id)
        current_value = getattr(course, field)
        label = self.course_field_label(profile, field)
        if self.course_field_choices(field):
            text = self.t(
                profile,
                "course_edit_choice_prompt",
                field=html.escape(label),
                current=html.escape(str(current_value)),
            )
            self.send_chain_message(
                profile,
                text,
                reply_markup=self.course_edit_choice_keyboard(profile, course_id=compact_course_id, field=field),
                message_id=message_id,
            )
            return

        self.set_course_edit_flow_data(profile.chat_id, {"course_id": compact_course_id, "field": field})
        self.set_action(profile.chat_id, self.STATE_COURSE_EDIT_VALUE)
        text = self.t(
            profile,
            "course_edit_value_prompt",
            field=html.escape(label),
            current=html.escape(str(current_value if current_value is not None else "")),
        )
        self.send_chain_message(profile, text, reply_markup=self.cancel_keyboard(profile), message_id=message_id)

    def handle_course_create_choice_callback(
        self,
        profile: TelegramProfile,
        *,
        field: str,
        raw_value: str,
        message_id: int | None = None,
    ) -> None:
        action = self.get_action(profile.chat_id)
        if field == self.COMMERCE_FEATURE.CREATE_LEVEL_FIELD and action == self.STATE_COURSE_LEVEL:
            self.handle_course_level_text(profile, raw_value)
            return
        if field == self.COMMERCE_FEATURE.CREATE_PUBLISH_FIELD and action == self.STATE_COURSE_PUBLISH:
            self.handle_course_publish_text(profile, "yes" if raw_value == self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE else "no")
            return
        if field == self.COMMERCE_FEATURE.CREATE_PREVIEW_FIELD and action == self.STATE_LESSON_PREVIEW:
            self.handle_lesson_preview_text(profile, "yes" if raw_value == self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE else "no")
            return
        self.client.send_message(profile.chat_id, self.t(profile, "course_choice_session_expired"), reply_markup=self.main_menu_keyboard(profile))

    def handle_course_edit_value_text(self, profile: TelegramProfile, text: str) -> None:
        pending_data = self.get_course_edit_flow_data(profile.chat_id)
        course_id = str(pending_data.get("course_id") or "")
        field = str(pending_data.get("field") or "")
        if not course_id or not field:
            self.clear_action(profile.chat_id)
            self.clear_course_edit_flow_data(profile.chat_id)
            self.client.send_message(profile.chat_id, self.t(profile, "course_edit_session_expired"), reply_markup=self.main_menu_keyboard(profile))
            return
        self.update_course_field_from_bot(profile, course_id=course_id, field=field, raw_value=text)

    def update_course_field_from_bot(
        self,
        profile: TelegramProfile,
        *,
        course_id: str,
        field: str,
        raw_value: str,
        message_id: int | None = None,
    ) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            value = self.normalize_course_edit_value(field, raw_value)
            if field == self.COMMERCE_FEATURE.FIELD_STATUS:
                course = self.commerce_logic.update_course_status(admin_user=profile.user, course_id=course_id, status=value)
            else:
                course = self.commerce_logic.update_course_field(admin_user=profile.user, course_id=course_id, field=field, value=value)
        except Exception as error:
            logger.exception("Telegram course field update failed")
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.cancel_keyboard(profile))
            return
        self.clear_action(profile.chat_id)
        self.clear_course_edit_flow_data(profile.chat_id)
        self.send_chain_message(
            profile,
            f"{self.t(profile, 'course_field_updated')}\n\n{self.admin_course_text(profile, course)}",
            reply_markup=self.admin_course_keyboard(profile, course),
            message_id=message_id,
        )

    def normalize_course_edit_value(self, field: str, raw_value: Any):
        value = str(raw_value or "").strip()
        if field not in self.course_editable_fields():
            raise ValidationError("Unsupported course field.")
        if field == self.COMMERCE_FEATURE.FIELD_TITLE:
            if len(value) < 3 or len(value) > 180:
                raise ValidationError(self.t(None, "course_title_invalid"))
            return value
        if field == self.COMMERCE_FEATURE.FIELD_SHORT_DESCRIPTION:
            value = "" if value == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else value
            if len(value) > 300:
                raise ValidationError("Short description must be at most 300 characters.")
            return value
        if field == self.COMMERCE_FEATURE.FIELD_DESCRIPTION:
            return "" if value == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else value
        if field == self.COMMERCE_FEATURE.FIELD_PRICE:
            amount = self.parse_decimal_amount(value)
            if amount is None:
                raise ValidationError("Course price must be a non-negative number.")
            return amount
        if field == self.COMMERCE_FEATURE.FIELD_DURATION_MINUTES:
            if value == "0":
                return 0
            duration = self.parse_optional_positive_int(value)
            if duration is None:
                raise ValidationError("Duration must be 0 or a positive integer.")
            return duration
        if field == self.COMMERCE_FEATURE.FIELD_CURRENCY:
            allowed = {item.value for item in CurrencyEnum}
            if value not in allowed:
                raise ValidationError(f"Currency must be one of: {', '.join(sorted(allowed))}")
            return value
        if field == self.COMMERCE_FEATURE.FIELD_LEVEL:
            allowed = {item.value for item in CourseLevelEnum}
            if value not in allowed:
                raise ValidationError(f"Level must be one of: {', '.join(sorted(allowed))}")
            return value
        if field == self.COMMERCE_FEATURE.FIELD_STATUS:
            allowed = {item.value for item in CourseStatusEnum}
            if value not in allowed:
                raise ValidationError(f"Status must be one of: {', '.join(sorted(allowed))}")
            return value
        if field == self.COMMERCE_FEATURE.FIELD_IS_FEATURED:
            parsed = self.parse_yes_no(value)
            if parsed is None:
                if value.lower() == self.COMMERCE_FEATURE.BOOLEAN_TRUE_VALUE:
                    return True
                if value.lower() == self.COMMERCE_FEATURE.BOOLEAN_FALSE_VALUE:
                    return False
                raise ValidationError("Featured must be yes/no.")
            return parsed
        return value

    def confirm_delete_course_from_bot(self, profile: TelegramProfile, *, course_id: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        course = self.commerce_logic.get_admin_course(course_id)
        compact_course_id = self.compact_id(course.id)
        text = self.t(profile, "course_delete_confirm", title=html.escape(course.title))
        keyboard = self.inline_keyboard(
            [
                [self.inline_button(self.t(profile, "confirm_delete_button"), f"a:delc:{compact_course_id}")],
                [self.inline_button(self.t(profile, "course_back_button"), f"a:d:{compact_course_id}")],
            ]
        )
        self.send_chain_message(profile, text, reply_markup=keyboard, message_id=message_id)

    def delete_course_from_bot(self, profile: TelegramProfile, *, course_id: str, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.client.send_message(profile.chat_id, self.t(profile, "admin_only"), reply_markup=self.main_menu_keyboard(profile))
            return
        try:
            course = self.commerce_logic.delete_course(admin_user=profile.user, course_id=course_id)
        except Exception as error:
            logger.exception("Telegram course delete failed")
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.main_menu_keyboard(profile))
            return
        self.send_chain_message(
            profile,
            self.t(profile, "course_deleted", title=html.escape(course.title)),
            reply_markup=self.inline_keyboard([[self.inline_button(self.t(profile, "all_courses_button"), "a:c:1")]]),
            message_id=message_id,
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
        data["description"] = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_CONTENT)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_content_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_content_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_lesson_flow_data(profile.chat_id)
        data["content"] = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()
        self.set_lesson_flow_data(profile.chat_id, data)
        self.set_action(profile.chat_id, self.STATE_LESSON_VIDEO_URL)
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_video_url_prompt"), reply_markup=self.cancel_keyboard(profile))

    def handle_lesson_video_url_text(self, profile: TelegramProfile, text: str) -> None:
        data = self.get_lesson_flow_data(profile.chat_id)
        data["video_url"] = "" if text.strip() == self.COMMERCE_FEATURE.CLEAR_VALUE_MARKER else text.strip()
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
        self.client.send_message(profile.chat_id, self.t(profile, "lesson_preview_prompt"), reply_markup=self.lesson_preview_create_keyboard(profile))

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
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.main_menu_keyboard(profile))
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
        courses, has_next = self.commerce_logic.list_admin_courses(page=page, page_size=self.COMMERCE_FEATURE.ADMIN_LIST_PAGE_SIZE)
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
            self.client.send_message(profile.chat_id, self.warning_text(html.escape(self.validation_message(error))), reply_markup=self.main_menu_keyboard(profile))
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
        rows.append([self.inline_button(self.t(profile, "edit_course_button"), f"a:e:{course_id}")])
        rows.append([self.inline_button(self.t(profile, "add_lesson_button"), f"a:lc:{course_id}")])
        if course.status != CourseStatusEnum.PUBLISHED.value:
            rows.append([self.inline_button(self.t(profile, "publish_button"), f"a:p:{course_id}")])
        else:
            rows.append([self.inline_button(self.t(profile, "unpublish_button"), f"a:u:{course_id}")])
        if course.status != CourseStatusEnum.ARCHIVED.value:
            rows.append([self.inline_button(self.t(profile, "archive_button"), f"a:x:{course_id}")])
        rows.append([self.inline_button(self.t(profile, "delete_course_button"), f"a:del:{course_id}")])
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
            rows.append([cls.button(profile, "my_orders"), cls.button(profile, "account")])
            if profile and cls.is_admin_profile(profile):
                rows.append([cls.button(profile, "admin_courses"), cls.button(profile, "create_course")])
                rows.append([cls.button(profile, "create_user"), cls.button(profile, "review_queue")])
                rows.append([cls.button(profile, "payment_queue"), cls.button(profile, "forgot_password")])
                rows.append([cls.button(profile, "bot_settings"), cls.button(profile, "admin_notification")])
                rows.append([cls.button(profile, "discounts"), cls.button(profile, "support_queue")])
                rows.append([cls.button(profile, "channels"), cls.button(profile, "help")])
            else:
                rows.append([cls.button(profile, "support"), cls.button(profile, "forgot_password")])
                rows.append([cls.button(profile, "channels"), cls.button(profile, "help")])

            verification_buttons: list[str] = []
            if profile and profile.user:
                if not profile.user.email_verified:
                    verification_buttons.append(cls.button(profile, "verify_email"))
                if not profile.user.phone_number_verified:
                    verification_buttons.append(cls.button(profile, "verify_phone"))
            if verification_buttons:
                rows.append(verification_buttons)

            rows.append([cls.button(profile, "language"), cls.button(profile, "unlink")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile), cls.button(profile, "help")])
        else:
            rows.append([cls.button(profile, "courses"), cls.button(profile, "link")])
            rows.append([cls.button(profile, "forgot_password"), cls.button(profile, "channels")])
            if cls.web_app_url():
                rows.append([cls.web_app_button(profile), cls.button(profile, "help")])
                rows.append([cls.button(profile, "language")])
            else:
                rows.append([cls.button(profile, "help"), cls.button(profile, "language")])

        placeholder = cls.t(profile, "placeholder_main_menu")
        return cls.reply_keyboard(rows, placeholder=placeholder)

    @classmethod
    def link_method_keyboard(
        cls,
        profile: TelegramProfile | None = None,
    ) -> dict[str, Any]:
        return cls.reply_keyboard(
            [
                [
                    cls.button(profile, "link_by_email"),
                    cls.button(profile, "link_by_phone"),
                ],
                [
                    cls.button(profile, "main_menu"),
                    cls.button(profile, "cancel"),
                ],
            ],
            placeholder=cls.t(profile, "link_choose"),
        )

    @classmethod
    def forgot_password_method_keyboard(
        cls,
        profile: TelegramProfile | None = None,
    ) -> dict[str, Any]:
        return cls.reply_keyboard(
            [
                [
                    cls.button(profile, "forgot_by_email"),
                    cls.button(profile, "forgot_by_phone"),
                ],
                [
                    cls.button(profile, "main_menu"),
                    cls.button(profile, "cancel"),
                ],
            ],
            placeholder=cls.t(profile, "forgot_choose"),
        )

    @classmethod
    def phone_verification_method_keyboard(
        cls,
        profile: TelegramProfile | None = None,
    ) -> dict[str, Any]:
        rows: list[list[dict[str, Any] | str]] = []
        if profile and profile.user_id and profile.user.phone_number:
            rows.append([cls.button(profile, "verify_phone_sms")])
        rows.append(
            [
                {
                    "text": cls.button(profile, "verify_phone_telegram"),
                    "request_contact": True,
                }
            ]
        )
        rows.append(
            [
                cls.button(profile, "main_menu"),
                cls.button(profile, "cancel"),
            ]
        )
        return cls.reply_keyboard(
            rows,
            placeholder=cls.t(profile, "phone_verify_share_prompt"),
        )

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
        return BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "webapp_url")

    @classmethod
    def web_app_button(cls, profile: TelegramProfile | None = None) -> str:
        return cls.button(profile, "webapp")
