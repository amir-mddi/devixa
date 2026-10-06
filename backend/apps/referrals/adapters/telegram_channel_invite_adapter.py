from __future__ import annotations

from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient


class TelegramChannelInviteAdapter:
    """Telegram transport adapter used by the referral domain.

    The domain logic only requests an invite link; Telegram HTTP details remain
    isolated inside the existing Telegram API client.
    """

    def __init__(self, client=None):
        self.client = client or TelegramBotClient()

    def create_invite_link(self, *, channel: str, invite_name: str) -> str:
        response = self.client.create_chat_invite_link(
            chat_id=channel,
            name=invite_name,
        )
        result = response.get("result") or {}
        invite_link = str(result.get("invite_link") or "").strip()
        if not invite_link:
            raise RuntimeError("Telegram did not return an invite link.")
        return invite_link
