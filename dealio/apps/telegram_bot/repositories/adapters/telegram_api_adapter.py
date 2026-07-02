from __future__ import annotations

import json
from typing import Any

import requests

from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.interfaces.bot_client_interface import BotClientInterface
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider


class TelegramApiAdapter(BotClientInterface):
    """Telegram HTTP API adapter.

    Reads runtime settings through BotRuntimeConfigProvider and keeps all HTTP API
    calls outside controllers/services/logic.
    """

    PROVIDER = BotSettingProviderEnum.TELEGRAM.value

    def __init__(self, token: str | None = None, proxy_url: str | None = None):
        self._token_override = token
        self._proxy_url_override = proxy_url

    @property
    def token(self) -> str:
        return (self._token_override or BotRuntimeConfigProvider.get(self.PROVIDER, "bot_token") or "").strip()

    @property
    def base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    @property
    def proxy_url(self) -> str:
        return (self._proxy_url_override or BotRuntimeConfigProvider.get(self.PROVIDER, "proxy_url") or "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    @property
    def proxies(self) -> dict[str, str] | None:
        proxy_url = self.proxy_url
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def request(self, method_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

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

        if not response.ok or not body.get("ok"):
            raise RuntimeError(f"Telegram API error in {method_name}: {body}")

        return body

    def request_multipart(
        self,
        method_name: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

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

        if not response.ok or not body.get("ok"):
            raise RuntimeError(f"Telegram API error in {method_name}: {body}")

        return body


    def _request(self, method_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request(method_name, payload)


    def get_file(self, file_id: str) -> dict[str, Any]:
        return self.request("getFile", {"file_id": file_id})

    def get_file_url(self, file_id: str) -> str:
        body = self.get_file(file_id)
        result = body.get("result") or {}
        file_path = result.get("file_path")
        if not file_path:
            return ""
        return f"https://api.telegram.org/file/bot{self.token}/{file_path}"

    def send_photo(self, chat_id: str | int, photo: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "photo": photo}
        if caption:
            payload.update({"caption": caption, "parse_mode": "HTML"})
        return self.request("sendPhoto", payload)

    def send_video(self, chat_id: str | int, video: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "video": video}
        if caption:
            payload.update({"caption": caption, "parse_mode": "HTML"})
        return self.request("sendVideo", payload)

    def send_document(self, chat_id: str | int, document: str, *, caption: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "document": document}
        if caption:
            payload.update({"caption": caption, "parse_mode": "HTML"})
        return self.request("sendDocument", payload)

    def send_sticker(self, chat_id: str | int, sticker: str) -> dict[str, Any]:
        return self.request("sendSticker", {"chat_id": chat_id, "sticker": sticker})

    def send_photo_file(self, chat_id: str | int, content: bytes, *, filename: str = "photo.jpg", caption: str = "", mime_type: str = "image/jpeg") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data.update({"caption": caption, "parse_mode": "HTML"})
        return self.request_multipart("sendPhoto", data=data, files={"photo": (filename, content, mime_type)})

    def send_video_file(self, chat_id: str | int, content: bytes, *, filename: str = "video.mp4", caption: str = "", mime_type: str = "video/mp4") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data.update({"caption": caption, "parse_mode": "HTML"})
        return self.request_multipart("sendVideo", data=data, files={"video": (filename, content, mime_type)})

    def send_animation_file(self, chat_id: str | int, content: bytes, *, filename: str = "animation.mp4", caption: str = "", mime_type: str = "video/mp4") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data.update({"caption": caption, "parse_mode": "HTML"})
        return self.request_multipart("sendAnimation", data=data, files={"animation": (filename, content, mime_type)})

    def send_document_file(self, chat_id: str | int, content: bytes, *, filename: str = "file.bin", caption: str = "", mime_type: str = "application/octet-stream") -> dict[str, Any]:
        data: dict[str, Any] = {"chat_id": chat_id}
        if caption:
            data.update({"caption": caption, "parse_mode": "HTML"})
        return self.request_multipart("sendDocument", data=data, files={"document": (filename, content, mime_type)})

    def send_sticker_file(self, chat_id: str | int, content: bytes, *, filename: str = "sticker.webp", caption: str = "", mime_type: str = "image/webp") -> dict[str, Any]:
        return self.request_multipart("sendSticker", data={"chat_id": chat_id}, files={"sticker": (filename, content, mime_type)})

    def edit_message_caption(self, chat_id: str | int, message_id: int | str, caption: str) -> dict[str, Any]:
        return self.request(
            "editMessageCaption",
            {"chat_id": chat_id, "message_id": message_id, "caption": caption, "parse_mode": "HTML"},
        )

    def edit_message_media_file(
        self,
        chat_id: str | int,
        message_id: int | str,
        media_type: str,
        content: bytes,
        *,
        filename: str = "media.bin",
        caption: str = "",
        mime_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        normalized_type = self._editable_media_type(media_type)
        media: dict[str, Any] = {"type": normalized_type, "media": "attach://media"}
        if caption:
            media.update({"caption": caption, "parse_mode": "HTML"})
        return self.request_multipart(
            "editMessageMedia",
            data={"chat_id": chat_id, "message_id": message_id, "media": json.dumps(media)},
            files={"media": (filename, content, mime_type)},
        )

    @staticmethod
    def _editable_media_type(media_type: str) -> str:
        normalized = (media_type or "document").lower()
        if normalized in {"photo", "video", "animation", "document"}:
            return normalized
        return "document"

    def send_message(self, chat_id: str | int, text: str, *, reply_markup: dict[str, Any] | None = None, disable_web_page_preview: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.request("sendMessage", payload)

    def edit_message_text(self, chat_id: str | int, message_id: int, text: str, *, reply_markup: dict[str, Any] | None = None, disable_web_page_preview: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.request("editMessageText", payload)

    def delete_message(self, chat_id: str | int, message_id: int) -> dict[str, Any]:
        return self.request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def answer_callback_query(self, callback_query_id: str, *, text: str | None = None, show_alert: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        return self.request("answerCallbackQuery", payload)

    def set_my_description(self, description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"description": description}
        if language_code:
            payload["language_code"] = language_code
        return self.request("setMyDescription", payload)

    def set_my_short_description(self, short_description: str, *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"short_description": short_description}
        if language_code:
            payload["language_code"] = language_code
        return self.request("setMyShortDescription", payload)

    def set_my_commands(self, commands: list[dict[str, str]], *, language_code: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"commands": commands}
        if language_code:
            payload["language_code"] = language_code
        return self.request("setMyCommands", payload)

    def set_webhook(self, url: str, *, secret_token: str | None = None, drop_pending_updates: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": url,
            "drop_pending_updates": drop_pending_updates,
            "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return self.request("setWebhook", payload)

    def delete_webhook(self, *, drop_pending_updates: bool = False) -> dict[str, Any]:
        return self.request("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    def get_webhook_info(self) -> dict[str, Any]:
        return self.request("getWebhookInfo")

    def get_chat_member(self, *, chat_id: str | int, user_id: str | int) -> dict[str, Any]:
        return self.request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    def get_updates(self, *, offset: int | None = None, timeout: int = 30, allowed_updates: list[str] | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": allowed_updates or ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query"],
        }
        if offset is not None:
            payload["offset"] = offset
        response = self.request("getUpdates", payload)
        return response.get("result", [])


# Backwards-compatible name used by older code/imports.
TelegramBotClient = TelegramApiAdapter
