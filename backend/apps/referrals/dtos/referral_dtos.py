from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ReferralSummaryDTO:
    code: str
    invited_count: int
    recent_invitees: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class ReferralPublicSummaryDTO:
    code: str
    channel_username: str
    channel_invite_link: str = ""


@dataclass(frozen=True, slots=True)
class ReferralApplyDTO:
    invitee: Any
    code: str


@dataclass(frozen=True, slots=True)
class TelegramChannelMemberUpdateDTO:
    channel_username: str
    channel_chat_id: str
    telegram_user_id: int
    username: str
    first_name: str
    last_name: str
    invite_link: str
    old_status: str
    new_status: str
    occurred_at: datetime
    is_bot: bool = False


@dataclass(frozen=True, slots=True)
class ChannelReferralAdminSummaryDTO:
    channel_username: str
    invite_link: str
    invited_count: int
    current_member_count: int
    members: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class ReferralAdminSummaryDTO:
    code: str
    website_invited_count: int
    channel: ChannelReferralAdminSummaryDTO
