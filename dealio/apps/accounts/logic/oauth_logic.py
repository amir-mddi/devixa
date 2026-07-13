from __future__ import annotations

from collections.abc import Mapping

from django.conf import settings
from django.db import transaction

from dealio.apps.accounts.adapters.oauth_provider_adapter import (
    BaseOAuthProviderAdapter,
    GitHubOAuthProviderAdapter,
    GoogleOAuthProviderAdapter,
)
from dealio.apps.accounts.dtos.oauth_dto import (
    OAuthAuthenticationResultDTO,
    OAuthAuthorizationRequestDTO,
    OAuthCodeExchangeDTO,
)
from dealio.apps.accounts.enums.oauth_enums import OAuthProviderEnum
from dealio.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from dealio.apps.accounts.repositories.oauth_repository import OAuthAccountRepository
from dealio.apps.accounts.vo.oauth_vo import OAuthMessageVO


class OAuthLoginLogic:
    def __init__(
        self,
        *,
        account_repository: OAuthAccountRepository | None = None,
        provider_adapters: Mapping[str, BaseOAuthProviderAdapter] | None = None,
    ) -> None:
        self.account_repository = account_repository or OAuthAccountRepository()
        self.provider_adapters = dict(
            provider_adapters
            or {
                OAuthProviderEnum.GOOGLE.value: GoogleOAuthProviderAdapter(),
                OAuthProviderEnum.GITHUB.value: GitHubOAuthProviderAdapter(),
            }
        )

    def build_authorization_url(self, dto: OAuthAuthorizationRequestDTO) -> str:
        self.validate_redirect_uri(dto.redirect_uri)
        return self._provider(dto.provider).build_authorization_url(dto)

    def authenticate(self, dto: OAuthCodeExchangeDTO) -> OAuthAuthenticationResultDTO:
        self.validate_redirect_uri(dto.redirect_uri)
        profile = self._provider(dto.provider).exchange_code(dto)
        self._validate_profile(profile)

        with transaction.atomic():
            user = self.account_repository.get_user_by_email(profile.email)
            if not user:
                raise OAuthProviderError(OAuthMessageVO.ACCOUNT_NOT_REGISTERED.value)
            self._assert_user_active(user)
            self.account_repository.link_or_refresh(user=user, profile=profile)

        return OAuthAuthenticationResultDTO(user=user, profile=profile)

    @staticmethod
    def validate_redirect_uri(redirect_uri: str) -> None:
        normalized = str(redirect_uri or "").strip()
        allowed = [
            str(item).strip()
            for item in getattr(settings, "OAUTH_ALLOWED_REDIRECT_URIS", [])
            if str(item).strip()
        ]
        if not allowed:
            raise OAuthProviderError(
                OAuthMessageVO.REDIRECT_ALLOWLIST_MISSING.value,
                status_code=500,
            )
        if normalized not in allowed:
            raise OAuthProviderError(OAuthMessageVO.REDIRECT_NOT_ALLOWED.value)

    def _provider(self, provider: str) -> BaseOAuthProviderAdapter:
        adapter = self.provider_adapters.get(str(provider))
        if not adapter:
            raise OAuthProviderError(OAuthMessageVO.UNSUPPORTED_PROVIDER.value)
        return adapter

    @staticmethod
    def _validate_profile(profile) -> None:
        if not profile.provider_user_id:
            raise OAuthProviderError(OAuthMessageVO.MISSING_STABLE_ID.value)
        if not profile.email:
            raise OAuthProviderError(OAuthMessageVO.MISSING_EMAIL.value)
        if not profile.email_verified:
            raise OAuthProviderError(OAuthMessageVO.UNVERIFIED_EMAIL.value)

    @staticmethod
    def _assert_user_active(user) -> None:
        if not user.is_active or getattr(user, "is_deleted", False):
            raise OAuthProviderError(OAuthMessageVO.ACCOUNT_INACTIVE.value)
