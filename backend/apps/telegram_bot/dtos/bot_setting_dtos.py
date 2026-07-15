from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BotSettingDefinitionDTO:
    provider: str
    key: str
    env_name: str
    label: str
    value_type: str
    required: bool = False
    default: str = ""
    is_secret: bool = False
    choices: tuple[str, ...] = field(default_factory=tuple)
    help_text: str = ""


@dataclass(frozen=True)
class BotSettingValueDTO:
    provider: str
    key: str
    value: str
    source: str
    is_configured: bool


@dataclass(frozen=True)
class BotSettingPresentationDTO:
    provider: str
    key: str
    env_name: str
    label: str
    value_type: str
    value: Any
    source: str
    required: bool
    is_secret: bool
    is_configured: bool
    choices: tuple[str, ...] = field(default_factory=tuple)
    help_text: str = ""
