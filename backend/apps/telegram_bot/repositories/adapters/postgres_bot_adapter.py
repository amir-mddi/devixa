from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils.timezone import now

from backend.apps.accounts.models import Role
from backend.apps.telegram_bot.models import TelegramProfile, TelegramUpdateLog


class TelegramBotPostgresAdapter:
    """PostgreSQL/Django ORM adapter for Telegram/Bale/Rubika bot data."""

    @staticmethod
    def upsert_profile(
        *, provider: str, chat_id: str | int, user_data: dict[str, Any]
    ) -> TelegramProfile:
        defaults = {
            "messenger_provider": provider,
            "telegram_user_id": str(user_data.get("id") or ""),
            "username": user_data.get("username") or "",
            "first_name": user_data.get("first_name") or "",
            "last_name": user_data.get("last_name") or "",
            "language_code": user_data.get("language_code") or "",
            "is_active": True,
        }
        profile, created = TelegramProfile.objects.get_or_create(
            messenger_provider=provider,
            chat_id=str(chat_id),
            defaults=defaults,
        )
        if created:
            return profile

        changed_fields: list[str] = []
        for field, value in defaults.items():
            if getattr(profile, field) != value:
                setattr(profile, field, value)
                changed_fields.append(field)

        if changed_fields:
            changed_fields.append("updated_at")
            profile.save(update_fields=changed_fields)

        return profile

    @staticmethod
    def get_profile_language(*, provider: str, chat_id: str | int) -> str | None:
        profile = (
            TelegramProfile.objects.filter(
                messenger_provider=provider, chat_id=str(chat_id)
            )
            .only("bot_language")
            .first()
        )
        return profile.bot_language if profile else None

    @staticmethod
    def list_profiles_for_user(user):
        return TelegramProfile.objects.filter(user=user, is_active=True).order_by(
            "messenger_provider", "-updated_at"
        )

    @staticmethod
    def disconnect_profile_for_user(*, profile_id: int, user_id) -> bool:
        updated_count = TelegramProfile.objects.filter(
            id=profile_id,
            user_id=user_id,
            is_active=True,
        ).update(
            user=None,
            is_verified=False,
            updated_at=now(),
        )
        return updated_count == 1

    @staticmethod
    def get_or_create_update_log(
        *, provider: str, update_id: str | int, payload: dict[str, Any]
    ) -> tuple[TelegramUpdateLog, bool]:
        try:
            normalized_update_id = int(update_id)
        except (TypeError, ValueError):
            raise ValueError("Bot update id must be an integer.") from None
        if normalized_update_id < 0 or normalized_update_id > 9_223_372_036_854_775_807:
            raise ValueError("Bot update id is out of range.")

        return TelegramUpdateLog.objects.get_or_create(
            messenger_provider=str(provider or "")[:30],
            update_id=normalized_update_id,
            defaults={"payload": TelegramBotPostgresAdapter._summarize_update(payload)},
        )

    @staticmethod
    def _summarize_update(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {"event_type": "invalid"}
        known_event_keys = (
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "callback_query",
            "inline_query",
            "my_chat_member",
            "chat_member",
        )
        event_type = next(
            (key for key in known_event_keys if key in payload), "unknown"
        )
        return {
            "event_type": event_type,
            "top_level_keys": sorted(str(key)[:100] for key in payload.keys())[:50],
        }

    @staticmethod
    def mark_update_processed(update_log: TelegramUpdateLog) -> None:
        update_log.processed = True
        update_log.save(update_fields=["processed"])

    @staticmethod
    def mark_update_error(update_log: TelegramUpdateLog, error_text: str) -> None:
        update_log.error_text = str(error_text or "ProcessingError")[:120]
        update_log.save(update_fields=["error_text"])

    @staticmethod
    def delete_update_logs_before(cutoff: datetime) -> int:
        deleted_count, _ = TelegramUpdateLog.objects.filter(
            created_at__lt=cutoff
        ).delete()
        return deleted_count

    @staticmethod
    def ensure_default_user_role() -> None:
        if Role.objects.filter(symbol="user").exists():
            return

        role = Role.objects.filter(name__iexact="user").first()
        if role:
            role.symbol = "user"
            role.save(update_fields=["symbol", "updated_at"])
            return

        Role.objects.create(name="User", symbol="user")
