from __future__ import annotations

from enum import Enum


class BotSettingProviderEnum(str, Enum):
    TELEGRAM = "telegram"
    BALE = "bale"
    RUBIKA = "rubika"
    CHANNEL_SYNC = "channel_sync"
    CHANNEL_MEMBER_SYNC = "channel_member_sync"
    COMMERCE_BOT = "commerce_bot"


class BotSettingValueTypeEnum(str, Enum):
    STRING = "string"
    SECRET = "secret"
    URL = "url"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CHOICE = "choice"
