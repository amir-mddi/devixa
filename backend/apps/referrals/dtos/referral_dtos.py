from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReferralSummaryDTO:
    code: str
    invited_count: int
    recent_invitees: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class ReferralApplyDTO:
    invitee: Any
    code: str
