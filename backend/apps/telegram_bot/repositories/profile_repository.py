from __future__ import annotations

from typing import Any

from django.db.models import Q

from backend.apps.telegram_bot.models import TelegramProfile
from backend.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import (
    TelegramBotPostgresAdapter,
)


class TelegramProfileRepository:
    def __init__(self, adapter: TelegramBotPostgresAdapter | None = None):
        self.adapter = adapter or TelegramBotPostgresAdapter()

    def upsert_profile(
        self, *, provider: str, chat_id: str | int, user_data: dict[str, Any]
    ) -> TelegramProfile:
        return self.adapter.upsert_profile(
            provider=provider, chat_id=chat_id, user_data=user_data
        )

    def get_profile_language(self, *, provider: str, chat_id: str | int) -> str | None:
        return self.adapter.get_profile_language(provider=provider, chat_id=chat_id)

    def list_profiles_for_user(self, user):
        return self.adapter.list_profiles_for_user(user)

    def disconnect_profile_for_user(self, *, profile_id: int, user_id) -> bool:
        return self.adapter.disconnect_profile_for_user(
            profile_id=profile_id,
            user_id=user_id,
        )

    def list_admin_profiles(
        self,
        *,
        provider: str,
        exclude_chat_id: str | int | None = None,
        include_role_admin: bool = True,
    ):
        queryset = (
            TelegramProfile.objects
            .select_related("user", "user__role")
            .filter(
                messenger_provider=provider,
                is_verified=True,
                is_active=True,
                user__isnull=False,
                user__is_active=True,
            )
        )
        admin_filter = Q(user__is_staff=True) | Q(user__is_superuser=True)
        if include_role_admin:
            admin_filter |= Q(user__role__symbol="admin")
        queryset = queryset.filter(admin_filter)
        if exclude_chat_id is not None:
            queryset = queryset.exclude(chat_id=str(exclude_chat_id))
        return queryset.order_by("chat_id")

    @classmethod
    def upsert(
        cls, *, provider: str, chat_id: str | int, user_data: dict[str, Any]
    ) -> TelegramProfile:
        return cls().upsert_profile(
            provider=provider, chat_id=chat_id, user_data=user_data
        )

    @classmethod
    def language(cls, *, provider: str, chat_id: str | int) -> str | None:
        return cls().get_profile_language(provider=provider, chat_id=chat_id)
