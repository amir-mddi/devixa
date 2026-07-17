from __future__ import annotations

import json
import os
from typing import Any

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings

from backend.apps.telegram_bot.dtos.commerce_bot_dtos import BotDownloadedFileDTO

from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from backend.apps.telegram_bot.interfaces.bot_client_interface import BotClientInterface
from backend.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider
from backend.apps.telegram_bot.repositories.adapters.bot_http_transport import BotProviderHttpTransport


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

    async def _runtime_values(self) -> tuple[str, str]:
        return await sync_to_async(
            lambda: (self.token, self.proxy_url),
            thread_sensitive=True,
        )()

    async def arequest(
        self,
        method_name: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token, proxy_url = await self._runtime_values()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        body = await BotProviderHttpTransport.apost_json(
            url=f"https://api.telegram.org/bot{token}/{method_name}",
            method_name=method_name,
            payload=payload or {},
            timeout=(3.0, 15.0),
            proxies=proxies,
            provider_name="Telegram",
        )
        if body.get("ok") is not True:
            raise RuntimeError(f"Telegram API request failed in {method_name}.")
        return body

    def request(
        self,
        method_name: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return async_to_sync(self.arequest)(method_name, payload)

    async def arequest_multipart(
        self,
        method_name: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        token, proxy_url = await self._runtime_values()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        body = await BotProviderHttpTransport.apost_multipart(
            url=f"https://api.telegram.org/bot{token}/{method_name}",
            method_name=method_name,
            data=data or {},
            files=files or {},
            timeout=(5.0, 60.0),
            proxies=proxies,
            provider_name="Telegram",
        )
        if body.get("ok") is not True:
            raise RuntimeError(f"Telegram API request failed in {method_name}.")
        return body

    def request_multipart(
        self,
        method_name: str,
        *,
        data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        return async_to_sync(self.arequest_multipart)(
            method_name,
            data=data,
            files=files,
        )


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

    async def adownload_file(
        self,
        file_id: str,
        *,
        filename: str = "",
    ) -> BotDownloadedFileDTO:
        """Download a Telegram file without blocking the ASGI event loop."""
        token, proxy_url = await self._runtime_values()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

        body = await self.arequest("getFile", {"file_id": file_id})
        result = body.get("result") or {}
        file_path = str(result.get("file_path") or "").strip()
        path_parts = [part for part in file_path.split("/") if part]
        if (
            not file_path
            or file_path.startswith(("/", "\\"))
            or "://" in file_path
            or any(part in {".", ".."} for part in path_parts)
            or len(file_path) > 500
        ):
            raise RuntimeError("Telegram file metadata is unavailable.")

        max_bytes = int(
            getattr(settings, "PAYMENT_RECEIPT_MAX_BYTES", 5 * 1024 * 1024)
        )
        provider_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0),
                proxy=proxy_url or None,
                follow_redirects=False,
            ) as client:
                async with client.stream("GET", provider_url) as response:
                    if response.status_code != 200:
                        raise RuntimeError("Telegram file download failed.")
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        try:
                            if int(content_length) > max_bytes:
                                raise RuntimeError(
                                    "Telegram receipt file is too large."
                                )
                        except ValueError:
                            pass

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_bytes:
                            raise RuntimeError(
                                "Telegram receipt file is too large."
                            )
                        chunks.append(chunk)

                    safe_filename = os.path.basename(
                        filename or file_path
                    ).replace("\x00", "")[:180]
                    if not safe_filename:
                        safe_filename = "telegram-receipt.bin"
                    return BotDownloadedFileDTO(
                        content=b"".join(chunks),
                        filename=safe_filename,
                        content_type=(
                            response.headers.get("Content-Type", "")
                            or "application/octet-stream"
                        ).split(";", 1)[0],
                    )
        except RuntimeError:
            raise
        except httpx.HTTPError:
            raise RuntimeError("Telegram file download failed.") from None

    def download_file(
        self,
        file_id: str,
        *,
        filename: str = "",
    ) -> BotDownloadedFileDTO:
        return async_to_sync(self.adownload_file)(file_id, filename=filename)

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

    async def asend_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self.arequest("sendMessage", payload)

    def send_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        return async_to_sync(self.asend_message)(
            chat_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )

    async def aedit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self.arequest("editMessageText", payload)

    def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        return async_to_sync(self.aedit_message_text)(
            chat_id,
            message_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )

    async def adelete_message(
        self,
        chat_id: str | int,
        message_id: int,
    ) -> dict[str, Any]:
        return await self.arequest(
            "deleteMessage",
            {"chat_id": chat_id, "message_id": message_id},
        )

    def delete_message(
        self,
        chat_id: str | int,
        message_id: int,
    ) -> dict[str, Any]:
        return async_to_sync(self.adelete_message)(chat_id, message_id)

    async def aanswer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        if text:
            payload["text"] = text
        return await self.arequest("answerCallbackQuery", payload)

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        return async_to_sync(self.aanswer_callback_query)(
            callback_query_id,
            text=text,
            show_alert=show_alert,
        )

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

    async def adelete_webhook(
        self,
        *,
        drop_pending_updates: bool = False,
    ) -> dict[str, Any]:
        return await self.arequest(
            "deleteWebhook",
            {"drop_pending_updates": drop_pending_updates},
        )

    def delete_webhook(self, *, drop_pending_updates: bool = False) -> dict[str, Any]:
        return async_to_sync(self.adelete_webhook)(
            drop_pending_updates=drop_pending_updates
        )

    def get_webhook_info(self) -> dict[str, Any]:
        return self.request("getWebhookInfo")

    def get_chat_member(self, *, chat_id: str | int, user_id: str | int) -> dict[str, Any]:
        return self.request("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def aget_updates(
        self,
        *,
        offset: int | None = None,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": timeout,
            "allowed_updates": allowed_updates
            or [
                "message",
                "edited_message",
                "channel_post",
                "edited_channel_post",
                "callback_query",
            ],
        }
        if offset is not None:
            payload["offset"] = offset
        if limit is not None:
            payload["limit"] = limit
        response = await self.arequest("getUpdates", payload)
        return response.get("result", [])

    def get_updates(
        self,
        *,
        offset: int | None = None,
        timeout: int = 30,
        allowed_updates: list[str] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return async_to_sync(self.aget_updates)(
            offset=offset,
            timeout=timeout,
            allowed_updates=allowed_updates,
            limit=limit,
        )


# Backwards-compatible name used by older code/imports.
TelegramBotClient = TelegramApiAdapter
