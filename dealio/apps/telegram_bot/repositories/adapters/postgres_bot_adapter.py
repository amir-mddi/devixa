from __future__ import annotations

from typing import Any

from dealio.apps.accounts.models import Role
from dealio.apps.telegram_bot.models import TelegramProfile, TelegramUpdateLog


class TelegramBotPostgresAdapter:
    """PostgreSQL/Django ORM adapter for Telegram/Bale/Rubika bot data."""

    @staticmethod
    def upsert_profile(*, provider: str, chat_id: str | int, user_data: dict[str, Any]) -> TelegramProfile:
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
            TelegramProfile.objects
            .filter(messenger_provider=provider, chat_id=str(chat_id))
            .only("bot_language")
            .first()
        )
        return profile.bot_language if profile else None

    @staticmethod
    def get_or_create_update_log(*, provider: str, update_id: str | int, payload: dict[str, Any]) -> tuple[TelegramUpdateLog, bool]:
        return TelegramUpdateLog.objects.get_or_create(
            messenger_provider=provider,
            update_id=str(update_id),
            defaults={"payload": payload},
        )

    @staticmethod
    def mark_update_processed(update_log: TelegramUpdateLog) -> None:
        update_log.processed = True
        update_log.save(update_fields=["processed"])

    @staticmethod
    def mark_update_error(update_log: TelegramUpdateLog, error_text: str) -> None:
        update_log.error_text = error_text
        update_log.save(update_fields=["error_text"])

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
