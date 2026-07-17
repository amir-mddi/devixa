from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

from asgiref.sync import async_to_sync, sync_to_async
import httpx

from django.conf import settings

from backend.apps.accounts.dtos.oauth_dto import OAuthAuthorizationRequestDTO, OAuthCodeExchangeDTO
from backend.apps.accounts.entities.oauth_entity import OAuthProfileEntity
from backend.apps.accounts.enums.oauth_enums import OAuthProviderEnum
from backend.apps.accounts.exceptions.oauth_exceptions import OAuthProviderError
from backend.apps.accounts.vo.oauth_vo import (
    OAuthDefaultVO,
    OAuthEndpointVO,
    OAuthLogMessageVO,
    OAuthMessageVO,
    OAuthScopeVO,
    OAuthSettingNameVO,
)
from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class BaseOAuthProviderAdapter(ABC):
    provider: OAuthProviderEnum

    @abstractmethod
    def build_authorization_url(self, dto: OAuthAuthorizationRequestDTO) -> str:
        raise NotImplementedError

    @abstractmethod
    def exchange_code(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        """Synchronous compatibility entry point for browser views and tests."""
        raise NotImplementedError

    async def exchange_code_async(
        self,
        dto: OAuthCodeExchangeDTO,
    ) -> OAuthProfileEntity:
        """Async provider exchange contract.

        Third-party/custom adapters that only implement the legacy synchronous
        method remain supported without blocking the ASGI event loop. Native
        adapters override this method and use ``httpx.AsyncClient`` directly.
        """
        return await sync_to_async(self.exchange_code, thread_sensitive=False)(dto)

    @staticmethod
    def _required_setting(name: OAuthSettingNameVO) -> str:
        value = str(getattr(settings, name.value, "") or "").strip()
        if not value:
            raise OAuthProviderError(
                OAuthMessageVO.PROVIDER_NOT_CONFIGURED.value,
                status_code=500,
                log_message=OAuthLogMessageVO.MISSING_SETTING.value.format(setting_name=name.value),
            )
        return value

    async def _post_form(
        self,
        url: str,
        data: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Any:
        return await self._request_json(
            method="POST",
            url=url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                **(headers or {}),
            },
        )

    async def _get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return await self._request_json(
            method="GET",
            url=url,
            headers=headers,
        )

    async def _request_json(
        self,
        *,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        max_bytes = max(
            1024,
            int(getattr(settings, "OAUTH_MAX_RESPONSE_BYTES", OAuthDefaultVO.MAX_RESPONSE_BYTES.value)),
        )
        timeout = max(1, int(getattr(settings, "OAUTH_HTTP_TIMEOUT_SECONDS", 10)))
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "Devixa-OAuth/1.0",
            **(headers or {}),
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout),
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    method,
                    url,
                    data=data,
                    headers=request_headers,
                ) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("Content-Length")
                    try:
                        declared_size = int(content_length) if content_length else 0
                    except (TypeError, ValueError):
                        declared_size = 0
                    if declared_size > max_bytes:
                        raise OAuthProviderError(OAuthMessageVO.PROVIDER_OVERSIZED_RESPONSE.value)

                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise OAuthProviderError(OAuthMessageVO.PROVIDER_OVERSIZED_RESPONSE.value)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                OAuthLogMessageVO.PROVIDER_HTTP_ERROR.value.format(
                    provider=self.provider.value,
                    status=exc.response.status_code,
                )
            )
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_REJECTED.value) from exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
            logger.warning(
                OAuthLogMessageVO.PROVIDER_CONNECTION_ERROR.value.format(
                    provider=self.provider.value,
                    error=exc,
                )
            )
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_UNAVAILABLE.value) from exc

        try:
            return httpx.Response(200, content=bytes(body)).json()
        except ValueError as exc:
            logger.warning(
                OAuthLogMessageVO.PROVIDER_NON_JSON.value.format(provider=self.provider.value)
            )
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_INVALID_RESPONSE.value) from exc

    @staticmethod
    def _require_mapping(payload: Any) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping):
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_INVALID_RESPONSE.value)
        return payload

    @staticmethod
    def _is_verified(value: Any) -> bool:
        if value is True:
            return True
        return isinstance(value, str) and value.strip().lower() == "true"


class GoogleOAuthProviderAdapter(BaseOAuthProviderAdapter):
    provider = OAuthProviderEnum.GOOGLE

    def build_authorization_url(self, dto: OAuthAuthorizationRequestDTO) -> str:
        client_id = self._required_setting(OAuthSettingNameVO.GOOGLE_CLIENT_ID)
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": dto.redirect_uri,
                "response_type": "code",
                "scope": OAuthScopeVO.GOOGLE.value,
                "state": dto.state,
                "include_granted_scopes": "true",
                "prompt": "select_account",
            }
        )
        return f"{OAuthEndpointVO.GOOGLE_AUTHORIZE.value}?{query}"

    def exchange_code(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        return async_to_sync(self.exchange_code_async)(dto)

    async def exchange_code_async(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        token_data = await self._post_form(
            OAuthEndpointVO.GOOGLE_TOKEN.value,
            {
                "code": dto.code,
                "client_id": self._required_setting(OAuthSettingNameVO.GOOGLE_CLIENT_ID),
                "client_secret": self._required_setting(OAuthSettingNameVO.GOOGLE_CLIENT_SECRET),
                "redirect_uri": dto.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = self._require_mapping(token_data)
        access_token = str(token_data.get("access_token") or "").strip()
        if not access_token:
            raise OAuthProviderError(OAuthMessageVO.MISSING_ACCESS_TOKEN.value)

        userinfo = await self._get_json(
            OAuthEndpointVO.GOOGLE_USERINFO.value,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = self._require_mapping(userinfo)
        email = str(userinfo.get("email") or "").strip().lower()
        return OAuthProfileEntity(
            provider=self.provider.value,
            provider_user_id=str(userinfo.get("sub") or "").strip(),
            email=email,
            email_verified=self._is_verified(userinfo.get("email_verified")),
            username_hint=email.partition("@")[0],
            first_name=str(userinfo.get("given_name") or "").strip(),
            last_name=str(userinfo.get("family_name") or "").strip(),
            raw=dict(userinfo),
        )


class GitHubOAuthProviderAdapter(BaseOAuthProviderAdapter):
    provider = OAuthProviderEnum.GITHUB

    def build_authorization_url(self, dto: OAuthAuthorizationRequestDTO) -> str:
        client_id = self._required_setting(OAuthSettingNameVO.GITHUB_CLIENT_ID)
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": dto.redirect_uri,
                "scope": OAuthScopeVO.GITHUB.value,
                "state": dto.state,
                "allow_signup": "false",
            }
        )
        return f"{OAuthEndpointVO.GITHUB_AUTHORIZE.value}?{query}"

    def exchange_code(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        return async_to_sync(self.exchange_code_async)(dto)

    async def exchange_code_async(self, dto: OAuthCodeExchangeDTO) -> OAuthProfileEntity:
        token_data = await self._post_form(
            OAuthEndpointVO.GITHUB_TOKEN.value,
            {
                "code": dto.code,
                "client_id": self._required_setting(OAuthSettingNameVO.GITHUB_CLIENT_ID),
                "client_secret": self._required_setting(OAuthSettingNameVO.GITHUB_CLIENT_SECRET),
                "redirect_uri": dto.redirect_uri,
            },
        )
        token_data = self._require_mapping(token_data)
        access_token = str(token_data.get("access_token") or "").strip()
        if not access_token:
            raise OAuthProviderError(OAuthMessageVO.MISSING_ACCESS_TOKEN.value)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        github_user = await self._get_json(OAuthEndpointVO.GITHUB_USER.value, headers=headers)
        emails = await self._get_json(OAuthEndpointVO.GITHUB_EMAILS.value, headers=headers)
        github_user = self._require_mapping(github_user)
        if not isinstance(emails, list):
            raise OAuthProviderError(OAuthMessageVO.PROVIDER_INVALID_RESPONSE.value)

        primary_email = next(
            (
                item
                for item in emails
                if isinstance(item, dict)
                and self._is_verified(item.get("primary"))
                and self._is_verified(item.get("verified"))
                and item.get("email")
            ),
            None,
        )
        if not primary_email:
            raise OAuthProviderError(OAuthMessageVO.GITHUB_EMAIL_REQUIRED.value)

        email = str(primary_email["email"]).strip().lower()
        first_name, last_name = self._split_name(str(github_user.get("name") or ""))
        return OAuthProfileEntity(
            provider=self.provider.value,
            provider_user_id=str(github_user.get("id") or "").strip(),
            email=email,
            email_verified=True,
            username_hint=str(github_user.get("login") or email.partition("@")[0]).strip(),
            first_name=first_name,
            last_name=last_name,
            raw=dict(github_user),
        )

    @staticmethod
    def _split_name(full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)
        return (parts[0], parts[1] if len(parts) > 1 else "") if parts else ("", "")
