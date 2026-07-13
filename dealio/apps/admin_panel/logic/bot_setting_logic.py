from __future__ import annotations

from django.core.exceptions import ValidationError

from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import (
    BotSettingLogicRepository,
)
from dealio.apps.telegram_bot.vo.bot_setting_vo import BotSettingRegistryVO


class AdminBotSettingLogic:
    """Admin use cases for allow-listed runtime bot settings."""

    def __init__(self, setting_logic: BotSettingLogicRepository | None = None):
        self.setting_logic = setting_logic or BotSettingLogicRepository()

    @staticmethod
    def providers() -> tuple[str, ...]:
        return BotSettingRegistryVO.providers()

    def get_provider_settings(self, provider: str) -> dict:
        self._ensure_provider(provider)
        return self.setting_logic.provider_settings(provider)

    def update_provider_settings(self, *, actor, provider: str, values: dict) -> dict:
        self._ensure_provider(provider)
        return self.setting_logic.update_provider_settings(
            provider=provider,
            raw_settings=values,
            user=actor,
            write_to_database=True,
            write_to_env=False,
        )

    def delete_provider_setting(self, *, actor, provider: str, key: str) -> dict:
        self._ensure_provider(provider)
        return self.setting_logic.delete_provider_setting(
            provider=provider,
            key=key,
            user=actor,
        )

    def _ensure_provider(self, provider: str) -> None:
        if provider not in self.providers():
            raise ValidationError("پیام‌رسان یا بخش تنظیمات انتخاب‌شده معتبر نیست.")
