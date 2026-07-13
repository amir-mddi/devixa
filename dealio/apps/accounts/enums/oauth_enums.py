from __future__ import annotations

from enum import StrEnum


class OAuthProviderEnum(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"


class OAuthSessionKeyEnum(StrEnum):
    FLOW = "oauth_flow"
    STATE = "oauth_state"
    PROVIDER = "oauth_provider"
    CREATED_AT = "oauth_created_at"
    NEXT_URL = "oauth_next_url"
    REDIRECT_URI = "oauth_redirect_uri"
