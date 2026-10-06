from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LMSBotScreenDTO:
    text: str
    keyboard: tuple[tuple[dict[str, Any], ...], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ReferralBotScreenDTO:
    text: str
    keyboard: tuple[tuple[dict[str, Any], ...], ...] = field(default_factory=tuple)
