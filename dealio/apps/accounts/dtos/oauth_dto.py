from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dealio.apps.accounts.entities.oauth_entity import OAuthProfileEntity


@dataclass(frozen=True, slots=True)
class OAuthAuthorizationRequestDTO:
    provider: str
    redirect_uri: str
    state: str


@dataclass(frozen=True, slots=True)
class OAuthCodeExchangeDTO:
    provider: str
    code: str
    redirect_uri: str


@dataclass(frozen=True, slots=True)
class OAuthAuthenticationResultDTO:
    user: Any
    profile: OAuthProfileEntity
