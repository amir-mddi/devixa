from __future__ import annotations

from dealio.apps.telegram_bot.dtos.profile_dtos import (
    DisconnectMessengerProfileDTO,
    DisconnectMessengerProfileResultDTO,
)
from dealio.apps.telegram_bot.enums.profile_enums import (
    MessengerProfileDisconnectErrorEnum,
)
from dealio.apps.telegram_bot.repositories.profile_repository import (
    TelegramProfileRepository,
)


class MessengerProfileLogic:
    def __init__(self, repository: TelegramProfileRepository | None = None):
        self.repository = repository or TelegramProfileRepository()

    def disconnect(
        self,
        dto: DisconnectMessengerProfileDTO,
    ) -> DisconnectMessengerProfileResultDTO:
        disconnected = self.repository.disconnect_profile_for_user(
            profile_id=dto.profile_id,
            user_id=dto.user_id,
        )
        if not disconnected:
            return DisconnectMessengerProfileResultDTO.failed(
                MessengerProfileDisconnectErrorEnum.PROFILE_NOT_FOUND
            )
        return DisconnectMessengerProfileResultDTO.success()
