from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from dealio.apps.telegram_bot.enums.profile_enums import (
    MessengerProfileDisconnectErrorEnum,
)


@dataclass(frozen=True, slots=True)
class DisconnectMessengerProfileDTO:
    profile_id: int
    user_id: UUID


@dataclass(frozen=True, slots=True)
class DisconnectMessengerProfileResultDTO:
    is_success: bool
    error_code: MessengerProfileDisconnectErrorEnum | None = None

    @classmethod
    def success(cls) -> "DisconnectMessengerProfileResultDTO":
        return cls(is_success=True)

    @classmethod
    def failed(
        cls,
        error_code: MessengerProfileDisconnectErrorEnum,
    ) -> "DisconnectMessengerProfileResultDTO":
        return cls(is_success=False, error_code=error_code)
