from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BotNotificationRecipientDTO:
    provider: str
    chat_id: str


@dataclass(frozen=True)
class BotNotificationDeliveryFailureDTO:
    chat_id: str
    error: str


@dataclass(frozen=True)
class BotNotificationDeliveryResultDTO:
    total_count: int
    success_count: int
    failed_count: int
    failures: list[BotNotificationDeliveryFailureDTO] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return self.failed_count > 0
