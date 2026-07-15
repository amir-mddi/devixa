from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BotUpdateProcessDTO:
    provider: str
    update: dict[str, Any]
    update_id: str | int | None = None
