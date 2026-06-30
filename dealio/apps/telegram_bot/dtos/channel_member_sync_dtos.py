from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelMemberCandidateDTO:
    user_id: int
    telegram_profile_id: int | None = None
    telegram_chat_id: str = ""
    telegram_user_id: str = ""
    bale_profile_id: int | None = None
    bale_chat_id: str = ""
    bale_user_id: str = ""


@dataclass(frozen=True)
class ChannelMemberCheckDTO:
    provider: str
    chat_id: str
    user_id: str
    is_member: bool
    status: str = ""
    error: str = ""


@dataclass(frozen=True)
class ChannelMemberSyncResultDTO:
    direction: str
    checked_count: int = 0
    invited_count: int = 0
    already_member_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
