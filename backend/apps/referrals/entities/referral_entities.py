from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReferralInviteEntity:
    username: str
    full_name: str
    registered_at: datetime | None
