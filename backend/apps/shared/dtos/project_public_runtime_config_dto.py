from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectPublicRuntimeConfigDTO:
    """Public contact and channel values whose runtime source is the environment."""

    contact_email: str = ""
    phone: str = ""
    telegram_url: str = ""
    bale_url: str = ""
    instagram_url: str = ""
    telegram_bot_url: str = ""
    bale_bot_url: str = ""
    rubika_bot_url: str = ""
