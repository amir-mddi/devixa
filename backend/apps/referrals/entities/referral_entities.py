from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReferralInviteEntity:
    username: str
    full_name: str
    registered_at: datetime | None


@dataclass(frozen=True, slots=True)
class TelegramChannelReferralLinkEntity:
    channel_username: str
    invite_link: str


@dataclass(frozen=True, slots=True)
class TelegramChannelReferralMemberEntity:
    telegram_user_id: int
    username: str
    full_name: str
    first_joined_at: datetime | None
    last_joined_at: datetime | None
    left_at: datetime | None
    is_current_member: bool
