from __future__ import annotations

import html
import re
from typing import Any

import requests

from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.services import TelegramBotService
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider
from dealio.apps.telegram_bot.repositories.logic.commerce_bot_logic import TelegramCommerceBotLogicRepository


class BaleBotClient:
    """Bale Bot API client with the same public methods used by TelegramBotService.

    Bale requests are sent to: {BALE_BOT_BASE_URL}/bot{BALE_BOT_TOKEN}/{method}.
    Runtime settings are read through BotRuntimeConfigProvider; env remains fallback/bootstrap only.
    """

    PROVIDER = BotSettingProviderEnum.BALE.value

    def __init__(self, token: str | None = None, base_url: str | None = None, proxy_url: str | None = None):
        self._token_override = token
        self._base_url_override = base_url
        self._proxy_url_override = proxy_url

    @property
    def token(self) -> str:
        return (self._token_override or BotRuntimeConfigProvider.get(self.PROVIDER, "bot_token") or "").strip()

    @property
    def base_api_url(self) -> str:
        return (self._base_url_override or BotRuntimeConfigProvider.get(self.PROVIDER, "bot_base_url") or "").strip().rstrip("/")

    @property
    def proxy_url(self) -> str:
        provider_proxy = BotRuntimeConfigProvider.get(self.PROVIDER, "proxy_url")
        global_proxy = BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "proxy_url")
        return (self._proxy_url_override or provider_proxy or global_proxy or "").strip()

    @property
    def base_url(self) -> str:
        return f"{self.base_api_url}/bot{self.token}" if self.base_api_url and self.token else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.base_api_url)

    @property
    def proxies(self) -> dict[str, str] | None:
        proxy_url = self.proxy_url
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def _request(self, method_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required.")

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

        if not response.ok or not body.get("ok", False):
            raise RuntimeError(f"Bale API error in {method_name}: {body}")

        return body

    def _request_multipart(
        self,
        method_name: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required.")

        response = requests.post(
            f"{self.base_url}/{method_name}",
            data=data or {},
            files=files or {},
            timeout=(5.0, 60.0),
            proxies=self.proxies,
        )

        try:
            body = response.json()
        except ValueError:
            body = {"ok": False, "description": response.text}

        if not response.ok or not body.get("ok", False):
            raise RuntimeError(f"Bale API error in {method_name}: {body}")

        return body


    @staticmethod
    def _plain_text(text: str) -> str:
        """Keep shared bot messages safe for Bale if HTML parse mode is unsupported."""
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)


    def get_file(self, file_id: str) -> dict[str, Any]:
        return self._request("getFile", {"file_id": file_id})

    def get_file_url(self, file_id: str) -> str:
        body = self.get_file(file_id)
        result = body.get("result") if isinstance(body, dict) else {}
        data = body.get("data") if isinstance(body, dict) else {}
        if not isinstance(result, dict):
            result = {}
        if not isinstance(data, dict):
            data = {}
        file_url = result.get("file_url") or result.get("url") or data.get("file_url") or data.get("url")
        if file_url:
            return str(file_url)
        file_path = result.get("file_path") or data.get("file_path")
        if file_path:
            return f"{self.base_url}/file/{file_path}"
        return ""

    def send_photo(self, chat_id: int | str, photo: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "photo": photo}
        if caption:
            payload["caption"] = self._plain_text(caption)
        return self._request("sendPhoto", payload)

    def send_video(self, chat_id: int | str, video: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "video": video}
        if caption:
            payload["caption"] = self._plain_text(caption)
        return self._request("sendVideo", payload)

    def send_document(self, chat_id: int | str, document: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "document": document}
        if caption:
            payload["caption"] = self._plain_text(caption)
        return self._request("sendDocument", payload)

    def send_sticker(self, chat_id: int | str, sticker: str) -> dict[str, Any]:
        return self._request("sendSticker", {"chat_id": chat_id, "sticker": sticker})

    def send_photo_file(self, chat_id: int | str, content: bytes, *, filename: str = "photo.jpg", caption: str = "", mime_type: str = "image/jpeg") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = self._plain_text(caption)
        return self._request_multipart("sendPhoto", data=data, files={"photo": (filename, content, mime_type)})

    def send_video_file(self, chat_id: int | str, content: bytes, *, filename: str = "video.mp4", caption: str = "", mime_type: str = "video/mp4") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = self._plain_text(caption)
        return self._request_multipart("sendVideo", data=data, files={"video": (filename, content, mime_type)})

    def send_animation_file(self, chat_id: int | str, content: bytes, *, filename: str = "animation.mp4", caption: str = "", mime_type: str = "video/mp4") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = self._plain_text(caption)
        return self._request_multipart("sendAnimation", data=data, files={"animation": (filename, content, mime_type)})

    def send_document_file(self, chat_id: int | str, content: bytes, *, filename: str = "file.bin", caption: str = "", mime_type: str = "application/octet-stream") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data["caption"] = self._plain_text(caption)
        return self._request_multipart("sendDocument", data=data, files={"document": (filename, content, mime_type)})

    def send_sticker_file(self, chat_id: int | str, content: bytes, *, filename: str = "sticker.webp", caption: str = "", mime_type: str = "image/webp") -> dict[str, Any]:
        return self._request_multipart("sendSticker", data={"chat_id": chat_id}, files={"sticker": (filename, content, mime_type)})

    def edit_message_caption(self, chat_id: int | str, message_id: int | str, caption: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": self._plain_text(caption),
        }
        return self._request("editMessageCaption", payload)

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
            "text": self._plain_text(text),
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._request("sendMessage", payload)

    def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": self._plain_text(text),
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self._request("editMessageText", payload)

    def delete_message(self, chat_id: int, message_id: int) -> dict[str, Any]:
        return self._request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = self._plain_text(text)
        return self._request("answerCallbackQuery", payload)

    def set_my_description(self, description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"description": self._plain_text(description)}
        if language_code:
            payload["language_code"] = language_code
        return self._request("setMyDescription", payload)

    def set_my_short_description(self, short_description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"short_description": self._plain_text(short_description)}
        if language_code:
            payload["language_code"] = language_code
        return self._request("setMyShortDescription", payload)

    def set_my_commands(self, commands: list[dict[str, str]], *, language_code: str | None = None) -> dict[str, Any]:
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
            "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return self._request("setWebhook", payload)

    def delete_webhook(self, *, drop_pending_updates: bool = False) -> dict[str, Any]:
        return self._request("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    def get_webhook_info(self) -> dict[str, Any]:
        return self._request("getWebhookInfo")

    def get_chat_member(self, *, chat_id: str | int, user_id: str | int) -> dict[str, Any]:
        return self._request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def get_updates(
        self,
        *,
        offset: int | None = None,
        timeout: int | None = None,
        limit: int | None = None,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        timeout_value = timeout if timeout is not None else BotRuntimeConfigProvider.get_int(self.PROVIDER, "polling_timeout", 30)
        limit_value = limit if limit is not None else BotRuntimeConfigProvider.get_int(self.PROVIDER, "polling_limit", 50)
        payload: dict[str, Any] = {
            "timeout": timeout_value,
            "limit": limit_value,
            "allowed_updates": allowed_updates or ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
        }
        if offset is not None:
            payload["offset"] = offset
        response = self._request("getUpdates", payload)
        return response.get("result", [])


class BaleCommerceBotLogicRepository(TelegramCommerceBotLogicRepository):
    @staticmethod
    def default_payment_provider() -> str:
        provider = BotRuntimeConfigProvider.get(BotSettingProviderEnum.BALE.value, "payment_provider")
        if not provider:
            raise RuntimeError("BALE_PAYMENT_PROVIDER is required.")
        return provider


class BaleBotService(TelegramBotService):
    """Runs the same commerce/account bot use-cases through the Bale client."""

    MESSENGER_PROVIDER = "bale"
    CACHE_PREFIX = "bale"

    def __init__(self, client: BaleBotClient | None = None):
        super().__init__(client=client or BaleBotClient())
        self.commerce_logic = BaleCommerceBotLogicRepository()

    @staticmethod
    def web_app_url() -> str:
        return BotRuntimeConfigProvider.get(BotSettingProviderEnum.BALE.value, "webapp_url")
