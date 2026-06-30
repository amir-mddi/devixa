from __future__ import annotations

from typing import Any

from dealio.apps.telegram_bot.dtos.channel_member_sync_dtos import ChannelMemberCheckDTO
from dealio.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum


class ChannelMemberSyncMessengerAdapter:
    """Messenger API adapter for member checking and invitation delivery.

    Important: Bot APIs do not allow adding arbitrary users to channels. The
    safe operation here is checking a known user's membership when the provider
    supports it, then sending the missing channel invite link to that user's
    private bot chat.
    """

    MEMBER_STATUSES = {"creator", "administrator", "member", "restricted"}
    NON_MEMBER_STATUSES = {"left", "kicked", "banned"}

    def check_member(self, *, provider: str, channel_chat_id: str, user_id: str) -> ChannelMemberCheckDTO:
        try:
            response = self._get_chat_member(provider=provider, chat_id=channel_chat_id, user_id=user_id)
            status = self._extract_member_status(response)
            normalized_status = status.lower()
            return ChannelMemberCheckDTO(
                provider=provider,
                chat_id=channel_chat_id,
                user_id=user_id,
                is_member=normalized_status in self.MEMBER_STATUSES,
                status=status,
            )
        except Exception as exc:
            return ChannelMemberCheckDTO(
                provider=provider,
                chat_id=channel_chat_id,
                user_id=user_id,
                is_member=False,
                error=str(exc),
            )

    def send_invite(self, *, provider: str, chat_id: str, text: str) -> dict[str, Any]:
        client = self._client(provider)
        return client.send_message(chat_id, text)

    def _get_chat_member(self, *, provider: str, chat_id: str, user_id: str) -> dict[str, Any]:
        if provider == MessengerProviderEnum.TELEGRAM.value:
            client = self._client(provider)
            return client.get_chat_member(chat_id=chat_id, user_id=user_id)

        if provider == MessengerProviderEnum.BALE.value:
            client = self._client(provider)
            if hasattr(client, "get_chat_member"):
                return client.get_chat_member(chat_id=chat_id, user_id=user_id)
            return client._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

        raise RuntimeError(f"Unsupported member sync provider: {provider}")

    @classmethod
    def _extract_member_status(cls, response: dict[str, Any]) -> str:
        result = response.get("result") if isinstance(response, dict) else None
        if isinstance(result, dict):
            status = result.get("status")
            if status:
                return str(status)

            member = result.get("member")
            if isinstance(member, dict) and member.get("status"):
                return str(member["status"])

        data = response.get("data") if isinstance(response, dict) else None
        if isinstance(data, dict):
            status = data.get("status")
            if status:
                return str(status)

            member = data.get("member") or data.get("chat_member")
            if isinstance(member, dict) and member.get("status"):
                return str(member["status"])

        return "unknown"

    @staticmethod
    def _client(provider: str):
        if provider == MessengerProviderEnum.TELEGRAM.value:
            from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient

            return TelegramBotClient()

        if provider == MessengerProviderEnum.BALE.value:
            from dealio.apps.telegram_bot.bale_services import BaleBotClient

            return BaleBotClient()

        raise RuntimeError(f"Unsupported member sync provider: {provider}")
