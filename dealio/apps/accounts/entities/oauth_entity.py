from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class OAuthProfileEntity:
    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    username_hint: str
    first_name: str = ""
    last_name: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
