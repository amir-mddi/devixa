from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings

from backend.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)

from backend.apps.telegram_bot.dtos.channel_sync_dtos import ChannelMediaDTO, ChannelPostDTO
from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from backend.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from backend.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider


@dataclass(frozen=True)
class DownloadedChannelMedia:
    content: bytes
    filename: str
    mime_type: str


class ChannelSyncMessengerAdapter:
    """Provider API boundary for channel sync.

    Logic passes normalized ChannelPostDTO objects here. This adapter owns provider
    differences: API clients, file resolution, server-side media download/upload,
    edit, replace, and delete.
    """



    async def asend_post(
        self,
        *,
        provider: str,
        chat_id: str,
        post: ChannelPostDTO,
    ) -> dict[str, Any]:
        return await sync_to_async(
            self.send_post,
            thread_sensitive=True,
        )(provider=provider, chat_id=chat_id, post=post)

    async def aedit_post(
        self,
        *,
        provider: str,
        chat_id: str,
        message_id: str,
        post: ChannelPostDTO,
    ) -> dict[str, Any]:
        return await sync_to_async(
            self.edit_post,
            thread_sensitive=True,
        )(
            provider=provider,
            chat_id=chat_id,
            message_id=message_id,
            post=post,
        )

    async def adelete_text(
        self,
        *,
        provider: str,
        chat_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        return await sync_to_async(
            self.delete_text,
            thread_sensitive=True,
        )(provider=provider, chat_id=chat_id, message_id=message_id)

    def send_post(self, *, provider: str, chat_id: str, post: ChannelPostDTO) -> dict[str, Any]:
        if post.has_media and post.media:
            return self.send_media(provider=provider, chat_id=chat_id, media=post.media, caption=post.text)
        return self.send_text(provider=provider, chat_id=chat_id, text=post.text)

    def send_text(self, *, provider: str, chat_id: str, text: str) -> dict[str, Any]:
        client = self._client(provider)
        return client.send_message(chat_id, text)

    def send_media(
        self,
        *,
        provider: str,
        chat_id: str,
        media: ChannelMediaDTO,
        caption: str = "",
    ) -> dict[str, Any]:
        client = self._client(provider)
        normalized_type = self._normalized_media_type(media.media_type)

        downloaded = self._download_media(media)
        if downloaded:
            file_sender_name = self._file_sender_name(normalized_type)
            file_sender = getattr(client, file_sender_name, None)
            if callable(file_sender):
                return file_sender(
                    chat_id,
                    downloaded.content,
                    filename=downloaded.filename,
                    caption=caption,
                    mime_type=downloaded.mime_type,
                )

        # If provider can fetch the URL directly, this is the second best path.
        media_ref = media.file_url or media.file_id
        if normalized_type == "photo" and hasattr(client, "send_photo"):
            return client.send_photo(chat_id, media_ref, caption=caption)

        if normalized_type == "sticker" and hasattr(client, "send_sticker"):
            return client.send_sticker(chat_id, media_ref)

        if normalized_type in {"video", "animation"} and hasattr(client, "send_video"):
            return client.send_video(chat_id, media_ref, caption=caption)

        if hasattr(client, "send_document"):
            return client.send_document(chat_id, media_ref, caption=caption)

        # Safe fallback for providers with no media upload support.
        text = caption.strip()
        if media_ref:
            text = f"{text}\n{media_ref}".strip()
        return client.send_message(chat_id, text or media_ref)

    def edit_post(self, *, provider: str, chat_id: str, message_id: str, post: ChannelPostDTO) -> dict[str, Any]:
        if post.has_media and post.media:
            response = self.edit_media(provider=provider, chat_id=chat_id, message_id=message_id, media=post.media, caption=post.text)
            if response:
                return response

            if hasattr(self._client(provider), "edit_message_caption"):
                return self.edit_caption(provider=provider, chat_id=chat_id, message_id=message_id, caption=post.text)

        return self.edit_text(provider=provider, chat_id=chat_id, message_id=message_id, text=post.text)

    def edit_media(
        self,
        *,
        provider: str,
        chat_id: str,
        message_id: str,
        media: ChannelMediaDTO,
        caption: str = "",
    ) -> dict[str, Any] | None:
        client = self._client(provider)
        editor = getattr(client, "edit_message_media_file", None)
        if not callable(editor):
            return None

        downloaded = self._download_media(media)
        if not downloaded:
            return None

        return editor(
            chat_id,
            message_id,
            self._normalized_media_type(media.media_type),
            downloaded.content,
            filename=downloaded.filename,
            caption=caption,
            mime_type=downloaded.mime_type,
        )

    def edit_text(self, *, provider: str, chat_id: str, message_id: str, text: str) -> dict[str, Any]:
        client = self._client(provider)
        return client.edit_message_text(chat_id, message_id, text)

    def edit_caption(self, *, provider: str, chat_id: str, message_id: str, caption: str) -> dict[str, Any]:
        client = self._client(provider)
        if hasattr(client, "edit_message_caption"):
            return client.edit_message_caption(chat_id, message_id, caption)
        return client.edit_message_text(chat_id, message_id, caption)

    def delete_text(self, *, provider: str, chat_id: str, message_id: str) -> dict[str, Any]:
        client = self._client(provider)
        return client.delete_message(chat_id, message_id)

    def resolve_file_url(self, *, provider: str, file_id: str) -> str:
        if not file_id:
            return ""
        client = self._client(provider)
        if hasattr(client, "get_file_url"):
            return client.get_file_url(file_id)
        return ""

    @staticmethod
    def extract_message_id(response: dict[str, Any]) -> str:
        result = response.get("result") if isinstance(response, dict) else None
        if isinstance(result, dict):
            message_id = result.get("message_id") or result.get("messageId")
            if message_id is not None:
                return str(message_id)

        data = response.get("data") if isinstance(response, dict) else None
        if isinstance(data, dict):
            message_id = data.get("message_id") or data.get("new_message_id")
            if message_id is not None:
                return str(message_id)

        return ""

    @staticmethod
    def max_download_bytes() -> int:
        return BotRuntimeConfigProvider.get_int(
            BotSettingProviderEnum.CHANNEL_SYNC.value,
            "max_media_bytes",
            20 * 1024 * 1024,
        )

    async def _adownload_media(
        self,
        media: ChannelMediaDTO,
    ) -> DownloadedChannelMedia | None:
        url = media.file_url
        if not url:
            return None

        try:
            safe_url = await sync_to_async(
                validate_public_https_url,
                thread_sensitive=False,
            )(
                url,
                allowed_hosts=await sync_to_async(
                    self._allowed_media_hosts,
                    thread_sensitive=True,
                )(),
                resolve_dns=True,
            )
        except UnsafeOutboundUrlError as exc:
            raise RuntimeError(
                "Channel sync media URL is not allowed."
            ) from exc

        max_download_bytes = await sync_to_async(
            self.max_download_bytes,
            thread_sensitive=True,
        )()
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=60.0,
                    write=60.0,
                    pool=5.0,
                ),
                follow_redirects=False,
                trust_env=False,
            ) as client:
                async with client.stream("GET", safe_url) as response:
                    if 300 <= response.status_code < 400:
                        raise RuntimeError(
                            "Channel sync media redirects are not allowed."
                        )
                    response.raise_for_status()

                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        try:
                            if int(content_length) > max_download_bytes:
                                raise RuntimeError(
                                    "Channel sync media is larger than "
                                    f"{max_download_bytes} bytes."
                                )
                        except ValueError:
                            pass

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes(
                        chunk_size=1024 * 64
                    ):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > max_download_bytes:
                            raise RuntimeError(
                                "Channel sync media is larger than "
                                f"{max_download_bytes} bytes."
                            )
                        chunks.append(chunk)

                    content = b"".join(chunks)
                    content_type = (
                        response.headers.get("Content-Type", "")
                        .split(";", 1)[0]
                        .strip()
                    )
        except RuntimeError:
            raise
        except httpx.HTTPError as exc:
            raise RuntimeError("Channel sync media download failed.") from exc

        mime_type = (
            media.mime_type
            or content_type
            or self._mime_type_for(media.media_type)
        )
        filename = self._safe_filename(
            media.file_name
            or self._filename_from_url(safe_url)
            or self._filename_for(media.media_type, mime_type)
        )
        return DownloadedChannelMedia(
            content=content,
            filename=filename,
            mime_type=mime_type,
        )

    def _download_media(
        self,
        media: ChannelMediaDTO,
    ) -> DownloadedChannelMedia | None:
        return async_to_sync(self._adownload_media)(media)

    @staticmethod
    def _allowed_media_hosts() -> tuple[str, ...]:
        hosts = {"api.telegram.org"}
        for provider, key in (
            (BotSettingProviderEnum.BALE.value, "bot_base_url"),
            (BotSettingProviderEnum.RUBIKA.value, "bot_base_url"),
        ):
            configured = BotRuntimeConfigProvider.get(provider, key)
            parsed = urlparse(configured or "")
            if parsed.hostname:
                hosts.add(parsed.hostname)
        hosts.update(
            item.strip().lower()
            for item in getattr(settings, "CHANNEL_SYNC_ALLOWED_MEDIA_HOSTS", [])
            if item.strip()
        )
        return tuple(sorted(hosts))

    @staticmethod
    def _safe_filename(filename: str) -> str:
        normalized = os.path.basename(str(filename or "")).replace("\x00", "")
        normalized = "".join(ch for ch in normalized if ch.isalnum() or ch in "._-")
        return (normalized[:180] or "channel-sync-media.bin")

    @staticmethod
    def _filename_from_url(url: str) -> str:
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        return name if "." in name else ""

    @staticmethod
    def _filename_for(media_type: str, mime_type: str) -> str:
        extension = mimetypes.guess_extension(mime_type or "") or ""
        normalized = ChannelSyncMessengerAdapter._normalized_media_type(media_type)
        if not extension:
            extension_by_type = {
                "photo": ".jpg",
                "video": ".mp4",
                "animation": ".mp4",
                "sticker": ".webp",
                "audio": ".mp3",
                "voice": ".ogg",
                "document": ".bin",
            }
            extension = extension_by_type.get(normalized, ".bin")
        return f"channel_sync_{normalized}{extension}"

    @staticmethod
    def _mime_type_for(media_type: str) -> str:
        normalized = ChannelSyncMessengerAdapter._normalized_media_type(media_type)
        return {
            "photo": "image/jpeg",
            "video": "video/mp4",
            "animation": "video/mp4",
            "sticker": "image/webp",
            "audio": "audio/mpeg",
            "voice": "audio/ogg",
            "document": "application/octet-stream",
        }.get(normalized, "application/octet-stream")

    @staticmethod
    def _normalized_media_type(media_type: str) -> str:
        normalized = (media_type or "document").lower()
        if normalized in {"photo", "image"}:
            return "photo"
        if normalized in {"video", "video_note"}:
            return "video"
        if normalized in {"animation", "gif"}:
            return "animation"
        if normalized in {"sticker"}:
            return "sticker"
        if normalized in {"audio", "voice"}:
            return "audio"
        return "document"

    @classmethod
    def _file_sender_name(cls, media_type: str) -> str:
        normalized = cls._normalized_media_type(media_type)
        if normalized == "photo":
            return "send_photo_file"
        if normalized == "video":
            return "send_video_file"
        if normalized == "animation":
            return "send_animation_file"
        if normalized == "sticker":
            return "send_sticker_file"
        return "send_document_file"

    @staticmethod
    def _client(provider: str):
        if provider == MessengerProviderEnum.TELEGRAM.value:
            from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient

            return TelegramBotClient()

        if provider == MessengerProviderEnum.BALE.value:
            from backend.apps.telegram_bot.bale_services import BaleBotClient

            return BaleBotClient()

        if provider == MessengerProviderEnum.RUBIKA.value:
            from backend.apps.telegram_bot.rubika_services import RubikaBotClient

            return RubikaBotClient()

        raise RuntimeError(f"Unsupported channel sync provider: {provider}")
