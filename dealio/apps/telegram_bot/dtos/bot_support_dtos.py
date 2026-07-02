from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BotSupportTicketCreateDTO:
    provider: str
    profile_id: int
    user_id: int | None
    message: str
    subject: str = ""


@dataclass(frozen=True)
class BotSupportReplyDTO:
    ticket_id: int
    admin_user_id: int
    message: str


@dataclass(frozen=True)
class BotSupportCloseDTO:
    ticket_id: int
    admin_user_id: int
