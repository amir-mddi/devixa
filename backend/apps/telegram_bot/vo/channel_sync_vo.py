from __future__ import annotations


class ChannelSyncEnvVO:
    ENABLED = "CHANNEL_SYNC_ENABLED"

    # Source channels watched by the dedicated channel sync polling command.
    TELEGRAM_SOURCE_CHAT_ID = "CHANNEL_SYNC_TELEGRAM_SOURCE_CHAT_ID"
    BALE_SOURCE_CHAT_ID = "CHANNEL_SYNC_BALE_SOURCE_CHAT_ID"

    # Target channels used when mirroring from another source.
    TELEGRAM_TARGET_CHAT_ID = "CHANNEL_SYNC_TELEGRAM_TARGET_CHAT_ID"
    BALE_TARGET_CHAT_ID = "CHANNEL_SYNC_BALE_TARGET_CHAT_ID"
    RUBIKA_TARGET_CHAT_ID = "CHANNEL_SYNC_RUBIKA_TARGET_CHAT_ID"

    # Public invite URLs shown by /channels.
    TELEGRAM_INVITE_URL = "CHANNEL_INVITE_TELEGRAM_URL"
    BALE_INVITE_URL = "CHANNEL_INVITE_BALE_URL"
    RUBIKA_INVITE_URL = "CHANNEL_INVITE_RUBIKA_URL"


class ChannelSyncTextKeyVO:
    CHANNELS = "channels"
    CHANNELS_NOT_CONFIGURED = "channels_not_configured"
    CHANNELS_TITLE = "channels_title"
    TELEGRAM_CHANNEL = "telegram_channel"
    BALE_CHANNEL = "bale_channel"
    RUBIKA_CHANNEL = "rubika_channel"
    CHANNEL_SYNC_IGNORED = "channel_sync_ignored"


class ChannelSyncCommandVO:
    CHANNELS = "/channels"


class ChannelSyncButtonKeyVO:
    CHANNELS = "channels"


class ChannelMemberSyncEnvVO:
    TELEGRAM_CHANNEL_CHAT_ID = "CHANNEL_MEMBER_SYNC_TELEGRAM_CHAT_ID"
    BALE_CHANNEL_CHAT_ID = "CHANNEL_MEMBER_SYNC_BALE_CHAT_ID"
    TELEGRAM_INVITE_URL = "CHANNEL_INVITE_TELEGRAM_URL"
    BALE_INVITE_URL = "CHANNEL_INVITE_BALE_URL"


class ChannelMemberSyncTextVO:
    TELEGRAM_INVITE_MESSAGE = (
        "برای عضویت در کانال تلگرام {project_name} از لینک زیر استفاده کنید:\n"
        "{invite_url}"
    )
    BALE_INVITE_MESSAGE = (
        "برای عضویت در کانال بله {project_name} از لینک زیر استفاده کنید:\n"
        "{invite_url}"
    )


class ChannelSyncMediaTextVO:
    GIFT_ICON = "🎁"

    @classmethod
    def gift_title(cls, title: str) -> str:
        return f"{cls.GIFT_ICON} {title}"
