from __future__ import annotations


class BotAccountLinkMethodVO:
    EMAIL = "email"
    PHONE = "phone"


class BotAccountLinkVO:
    CODE_LENGTH = 6
    CODE_EXPIRATION_MINUTES = 10
    SESSION_CACHE_KEY_TEMPLATE = "bot_account_link:{provider}:{chat_id}"

    PROVIDER_DISPLAY_NAMES = {
        "telegram": "Telegram",
        "bale": "Bale",
        "rubika": "Rubika",
    }

    @classmethod
    def provider_display_name(cls, provider: str) -> str:
        normalized_provider = (provider or "").strip().lower()
        return cls.PROVIDER_DISPLAY_NAMES.get(
            normalized_provider,
            normalized_provider.title() or "Messenger",
        )
