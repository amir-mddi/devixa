from __future__ import annotations

import os
from urllib.parse import urlparse
from typing import Any

from asgiref.sync import sync_to_async

from django.conf import settings
from django.core.exceptions import ValidationError

from backend.apps.common.utils.network_security import UnsafeOutboundUrlError, validate_public_https_url
from backend.apps.telegram_bot.dtos.bot_setting_dtos import (
    BotSettingDefinitionDTO,
    BotSettingPresentationDTO,
    BotSettingValueDTO,
)
from backend.apps.telegram_bot.enums.bot_setting_enums import BotSettingValueTypeEnum
from backend.apps.telegram_bot.repositories.bot_setting_repository import BotSettingRepository
from backend.apps.telegram_bot.repositories.adapters.bot_setting_env_file_adapter import BotSettingEnvFileAdapter
from backend.apps.telegram_bot.vo.bot_setting_vo import BotSecretMaskVO, BotSettingRegistryVO, BotSettingSourceVO


class BotSettingLogicRepository:
    """Runtime bot configuration use-cases.

    Database values are preferred. Env values are only fallback/bootstrap values.
    """

    def __init__(
        self,
        repository: BotSettingRepository | None = None,
        env_file_adapter: type[BotSettingEnvFileAdapter] = BotSettingEnvFileAdapter,
    ) -> None:
        self.repository = repository or BotSettingRepository()
        self.env_file_adapter = env_file_adapter

    async def list_all_async(self) -> list[dict[str, Any]]:
        return await sync_to_async(self.list_all, thread_sensitive=True)()

    async def provider_settings_async(self, provider: str) -> dict[str, Any]:
        return await sync_to_async(
            self.provider_settings,
            thread_sensitive=True,
        )(provider)

    async def update_provider_settings_async(
        self,
        *,
        provider: str,
        raw_settings: dict[str, Any],
        user=None,
        write_to_database: bool = True,
        write_to_env: bool = False,
    ) -> dict[str, Any]:
        return await sync_to_async(
            self.update_provider_settings,
            thread_sensitive=True,
        )(
            provider=provider,
            raw_settings=raw_settings,
            user=user,
            write_to_database=write_to_database,
            write_to_env=write_to_env,
        )

    def list_all(self) -> list[dict[str, Any]]:
        return [self.provider_settings(provider) for provider in BotSettingRegistryVO.providers()]

    def provider_settings(self, provider: str) -> dict[str, Any]:
        self._ensure_provider(provider)
        return {
            "provider": provider,
            "settings": [self.presentation(definition).__dict__ for definition in BotSettingRegistryVO.definitions(provider)],
        }

    def presentation(self, definition: BotSettingDefinitionDTO) -> BotSettingPresentationDTO:
        value_dto = self.get_definition_value(definition)
        display_value: Any = value_dto.value
        if definition.is_secret:
            display_value = BotSecretMaskVO.MASK if value_dto.is_configured else ""

        return BotSettingPresentationDTO(
            provider=definition.provider,
            key=definition.key,
            env_name=definition.env_name,
            label=definition.label,
            value_type=definition.value_type,
            value=display_value,
            source=value_dto.source,
            required=definition.required,
            is_secret=definition.is_secret,
            is_configured=value_dto.is_configured,
            choices=definition.choices,
            help_text=definition.help_text,
        )

    def get_definition_value(self, definition: BotSettingDefinitionDTO) -> BotSettingValueDTO:
        db_value = self.repository.get_value(
            provider=definition.provider,
            key=definition.key,
            is_secret=definition.is_secret,
        )
        if db_value is not None:
            return BotSettingValueDTO(
                provider=definition.provider,
                key=definition.key,
                value=db_value,
                source=BotSettingSourceVO.DATABASE,
                is_configured=bool(str(db_value).strip()),
            )

        env_value = os.environ.get(definition.env_name)
        if env_value is not None:
            return BotSettingValueDTO(
                provider=definition.provider,
                key=definition.key,
                value=str(env_value),
                source=BotSettingSourceVO.ENV,
                is_configured=bool(str(env_value).strip()),
            )

        if definition.default != "":
            return BotSettingValueDTO(
                provider=definition.provider,
                key=definition.key,
                value=definition.default,
                source=BotSettingSourceVO.DEFAULT,
                is_configured=bool(str(definition.default).strip()),
            )

        return BotSettingValueDTO(
            provider=definition.provider,
            key=definition.key,
            value="",
            source=BotSettingSourceVO.EMPTY,
            is_configured=False,
        )

    def get_value(self, *, provider: str, key: str, default: Any = "") -> str:
        definition = BotSettingRegistryVO.definition(provider, key)
        if not definition:
            return str(default or "")
        value = self.get_definition_value(definition).value
        if value == "" and default is not None:
            return str(default)
        return str(value)

    def get_value_for_env(self, env_name: str, default: Any = "") -> str:
        definition = BotSettingRegistryVO.definition_by_env(env_name)
        if not definition:
            return str(os.environ.get(env_name, default) or "")
        value = self.get_definition_value(definition).value
        if value == "" and default is not None:
            return str(default)
        return str(value)

    def update_provider_settings(
        self,
        *,
        provider: str,
        raw_settings: dict[str, Any],
        user=None,
        write_to_database: bool = True,
        write_to_env: bool = False,
    ) -> dict[str, Any]:
        self._ensure_provider(provider)
        if not isinstance(raw_settings, dict):
            raise ValidationError("settings must be an object.")
        if write_to_env:
            raise ValidationError("Writing bot settings to .env is disabled. Runtime settings are stored in the database only.")
        if not write_to_database:
            raise ValidationError("Runtime bot settings must be saved to the database.")

        updated_keys: list[str] = []

        for key, raw_value in raw_settings.items():
            definition = BotSettingRegistryVO.definition(provider, key)
            if not definition:
                raise ValidationError(f"Unsupported setting key for {provider}: {key}")

            # Masked secret means the UI sent the placeholder back unchanged.
            if definition.is_secret and raw_value == BotSecretMaskVO.MASK:
                continue

            value = self.normalize_value(definition=definition, raw_value=raw_value)

            if write_to_database:
                self.repository.set_value(
                    provider=provider,
                    key=key,
                    value=value,
                    is_secret=definition.is_secret,
                    user=user,
                )

            updated_keys.append(key)

        response = self.provider_settings(provider)
        response["updated_keys"] = updated_keys
        response["write_to_database"] = True
        response["write_to_env"] = False
        response["updated_env_names"] = []
        return response

    def delete_provider_setting(self, *, provider: str, key: str, user=None) -> dict[str, Any]:
        self._ensure_provider(provider)
        definition = BotSettingRegistryVO.definition(provider, key)
        if not definition:
            raise ValidationError(f"Unsupported setting key for {provider}: {key}")
        deleted = self.repository.delete_value(provider=provider, key=key, user=user)
        response = self.provider_settings(provider)
        response["deleted_key"] = key
        response["deleted"] = deleted
        return response

    @classmethod
    def normalize_value(cls, *, definition: BotSettingDefinitionDTO, raw_value: Any) -> str:
        value = "" if raw_value is None else str(raw_value).strip()
        value_type = definition.value_type

        if definition.required and value == "":
            raise ValidationError(f"{definition.key} is required.")

        if value == "":
            return ""

        if definition.is_secret:
            minimum = 32 if definition.key == "webhook_secret" else 16
            if len(value) < minimum:
                raise ValidationError(
                    f"{definition.key} must contain at least {minimum} characters."
                )

        if value_type == BotSettingValueTypeEnum.BOOL.value:
            lowered = value.lower()
            if lowered in {"1", "true", "yes", "on"}:
                return "true"
            if lowered in {"0", "false", "no", "off"}:
                return "false"
            raise ValidationError(f"{definition.key} must be a boolean value.")

        if value_type == BotSettingValueTypeEnum.INT.value:
            try:
                return str(int(value))
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"{definition.key} must be an integer.") from exc

        if value_type == BotSettingValueTypeEnum.FLOAT.value:
            try:
                return str(float(value))
            except (TypeError, ValueError) as exc:
                raise ValidationError(f"{definition.key} must be a number.") from exc

        if value_type == BotSettingValueTypeEnum.URL.value:
            parsed = urlparse(value)
            if parsed.username or parsed.password or not parsed.netloc:
                raise ValidationError(f"{definition.key} contains an invalid URL.")
            if definition.key == "proxy_url":
                if parsed.scheme not in {"http", "https"}:
                    raise ValidationError(f"{definition.key} must be a valid http/https URL.")
                return value
            if getattr(settings, "IS_PROD", False):
                try:
                    return validate_public_https_url(value, resolve_dns=False)
                except UnsafeOutboundUrlError as exc:
                    raise ValidationError(str(exc)) from exc
            if parsed.scheme not in {"http", "https"}:
                raise ValidationError(f"{definition.key} must be a valid http/https URL.")
            return value

        if value_type == BotSettingValueTypeEnum.CHOICE.value:
            if definition.choices and value not in definition.choices:
                raise ValidationError(f"{definition.key} must be one of: {', '.join(definition.choices)}")
            return value

        return value

    @staticmethod
    def _ensure_provider(provider: str) -> None:
        if provider not in BotSettingRegistryVO.providers():
            raise ValidationError(f"Unsupported bot settings provider: {provider}")


class BotRuntimeConfigProvider:
    """Convenience facade used by clients, services, commands and logic."""

    _logic: BotSettingLogicRepository | None = None

    @classmethod
    def logic(cls) -> BotSettingLogicRepository:
        if cls._logic is None:
            cls._logic = BotSettingLogicRepository()
        return cls._logic

    @classmethod
    def get(cls, provider: str, key: str, default: Any = "") -> str:
        return cls.logic().get_value(provider=provider, key=key, default=default)

    @classmethod
    def get_env(cls, env_name: str, default: Any = "") -> str:
        return cls.logic().get_value_for_env(env_name, default=default)

    @classmethod
    def get_int(cls, provider: str, key: str, default: int = 0) -> int:
        value = cls.get(provider, key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_float(cls, provider: str, key: str, default: float = 0.0) -> float:
        value = cls.get(provider, key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_bool(cls, provider: str, key: str, default: bool = False) -> bool:
        value = cls.get(provider, key, "true" if default else "false")
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
