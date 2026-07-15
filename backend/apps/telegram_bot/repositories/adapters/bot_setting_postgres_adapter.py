from __future__ import annotations

from backend.apps.common.utils.common_utils import CommonUtils

from django.db import OperationalError, ProgrammingError, transaction

from backend.apps.telegram_bot.models import BotRuntimeSetting

logger = CommonUtils.get_project_logger(__name__)


class BotSettingPostgresAdapter:
    """Persistence adapter for runtime bot settings."""

    @staticmethod
    def get_value(*, provider: str, key: str) -> str | None:
        try:
            setting = (
                BotRuntimeSetting.objects.filter(provider=provider, key=key, is_active=True)
                .only("value")
                .first()
            )
        except (OperationalError, ProgrammingError):
            # During first migrations the table may not exist yet. The config
            # provider will safely fall back to env/default values.
            return None
        except Exception:
            logger.exception("Failed to read bot runtime setting from database.")
            return None
        return setting.value if setting else None

    @staticmethod
    def get_values_by_provider(*, provider: str) -> dict[str, str]:
        try:
            rows = BotRuntimeSetting.objects.filter(provider=provider, is_active=True).only("key", "value")
        except (OperationalError, ProgrammingError):
            return {}
        except Exception:
            logger.exception("Failed to read bot runtime settings from database.")
            return {}
        return {row.key: row.value for row in rows}

    @staticmethod
    @transaction.atomic
    def upsert_value(*, provider: str, key: str, value: str, is_secret: bool, user=None) -> BotRuntimeSetting:
        setting, _ = BotRuntimeSetting.objects.select_for_update().update_or_create(
            provider=provider,
            key=key,
            defaults={
                "value": value or "",
                "is_secret": is_secret,
                "is_active": True,
                "updated_by": user if getattr(user, "is_authenticated", False) else None,
            },
        )
        return setting

    @staticmethod
    @transaction.atomic
    def delete_value(*, provider: str, key: str, user=None) -> bool:
        try:
            setting = BotRuntimeSetting.objects.select_for_update().filter(
                provider=provider,
                key=key,
                is_active=True,
            ).first()
        except (OperationalError, ProgrammingError):
            return False
        if not setting:
            return False
        setting.is_active = False
        setting.updated_by = user if getattr(user, "is_authenticated", False) else None
        setting.save(update_fields=["is_active", "updated_by", "updated_at"])
        return True
