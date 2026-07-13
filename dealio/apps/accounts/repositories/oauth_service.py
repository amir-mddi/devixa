"""Backward-compatible import path for the OAuth application facade."""

from dealio.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from dealio.apps.accounts.services.oauth_service import SocialOAuthService

__all__ = ["OAuthProviderError", "SocialOAuthService"]
