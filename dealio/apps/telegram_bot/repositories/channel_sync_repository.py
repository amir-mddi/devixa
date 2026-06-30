from __future__ import annotations

from datetime import timedelta
from typing import Iterable

from django.utils import timezone

from dealio.apps.telegram_bot.models import ChannelSyncMessage


class ChannelSyncMessageRepository:
    @staticmethod
    def find_mappings(*, source_provider: str, source_chat_id: str, source_message_id: str) -> Iterable[ChannelSyncMessage]:
        return ChannelSyncMessage.objects.filter(
            source_provider=source_provider,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
        )

    @staticmethod
    def exists_as_target(*, target_provider: str, target_chat_id: str, target_message_id: str) -> bool:
        if not target_message_id:
            return False
        return ChannelSyncMessage.objects.filter(
            target_provider=target_provider,
            target_chat_id=target_chat_id,
            target_message_id=target_message_id,
        ).exists()

    @staticmethod
    def find_mappings_by_target(*, target_provider: str, target_chat_id: str, target_message_id: str) -> Iterable[ChannelSyncMessage]:
        if not target_message_id:
            return ChannelSyncMessage.objects.none()
        return ChannelSyncMessage.objects.filter(
            target_provider=target_provider,
            target_chat_id=target_chat_id,
            target_message_id=target_message_id,
        )


    @staticmethod
    def exists_as_recent_target_text(*, target_provider: str, target_chat_id: str, text_hash: str, seconds: int) -> bool:
        if not text_hash:
            return False

        threshold = timezone.now() - timedelta(seconds=seconds)
        return ChannelSyncMessage.objects.filter(
            target_provider=target_provider,
            target_chat_id=target_chat_id,
            text_hash=text_hash,
            updated_at__gte=threshold,
        ).exists()

    @staticmethod
    def upsert_mapping(
        *,
        source_provider: str,
        source_chat_id: str,
        source_message_id: str,
        target_provider: str,
        target_chat_id: str,
        target_message_id: str,
        text_hash: str,
        raw_response: dict,
        last_error: str = "",
    ) -> ChannelSyncMessage:
        mapping, _ = ChannelSyncMessage.objects.update_or_create(
            source_provider=source_provider,
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            target_provider=target_provider,
            target_chat_id=target_chat_id,
            defaults={
                "target_message_id": target_message_id,
                "text_hash": text_hash,
                "raw_response": raw_response,
                "last_error": last_error,
            },
        )
        return mapping



    @staticmethod
    def recent_mappings(*, limit: int = 20):
        return ChannelSyncMessage.objects.all().order_by("-created_at")[:limit]

    @staticmethod
    def recent_mappings_for_source(*, source_provider: str, source_chat_id: str = "", limit: int = 20):
        queryset = ChannelSyncMessage.objects.filter(source_provider=source_provider)
        if source_chat_id:
            queryset = queryset.filter(source_chat_id=source_chat_id)
        return queryset.order_by("-created_at")[:limit]

    @staticmethod
    def recent_mappings_for_target(*, target_provider: str, target_chat_id: str = "", limit: int = 20):
        queryset = ChannelSyncMessage.objects.filter(target_provider=target_provider)
        if target_chat_id:
            queryset = queryset.filter(target_chat_id=target_chat_id)
        return queryset.order_by("-created_at")[:limit]

    @staticmethod
    def mark_error(mapping: ChannelSyncMessage, error: str) -> None:
        mapping.last_error = error
        mapping.save(update_fields=["last_error", "updated_at"])

    @staticmethod
    def mark_deleted(mapping: ChannelSyncMessage) -> None:
        mapping.last_error = "Source message deleted; target message delete was requested."
        mapping.save(update_fields=["last_error", "updated_at"])
