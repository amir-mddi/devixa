from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BotSupportTicketCreateDTO:
    provider: str
    profile_id: int | None
    user_id: UUID | None
    message: str
    subject: str = ""


@dataclass(frozen=True, slots=True)
class BotSupportReplyDTO:
    ticket_id: int
    admin_user_id: UUID
    message: str


@dataclass(frozen=True, slots=True)
class BotSupportCloseDTO:
    ticket_id: int
    admin_user_id: UUID
