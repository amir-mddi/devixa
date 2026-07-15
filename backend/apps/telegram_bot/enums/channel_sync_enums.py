from __future__ import annotations

from enum import Enum


class MessengerProviderEnum(str, Enum):
    TELEGRAM = "telegram"
    BALE = "bale"
    RUBIKA = "rubika"


class ChannelSyncEventEnum(str, Enum):
    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
