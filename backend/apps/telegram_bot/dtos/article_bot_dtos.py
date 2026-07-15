from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ArticleBotButtonDTO:
    text: str
    callback_data: str


@dataclass(frozen=True, slots=True)
class ArticleBotScreenDTO:
    text: str
    rows: Sequence[Sequence[ArticleBotButtonDTO]] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ArticleBotHandleResultDTO:
    handled: bool
    screen: ArticleBotScreenDTO | None = None
