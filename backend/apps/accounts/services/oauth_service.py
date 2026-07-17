from __future__ import annotations

from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import RefreshToken

from backend.apps.accounts.dtos.oauth_dto import OAuthCodeExchangeDTO
from backend.apps.accounts.enums.oauth_enums import OAuthProviderEnum
from backend.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from backend.apps.accounts.logic.oauth_logic import OAuthLoginLogic


class SocialOAuthService:
    """Async-first OAuth application facade.

    Browser session views may use the explicit ``sync_*`` compatibility methods.
    API controllers use the native async methods and never block the ASGI loop.
    """

    def __init__(self, *, logic: OAuthLoginLogic | None = None) -> None:
        self.logic = logic or OAuthLoginLogic()

    async def authenticate(self, *, provider: str, code: str, redirect_uri: str):
        return await self.logic.authenticate(
            OAuthCodeExchangeDTO(
                provider=provider,
                code=code,
                redirect_uri=redirect_uri,
            )
        )

    async def login(self, *, provider: str, code: str, redirect_uri: str) -> dict:
        result = await self.authenticate(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
        )
        return await sync_to_async(self._token_payload, thread_sensitive=True)(result.user)

    async def authenticate_with_google(self, *, code: str, redirect_uri: str):
        return await self.authenticate(
            provider=OAuthProviderEnum.GOOGLE.value,
            code=code,
            redirect_uri=redirect_uri,
        )

    async def authenticate_with_github(self, *, code: str, redirect_uri: str):
        return await self.authenticate(
            provider=OAuthProviderEnum.GITHUB.value,
            code=code,
            redirect_uri=redirect_uri,
        )

    async def login_with_google(self, *, code: str, redirect_uri: str) -> dict:
        return await self.login(
            provider=OAuthProviderEnum.GOOGLE.value,
            code=code,
            redirect_uri=redirect_uri,
        )

    async def login_with_github(self, *, code: str, redirect_uri: str) -> dict:
        return await self.login(
            provider=OAuthProviderEnum.GITHUB.value,
            code=code,
            redirect_uri=redirect_uri,
        )

    def sync_authenticate(self, *, provider: str, code: str, redirect_uri: str):
        return self.logic.sync_authenticate(
            OAuthCodeExchangeDTO(
                provider=provider,
                code=code,
                redirect_uri=redirect_uri,
            )
        )

    def sync_login(self, *, provider: str, code: str, redirect_uri: str) -> dict:
        result = self.sync_authenticate(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
        )
        return self._token_payload(result.user)

    @staticmethod
    def _token_payload(user) -> dict:
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return {
            "token": str(access),
            "refreshToken": str(refresh),
            "expirationTime": int(access["exp"]) * 1000,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": getattr(user.role, "symbol", None),
                "emailVerified": user.email_verified,
            },
        }


__all__ = ["OAuthProviderError", "SocialOAuthService"]
