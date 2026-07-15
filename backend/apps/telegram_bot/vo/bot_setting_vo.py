from __future__ import annotations

from collections import OrderedDict

from backend.apps.telegram_bot.dtos.bot_setting_dtos import BotSettingDefinitionDTO
from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum, BotSettingValueTypeEnum


class BotSettingSourceVO:
    DATABASE = "database"
    ENV = "env"
    DEFAULT = "default"
    EMPTY = "empty"


class BotSecretMaskVO:
    MASK = "********"


class BotSettingRegistryVO:
    """Allow-list of bot runtime settings that may be changed from the panel.

    Do not dynamically expose every environment variable. This registry prevents
    unrelated infrastructure secrets from appearing in the bot settings UI.
    """

    PAYMENT_PROVIDER_CHOICES = ("manual", "card_to_card", "pardakhtyar", "sandbox")

    DEFINITIONS: "OrderedDict[str, tuple[BotSettingDefinitionDTO, ...]]" = OrderedDict(
        {
            BotSettingProviderEnum.TELEGRAM.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="bot_token",
                    env_name="TELEGRAM_BOT_TOKEN",
                    label="Telegram bot token",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="webhook_secret",
                    env_name="TELEGRAM_WEBHOOK_SECRET",
                    label="Telegram webhook secret",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="webhook_url",
                    env_name="TELEGRAM_WEBHOOK_URL",
                    label="Telegram webhook URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="webapp_url",
                    env_name="TELEGRAM_WEBAPP_URL",
                    label="Telegram web app URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="payment_provider",
                    env_name="TELEGRAM_PAYMENT_PROVIDER",
                    label="Telegram payment provider",
                    value_type=BotSettingValueTypeEnum.CHOICE.value,
                    choices=PAYMENT_PROVIDER_CHOICES,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="list_page_size",
                    env_name="TELEGRAM_LIST_PAGE_SIZE",
                    label="Telegram list page size",
                    value_type=BotSettingValueTypeEnum.INT.value,
                    default="5",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.TELEGRAM.value,
                    key="proxy_url",
                    env_name="PROXY_URL",
                    label="Telegram/global proxy URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                    help_text="Telegram uses PROXY_URL as its proxy fallback.",
                ),
            ),
            BotSettingProviderEnum.BALE.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="bot_token",
                    env_name="BALE_BOT_TOKEN",
                    label="Bale bot token",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="bot_base_url",
                    env_name="BALE_BOT_BASE_URL",
                    label="Bale bot base URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="webhook_secret",
                    env_name="BALE_WEBHOOK_SECRET",
                    label="Bale webhook secret",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="webhook_url",
                    env_name="BALE_WEBHOOK_URL",
                    label="Bale webhook URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="webapp_url",
                    env_name="BALE_WEBAPP_URL",
                    label="Bale web app URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="payment_provider",
                    env_name="BALE_PAYMENT_PROVIDER",
                    label="Bale payment provider",
                    value_type=BotSettingValueTypeEnum.CHOICE.value,
                    choices=PAYMENT_PROVIDER_CHOICES,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="polling_timeout",
                    env_name="BALE_POLLING_TIMEOUT",
                    label="Bale polling timeout",
                    value_type=BotSettingValueTypeEnum.INT.value,
                    default="30",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="polling_limit",
                    env_name="BALE_POLLING_LIMIT",
                    label="Bale polling limit",
                    value_type=BotSettingValueTypeEnum.INT.value,
                    default="50",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.BALE.value,
                    key="proxy_url",
                    env_name="BALE_PROXY_URL",
                    label="Bale proxy URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                    help_text="If empty, Bale falls back to Telegram/global PROXY_URL.",
                ),
            ),
            BotSettingProviderEnum.RUBIKA.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="bot_token",
                    env_name="RUBIKA_BOT_TOKEN",
                    label="Rubika bot token",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="bot_base_url",
                    env_name="RUBIKA_BOT_BASE_URL",
                    label="Rubika bot base URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="webhook_secret",
                    env_name="RUBIKA_WEBHOOK_SECRET",
                    label="Rubika webhook secret",
                    value_type=BotSettingValueTypeEnum.SECRET.value,
                    is_secret=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="webhook_url",
                    env_name="RUBIKA_WEBHOOK_URL",
                    label="Rubika webhook URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="webapp_url",
                    env_name="RUBIKA_WEBAPP_URL",
                    label="Rubika web app URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="payment_provider",
                    env_name="RUBIKA_PAYMENT_PROVIDER",
                    label="Rubika payment provider",
                    value_type=BotSettingValueTypeEnum.CHOICE.value,
                    choices=PAYMENT_PROVIDER_CHOICES,
                    required=True,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="polling_limit",
                    env_name="RUBIKA_POLLING_LIMIT",
                    label="Rubika polling limit",
                    value_type=BotSettingValueTypeEnum.INT.value,
                    default="50",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="polling_sleep_seconds",
                    env_name="RUBIKA_POLLING_SLEEP_SECONDS",
                    label="Rubika polling sleep seconds",
                    value_type=BotSettingValueTypeEnum.FLOAT.value,
                    default="1.0",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.RUBIKA.value,
                    key="proxy_url",
                    env_name="RUBIKA_PROXY_URL",
                    label="Rubika proxy URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                    help_text="If empty, Rubika falls back to Telegram/global PROXY_URL.",
                ),
            ),
            BotSettingProviderEnum.CHANNEL_SYNC.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="enabled",
                    env_name="CHANNEL_SYNC_ENABLED",
                    label="Channel sync enabled",
                    value_type=BotSettingValueTypeEnum.BOOL.value,
                    default="false",
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="telegram_source_chat_id",
                    env_name="CHANNEL_SYNC_TELEGRAM_SOURCE_CHAT_ID",
                    label="Telegram source channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="bale_source_chat_id",
                    env_name="CHANNEL_SYNC_BALE_SOURCE_CHAT_ID",
                    label="Bale source channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="telegram_target_chat_id",
                    env_name="CHANNEL_SYNC_TELEGRAM_TARGET_CHAT_ID",
                    label="Telegram target channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="bale_target_chat_id",
                    env_name="CHANNEL_SYNC_BALE_TARGET_CHAT_ID",
                    label="Bale target channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="rubika_target_chat_id",
                    env_name="CHANNEL_SYNC_RUBIKA_TARGET_CHAT_ID",
                    label="Rubika target channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="max_media_bytes",
                    env_name="CHANNEL_SYNC_MAX_MEDIA_BYTES",
                    label="Channel sync max media bytes",
                    value_type=BotSettingValueTypeEnum.INT.value,
                    default=str(20 * 1024 * 1024),
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="telegram_invite_url",
                    env_name="CHANNEL_INVITE_TELEGRAM_URL",
                    label="Telegram invite URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="bale_invite_url",
                    env_name="CHANNEL_INVITE_BALE_URL",
                    label="Bale invite URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_SYNC.value,
                    key="rubika_invite_url",
                    env_name="CHANNEL_INVITE_RUBIKA_URL",
                    label="Rubika invite URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
            ),
            BotSettingProviderEnum.CHANNEL_MEMBER_SYNC.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_MEMBER_SYNC.value,
                    key="telegram_channel_chat_id",
                    env_name="CHANNEL_MEMBER_SYNC_TELEGRAM_CHAT_ID",
                    label="Telegram member-sync channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_MEMBER_SYNC.value,
                    key="bale_channel_chat_id",
                    env_name="CHANNEL_MEMBER_SYNC_BALE_CHAT_ID",
                    label="Bale member-sync channel chat ID",
                    value_type=BotSettingValueTypeEnum.STRING.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_MEMBER_SYNC.value,
                    key="telegram_invite_url",
                    env_name="CHANNEL_INVITE_TELEGRAM_URL",
                    label="Telegram invite URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.CHANNEL_MEMBER_SYNC.value,
                    key="bale_invite_url",
                    env_name="CHANNEL_INVITE_BALE_URL",
                    label="Bale invite URL",
                    value_type=BotSettingValueTypeEnum.URL.value,
                ),
            ),
            BotSettingProviderEnum.COMMERCE_BOT.value: (
                BotSettingDefinitionDTO(
                    provider=BotSettingProviderEnum.COMMERCE_BOT.value,
                    key="payment_sandbox_enabled",
                    env_name="PAYMENT_SANDBOX_ENABLED",
                    label="Payment sandbox enabled",
                    value_type=BotSettingValueTypeEnum.BOOL.value,
                    default="false",
                ),
            ),
        }
    )

    @classmethod
    def providers(cls) -> tuple[str, ...]:
        return tuple(cls.DEFINITIONS.keys())

    @classmethod
    def definitions(cls, provider: str) -> tuple[BotSettingDefinitionDTO, ...]:
        return cls.DEFINITIONS.get(provider, ())

    @classmethod
    def definition(cls, provider: str, key: str) -> BotSettingDefinitionDTO | None:
        for definition in cls.definitions(provider):
            if definition.key == key:
                return definition
        return None

    @classmethod
    def definition_by_env(cls, env_name: str) -> BotSettingDefinitionDTO | None:
        for definitions in cls.DEFINITIONS.values():
            for definition in definitions:
                if definition.env_name == env_name:
                    return definition
        return None
