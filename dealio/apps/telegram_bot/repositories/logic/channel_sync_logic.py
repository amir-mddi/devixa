from __future__ import annotations

import hashlib
import html
from dataclasses import replace
import logging
import os
from typing import Any

from dealio.apps.telegram_bot.dtos.channel_sync_dtos import ChannelMediaDTO, ChannelPostDTO, ChannelSyncTargetDTO
from dealio.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from dealio.apps.telegram_bot.repositories.adapters.channel_sync_adapter import ChannelSyncMessengerAdapter
from dealio.apps.telegram_bot.repositories.channel_sync_repository import ChannelSyncMessageRepository
from dealio.apps.telegram_bot.vo.channel_sync_vo import ChannelSyncEnvVO

logger = logging.getLogger("dealio")


class ChannelSyncLogicRepository:
    """Mirrors channel messages between supported messengers.

    The mapping table stores every source message -> target message relation. That
    relation is used for future edit/delete events and prevents echo loops:
    if Telegram sends a message to Bale, the Bale copy may appear in Bale polling;
    it is ignored because it is either authored by the bot or already exists as a
    target mapping.
    """

    RECENT_TARGET_ECHO_SECONDS = 300

    def __init__(
        self,
        *,
        adapter: ChannelSyncMessengerAdapter | None = None,
        repository: ChannelSyncMessageRepository | None = None,
    ) -> None:
        self.adapter = adapter or ChannelSyncMessengerAdapter()
        self.repository = repository or ChannelSyncMessageRepository()

    @classmethod
    def is_enabled(cls) -> bool:
        return (os.environ.get(ChannelSyncEnvVO.ENABLED) or "").strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def source_chat_id_for(cls, provider: str) -> str:
        env_by_provider = {
            MessengerProviderEnum.TELEGRAM.value: ChannelSyncEnvVO.TELEGRAM_SOURCE_CHAT_ID,
            MessengerProviderEnum.BALE.value: ChannelSyncEnvVO.BALE_SOURCE_CHAT_ID,
        }
        env_name = env_by_provider.get(provider)
        if not env_name:
            return ""
        return (os.environ.get(env_name) or "").strip()

    @classmethod
    def telegram_source_chat_id(cls) -> str:
        return cls.source_chat_id_for(MessengerProviderEnum.TELEGRAM.value)

    @classmethod
    def bale_source_chat_id(cls) -> str:
        return cls.source_chat_id_for(MessengerProviderEnum.BALE.value)

    @classmethod
    def targets_for_source(cls, source_provider: str) -> list[ChannelSyncTargetDTO]:
        targets: list[ChannelSyncTargetDTO] = []

        if source_provider == MessengerProviderEnum.TELEGRAM.value:
            bale_chat_id = (os.environ.get(ChannelSyncEnvVO.BALE_TARGET_CHAT_ID) or "").strip()
            rubika_chat_id = (os.environ.get(ChannelSyncEnvVO.RUBIKA_TARGET_CHAT_ID) or "").strip()

            if bale_chat_id:
                targets.append(ChannelSyncTargetDTO(provider=MessengerProviderEnum.BALE.value, chat_id=bale_chat_id))
            if rubika_chat_id:
                targets.append(ChannelSyncTargetDTO(provider=MessengerProviderEnum.RUBIKA.value, chat_id=rubika_chat_id))

        if source_provider == MessengerProviderEnum.BALE.value:
            telegram_chat_id = (os.environ.get(ChannelSyncEnvVO.TELEGRAM_TARGET_CHAT_ID) or "").strip()
            if telegram_chat_id:
                targets.append(ChannelSyncTargetDTO(provider=MessengerProviderEnum.TELEGRAM.value, chat_id=telegram_chat_id))

        return targets

    @classmethod
    def targets(cls) -> list[ChannelSyncTargetDTO]:
        """Backward-compatible target list for Telegram source sync."""
        return cls.targets_for_source(MessengerProviderEnum.TELEGRAM.value)

    @classmethod
    def validate_configuration(cls, *, source_provider: str = MessengerProviderEnum.TELEGRAM.value) -> None:
        if not cls.is_enabled():
            return

        missing: list[str] = []
        source_env_by_provider = {
            MessengerProviderEnum.TELEGRAM.value: ChannelSyncEnvVO.TELEGRAM_SOURCE_CHAT_ID,
            MessengerProviderEnum.BALE.value: ChannelSyncEnvVO.BALE_SOURCE_CHAT_ID,
        }
        source_env = source_env_by_provider.get(source_provider)
        if source_env and not cls.source_chat_id_for(source_provider):
            missing.append(source_env)

        target_envs_by_provider = {
            MessengerProviderEnum.TELEGRAM.value: [ChannelSyncEnvVO.BALE_TARGET_CHAT_ID, ChannelSyncEnvVO.RUBIKA_TARGET_CHAT_ID],
            MessengerProviderEnum.BALE.value: [ChannelSyncEnvVO.TELEGRAM_TARGET_CHAT_ID],
        }
        if not cls.targets_for_source(source_provider):
            missing.extend(target_envs_by_provider.get(source_provider, []))

        if missing:
            raise RuntimeError(f"Channel sync is enabled but env is missing: {', '.join(missing)}")

    def handle_telegram_update(self, update: dict[str, Any]) -> None:
        channel_post = update.get("channel_post")
        if channel_post:
            self.handle_telegram_channel_post(channel_post, is_edit=False)
            return

        edited_channel_post = update.get("edited_channel_post")
        if edited_channel_post:
            self.handle_telegram_channel_post(edited_channel_post, is_edit=True)

    def handle_bale_update(self, update: dict[str, Any]) -> None:
        posts = self.bale_update_to_dtos(update)
        for post in posts:
            self.sync(post)

    def handle_telegram_channel_post(self, message: dict[str, Any], *, is_edit: bool) -> None:
        if self.is_bot_authored_message(message):
            logger.info("Ignored Telegram channel sync echo authored by bot.")
            return

        post = self.telegram_message_to_dto(message, is_edit=is_edit)
        if not post:
            return
        self.sync(post)

    def sync(self, post: ChannelPostDTO) -> None:
        if not self.is_enabled():
            return

        self.validate_configuration(source_provider=post.source_provider)

        expected_source_chat_id = self.source_chat_id_for(post.source_provider)
        if expected_source_chat_id and str(post.source_chat_id) != expected_source_chat_id:
            return

        if self._is_mirrored_target(post):
            logger.info(
                "Ignored mirrored channel sync echo: %s:%s:%s",
                post.source_provider,
                post.source_chat_id,
                post.source_message_id,
            )
            return

        if post.is_delete:
            self._delete_related_messages(post)
            return

        if not post.text and not post.has_media:
            return

        post = self._with_resolved_media_url(post)
        text_hash = self.post_hash(post)

        if post.is_edit:
            self._edit_related_messages(post, text_hash=text_hash)
            return

        self._send_targets(post, text_hash=text_hash)

    def _with_resolved_media_url(self, post: ChannelPostDTO) -> ChannelPostDTO:
        if not post.media or post.media.file_url or not post.media.file_id:
            return post

        try:
            file_url = self.adapter.resolve_file_url(provider=post.source_provider, file_id=post.media.file_id)
        except Exception as exc:
            logger.exception("Failed to resolve channel sync media URL from %s", post.source_provider)
            file_url = ""

        if not file_url:
            return post

        return replace(post, media=replace(post.media, file_url=file_url))

    def _is_mirrored_target(self, post: ChannelPostDTO) -> bool:
        if self.repository.exists_as_target(
            target_provider=post.source_provider,
            target_chat_id=post.source_chat_id,
            target_message_id=post.source_message_id,
        ):
            return True

        if not post.text and not post.has_media:
            return False

        return self.repository.exists_as_recent_target_text(
            target_provider=post.source_provider,
            target_chat_id=post.source_chat_id,
            text_hash=self.post_hash(post),
            seconds=self.RECENT_TARGET_ECHO_SECONDS,
        )

    def _send_targets(self, post: ChannelPostDTO, *, text_hash: str) -> None:
        for target in self.targets_for_source(post.source_provider):
            try:
                response = self.adapter.send_post(provider=target.provider, chat_id=target.chat_id, post=post)
                target_message_id = self.adapter.extract_message_id(response)
                self.repository.upsert_mapping(
                    source_provider=post.source_provider,
                    source_chat_id=post.source_chat_id,
                    source_message_id=post.source_message_id,
                    target_provider=target.provider,
                    target_chat_id=target.chat_id,
                    target_message_id=target_message_id,
                    text_hash=text_hash,
                    raw_response=response,
                )
            except Exception as exc:
                logger.exception("Failed to sync %s channel post to %s", post.source_provider, target.provider)
                self.repository.upsert_mapping(
                    source_provider=post.source_provider,
                    source_chat_id=post.source_chat_id,
                    source_message_id=post.source_message_id,
                    target_provider=target.provider,
                    target_chat_id=target.chat_id,
                    target_message_id="",
                    text_hash=text_hash,
                    raw_response={},
                    last_error=str(exc),
                )

    def _edit_related_messages(self, post: ChannelPostDTO, *, text_hash: str) -> None:
        direct_mappings = list(
            self.repository.find_mappings(
                source_provider=post.source_provider,
                source_chat_id=post.source_chat_id,
                source_message_id=post.source_message_id,
            )
        )

        # If user edits the mirrored target message, edit the original source message.
        reverse_mappings = list(
            self.repository.find_mappings_by_target(
                target_provider=post.source_provider,
                target_chat_id=post.source_chat_id,
                target_message_id=post.source_message_id,
            )
        )

        if not direct_mappings and not reverse_mappings:
            self._send_targets(post, text_hash=text_hash)
            return

        for mapping in direct_mappings:
            if not mapping.target_message_id:
                continue
            self._edit_mapping_target(mapping, post, text_hash=text_hash)

        for mapping in reverse_mappings:
            self._edit_reverse_mapping_source(mapping, post, text_hash=text_hash)

    def _edit_mapping_target(self, mapping, post: ChannelPostDTO, *, text_hash: str) -> None:
        try:
            response = self.adapter.edit_post(
                provider=mapping.target_provider,
                chat_id=mapping.target_chat_id,
                message_id=mapping.target_message_id,
                post=post,
            )
            mapping.text_hash = text_hash
            mapping.raw_response = response
            mapping.last_error = ""
            mapping.save(update_fields=["text_hash", "raw_response", "last_error", "updated_at"])
        except Exception as exc:
            if post.has_media:
                logger.info("Media edit failed on %s; replacing synced message instead.", mapping.target_provider)
                self._replace_mapping_message(
                    mapping=mapping,
                    provider=mapping.target_provider,
                    chat_id=mapping.target_chat_id,
                    message_id=mapping.target_message_id,
                    post=post,
                    text_hash=text_hash,
                    update_target=True,
                )
                return
            logger.exception("Failed to edit synced channel message on %s", mapping.target_provider)
            self.repository.mark_error(mapping, str(exc))

    def _edit_reverse_mapping_source(self, mapping, post: ChannelPostDTO, *, text_hash: str) -> None:
        try:
            response = self.adapter.edit_post(
                provider=mapping.source_provider,
                chat_id=mapping.source_chat_id,
                message_id=mapping.source_message_id,
                post=post,
            )
            mapping.text_hash = text_hash
            mapping.raw_response = response
            mapping.last_error = ""
            mapping.save(update_fields=["text_hash", "raw_response", "last_error", "updated_at"])
        except Exception as exc:
            if post.has_media:
                logger.info("Reverse media edit failed on %s; replacing source message instead.", mapping.source_provider)
                self._replace_mapping_message(
                    mapping=mapping,
                    provider=mapping.source_provider,
                    chat_id=mapping.source_chat_id,
                    message_id=mapping.source_message_id,
                    post=post,
                    text_hash=text_hash,
                    update_target=False,
                )
                return
            logger.exception("Failed to edit reverse synced channel message on %s", mapping.source_provider)
            self.repository.mark_error(mapping, str(exc))

    def _replace_mapping_message(
        self,
        *,
        mapping,
        provider: str,
        chat_id: str,
        message_id: str,
        post: ChannelPostDTO,
        text_hash: str,
        update_target: bool,
    ) -> None:
        try:
            try:
                self.adapter.delete_text(provider=provider, chat_id=chat_id, message_id=message_id)
            except Exception:
                logger.info("Old media message could not be deleted during replace on %s.", provider)

            response = self.adapter.send_post(provider=provider, chat_id=chat_id, post=post)
            new_message_id = self.adapter.extract_message_id(response)

            if update_target:
                mapping.target_message_id = new_message_id
            else:
                mapping.source_message_id = new_message_id

            mapping.text_hash = text_hash
            mapping.raw_response = response
            mapping.last_error = ""
            mapping.save(update_fields=["source_message_id", "target_message_id", "text_hash", "raw_response", "last_error", "updated_at"])
        except Exception as exc:
            logger.exception("Failed to replace synced channel media message on %s", provider)
            self.repository.mark_error(mapping, str(exc))

    def _delete_targets(self, post: ChannelPostDTO) -> None:
        # Backward-compatible name used by channel_sync_delete command.
        self._delete_related_messages(post)

    def _delete_related_messages(self, post: ChannelPostDTO) -> None:
        direct_mappings = list(
            self.repository.find_mappings(
                source_provider=post.source_provider,
                source_chat_id=post.source_chat_id,
                source_message_id=post.source_message_id,
            )
        )
        reverse_mappings = list(
            self.repository.find_mappings_by_target(
                target_provider=post.source_provider,
                target_chat_id=post.source_chat_id,
                target_message_id=post.source_message_id,
            )
        )

        for mapping in direct_mappings:
            if not mapping.target_message_id:
                continue
            self._delete_mapping_message(
                mapping=mapping,
                provider=mapping.target_provider,
                chat_id=mapping.target_chat_id,
                message_id=mapping.target_message_id,
            )

        for mapping in reverse_mappings:
            self._delete_mapping_message(
                mapping=mapping,
                provider=mapping.source_provider,
                chat_id=mapping.source_chat_id,
                message_id=mapping.source_message_id,
            )

    def _delete_mapping_message(self, *, mapping, provider: str, chat_id: str, message_id: str) -> None:
        try:
            self.adapter.delete_text(provider=provider, chat_id=chat_id, message_id=message_id)
            self.repository.mark_deleted(mapping)
        except Exception as exc:
            logger.exception("Failed to delete synced channel message on %s", provider)
            self.repository.mark_error(mapping, str(exc))

    @classmethod
    def delete_targets_for_source(cls, *, source_provider: str, source_chat_id: str, source_message_id: str) -> int:
        logic = cls()
        post = ChannelPostDTO(
            source_provider=source_provider,
            source_chat_id=str(source_chat_id),
            source_message_id=str(source_message_id),
            is_delete=True,
        )
        mappings = list(
            logic.repository.find_mappings(
                source_provider=post.source_provider,
                source_chat_id=post.source_chat_id,
                source_message_id=post.source_message_id,
            )
        )
        logic._delete_targets(post)
        return len(mappings)

    @classmethod
    def delete_related_for_target(cls, *, target_provider: str, target_chat_id: str, target_message_id: str) -> int:
        logic = cls()
        mappings = list(
            logic.repository.find_mappings_by_target(
                target_provider=target_provider,
                target_chat_id=str(target_chat_id),
                target_message_id=str(target_message_id),
            )
        )

        for mapping in mappings:
            logic._delete_mapping_message(
                mapping=mapping,
                provider=mapping.source_provider,
                chat_id=mapping.source_chat_id,
                message_id=mapping.source_message_id,
            )

        return len(mappings)

    @classmethod
    def delete_exact_message(cls, *, provider: str, chat_id: str, message_id: str) -> None:
        logic = cls()
        logic.adapter.delete_text(provider=provider, chat_id=str(chat_id), message_id=str(message_id))

    @classmethod
    def recent_mappings(cls, *, limit: int = 20):
        return cls().repository.recent_mappings(limit=limit)

    @classmethod
    def recent_mappings_for_source(cls, *, source_provider: str, source_chat_id: str = "", limit: int = 20):
        return cls().repository.recent_mappings_for_source(
            source_provider=source_provider,
            source_chat_id=str(source_chat_id or ""),
            limit=limit,
        )

    @classmethod
    def recent_mappings_for_target(cls, *, target_provider: str, target_chat_id: str = "", limit: int = 20):
        return cls().repository.recent_mappings_for_target(
            target_provider=target_provider,
            target_chat_id=str(target_chat_id or ""),
            limit=limit,
        )

    @classmethod
    def telegram_message_to_dto(cls, message: dict[str, Any], *, is_edit: bool) -> ChannelPostDTO | None:
        chat_id, message_id = cls.extract_message_identity(message)
        if chat_id is None or message_id is None:
            return None

        text = cls.extract_text(message)
        media = cls.extract_media(message)
        if not text and not media:
            return None

        return ChannelPostDTO(
            source_provider=MessengerProviderEnum.TELEGRAM.value,
            source_chat_id=str(chat_id),
            source_message_id=str(message_id),
            text=text,
            is_edit=is_edit,
            media=media,
        )

    @classmethod
    def bale_update_to_dto(cls, update: dict[str, Any]) -> ChannelPostDTO | None:
        posts = cls.bale_update_to_dtos(update)
        return posts[0] if posts else None

    @classmethod
    def bale_update_to_dtos(cls, update: dict[str, Any]) -> list[ChannelPostDTO]:
        delete_posts = cls.bale_delete_update_to_dtos(update)
        if delete_posts:
            return delete_posts

        message = cls.first_dict(update, ["edited_channel_post", "edited_message"])
        if message:
            post = cls.bale_message_to_dto(message, is_edit=True, is_delete=False)
            return [post] if post else []

        if cls.update_type_contains(update, "edit"):
            post = cls.bale_message_to_dto(update, is_edit=True, is_delete=False)
            return [post] if post else []

        message = cls.first_dict(update, ["channel_post", "message", "new_message"])
        if message:
            post = cls.bale_message_to_dto(message, is_edit=False, is_delete=False)
            return [post] if post else []

        if cls.update_type_contains(update, "message"):
            post = cls.bale_message_to_dto(update, is_edit=False, is_delete=False)
            return [post] if post else []

        return []

    @classmethod
    def bale_delete_update_to_dtos(cls, update: dict[str, Any]) -> list[ChannelPostDTO]:
        message = cls.first_dict(
            update,
            ["deleted_channel_post", "deleted_message", "message_deleted", "channel_post_deleted", "delete_message"],
        )
        if message:
            post = cls.bale_message_to_dto(message, is_edit=False, is_delete=True)
            return [post] if post else []

        if not cls.update_type_contains(update, "delete"):
            return []

        chat_id = (
            update.get("chat_id")
            or update.get("chatId")
            or ((update.get("chat") or {}).get("id") if isinstance(update.get("chat"), dict) else None)
        )
        message_ids = (
            update.get("message_ids")
            or update.get("messageIds")
            or update.get("deleted_message_ids")
            or update.get("deletedMessageIds")
        )
        if message_ids and chat_id is not None:
            if not isinstance(message_ids, list):
                message_ids = [message_ids]
            return [
                ChannelPostDTO(
                    source_provider=MessengerProviderEnum.BALE.value,
                    source_chat_id=str(chat_id),
                    source_message_id=str(message_id),
                    is_delete=True,
                )
                for message_id in message_ids
                if message_id is not None
            ]

        post = cls.bale_message_to_dto(update, is_edit=False, is_delete=True)
        return [post] if post else []

    @classmethod
    def bale_message_to_dto(cls, message: dict[str, Any], *, is_edit: bool, is_delete: bool) -> ChannelPostDTO | None:
        if not is_delete and cls.is_bot_authored_message(message):
            logger.info("Ignored Bale channel sync echo authored by bot.")
            return None

        chat_id, message_id = cls.extract_message_identity(message)
        if chat_id is None or message_id is None:
            return None

        text = "" if is_delete else cls.extract_text(message)
        media = None if is_delete else cls.extract_media(message)
        if not is_delete and not text and not media:
            return None

        return ChannelPostDTO(
            source_provider=MessengerProviderEnum.BALE.value,
            source_chat_id=str(chat_id),
            source_message_id=str(message_id),
            text=text,
            is_edit=is_edit,
            is_delete=is_delete,
            media=media,
        )

    @staticmethod
    def update_type_contains(payload: dict[str, Any], needle: str) -> bool:
        update_type = str(payload.get("type") or payload.get("update_type") or payload.get("event") or "").lower()
        return needle.lower() in update_type

    @staticmethod
    def first_dict(payload: dict[str, Any], keys: list[str]) -> dict[str, Any] | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return None

    @classmethod
    def extract_message_identity(cls, message: dict[str, Any]) -> tuple[str | int | None, str | int | None]:
        nested = cls.first_dict(message, ["new_message", "message", "deleted_message"])
        chat = message.get("chat") or {}
        nested_chat = nested.get("chat") if isinstance(nested, dict) else {}
        if not isinstance(nested_chat, dict):
            nested_chat = {}

        chat_id = (
            message.get("chat_id")
            or message.get("chatId")
            or chat.get("id")
            or nested_chat.get("id")
            or (nested.get("chat_id") if isinstance(nested, dict) else None)
            or (nested.get("chatId") if isinstance(nested, dict) else None)
        )
        message_id = (
            message.get("message_id")
            or message.get("messageId")
            or message.get("deleted_message_id")
            or message.get("deletedMessageId")
            or message.get("id")
            or (nested.get("message_id") if isinstance(nested, dict) else None)
            or (nested.get("messageId") if isinstance(nested, dict) else None)
            or (nested.get("deleted_message_id") if isinstance(nested, dict) else None)
            or (nested.get("deletedMessageId") if isinstance(nested, dict) else None)
            or (nested.get("id") if isinstance(nested, dict) else None)
        )
        return chat_id, message_id

    @classmethod
    def extract_text(cls, message: dict[str, Any]) -> str:
        nested = cls.first_dict(message, ["new_message", "message"])
        text = (message.get("text") or message.get("caption") or "").strip()
        if not text and isinstance(nested, dict):
            text = (nested.get("text") or nested.get("caption") or "").strip()
        if not text:
            gift = message.get("gift") or message.get("unique_gift")
            if not gift and isinstance(nested, dict):
                gift = nested.get("gift") or nested.get("unique_gift")
            if isinstance(gift, dict):
                title = gift.get("title") or gift.get("name") or gift.get("emoji") or "Gift"
                return html.escape(f"🎁 {title}")

            sticker = message.get("sticker")
            if not sticker and isinstance(nested, dict):
                sticker = nested.get("sticker")
            if isinstance(sticker, dict) and sticker.get("emoji"):
                return html.escape(str(sticker.get("emoji")))

            return ""
        return html.escape(text)

    @classmethod
    def extract_media(cls, message: dict[str, Any]) -> ChannelMediaDTO | None:
        nested = cls.first_dict(message, ["new_message", "message"])
        candidates = [message]
        if isinstance(nested, dict):
            candidates.append(nested)

        for candidate in candidates:
            photo = candidate.get("photo")
            if isinstance(photo, list) and photo:
                best = max(photo, key=lambda item: item.get("file_size") or (item.get("width", 0) * item.get("height", 0)))
                file_id = str(best.get("file_id") or best.get("fileId") or best.get("url") or "")
                file_url = str(best.get("file_url") or best.get("url") or "")
                if file_id or file_url:
                    return ChannelMediaDTO(media_type="photo", file_id=file_id, file_url=file_url)
            if isinstance(photo, dict):
                file_id = str(photo.get("file_id") or photo.get("fileId") or "")
                file_url = str(photo.get("file_url") or photo.get("url") or "")
                if file_id or file_url:
                    return ChannelMediaDTO(media_type="photo", file_id=file_id, file_url=file_url)

            for media_type in ["video", "animation", "document", "sticker", "voice", "audio", "video_note"]:
                media = candidate.get(media_type)
                if not isinstance(media, dict):
                    continue
                file_id = str(media.get("file_id") or media.get("fileId") or media.get("id") or "")
                file_url = str(media.get("file_url") or media.get("url") or "")
                mime_type = str(media.get("mime_type") or media.get("mimeType") or "")
                file_name = str(media.get("file_name") or media.get("fileName") or "")
                if file_id or file_url:
                    normalized_media_type = "video" if media_type == "video_note" else media_type
                    return ChannelMediaDTO(
                        media_type=normalized_media_type,
                        file_id=file_id,
                        file_url=file_url,
                        mime_type=mime_type,
                        file_name=file_name,
                    )

            # Some providers expose a generic file/media object.
            generic = candidate.get("file") or candidate.get("media")
            if isinstance(generic, dict):
                file_id = str(generic.get("file_id") or generic.get("fileId") or generic.get("id") or "")
                file_url = str(generic.get("file_url") or generic.get("url") or "")
                media_type = str(generic.get("type") or generic.get("media_type") or "document")
                if file_id or file_url:
                    return ChannelMediaDTO(media_type=media_type, file_id=file_id, file_url=file_url)

        return None

    @classmethod
    def is_bot_authored_message(cls, message: dict[str, Any]) -> bool:
        nested = cls.first_dict(message, ["new_message", "message"])
        candidates = [message]
        if isinstance(nested, dict):
            candidates.append(nested)

        for candidate in candidates:
            from_obj = candidate.get("from") or candidate.get("sender") or {}
            if isinstance(from_obj, dict) and from_obj.get("is_bot") is True:
                return True

            sender_type = str(candidate.get("sender_type") or candidate.get("senderType") or "").lower()
            if sender_type == "bot":
                return True

        return False

    @classmethod
    def post_hash(cls, post: ChannelPostDTO) -> str:
        media_part = ""
        if post.media:
            media_part = f"{post.media.media_type}:{post.media.file_id}:{post.media.file_url}"
        return cls.text_hash(f"{post.text}|{media_part}")

    @staticmethod
    def text_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
