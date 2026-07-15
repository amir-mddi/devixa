"""Backward-compatible import path for the OAuth application facade."""

from backend.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from backend.apps.accounts.services.oauth_service import SocialOAuthService

__all__ = ["OAuthProviderError", "SocialOAuthService"]
