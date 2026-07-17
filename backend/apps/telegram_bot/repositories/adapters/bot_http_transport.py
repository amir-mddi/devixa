from __future__ import annotations

import json
import re
from typing import Any

import httpx
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings

from backend.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)


class BotProviderTransportError(RuntimeError):
    pass


class BotProviderHttpTransport:
    """Bounded async HTTP transport for bot provider adapters.

    Synchronous wrappers remain only for legacy service edges. They execute the
    exact same async implementation, so no blocking ``requests`` calls remain in
    the provider transport.
    """

    _METHOD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,99}$")
    DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024

    @classmethod
    async def apost_json(
        cls,
        *,
        url: str,
        method_name: str,
        payload: dict[str, Any],
        timeout: tuple[float, float],
        proxies: dict[str, str] | None,
        provider_name: str,
    ) -> dict[str, Any]:
        return await cls._post(
            url=url,
            method_name=method_name,
            timeout=timeout,
            proxies=proxies,
            provider_name=provider_name,
            json_payload=payload,
        )

    @classmethod
    async def apost_multipart(
        cls,
        *,
        url: str,
        method_name: str,
        data: dict[str, Any],
        files: dict[str, tuple[str, bytes, str]],
        timeout: tuple[float, float],
        proxies: dict[str, str] | None,
        provider_name: str,
    ) -> dict[str, Any]:
        return await cls._post(
            url=url,
            method_name=method_name,
            timeout=timeout,
            proxies=proxies,
            provider_name=provider_name,
            form_data=data,
            files=files,
        )

    @classmethod
    def post_json(cls, **kwargs: Any) -> dict[str, Any]:
        return async_to_sync(cls.apost_json)(**kwargs)

    @classmethod
    def post_multipart(cls, **kwargs: Any) -> dict[str, Any]:
        return async_to_sync(cls.apost_multipart)(**kwargs)

    @classmethod
    async def _post(
        cls,
        *,
        url: str,
        method_name: str,
        timeout: tuple[float, float],
        proxies: dict[str, str] | None,
        provider_name: str,
        json_payload: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        cls._validate_method(method_name)
        try:
            await sync_to_async(
                validate_public_https_url,
                thread_sensitive=False,
            )(
                url,
                resolve_dns=bool(getattr(settings, "IS_PROD", False)),
            )
        except UnsafeOutboundUrlError:
            raise BotProviderTransportError(
                f"{provider_name} API endpoint configuration is unsafe."
            ) from None

        timeout_config = httpx.Timeout(
            connect=float(timeout[0]),
            read=float(timeout[1]),
            write=float(timeout[1]),
            pool=float(timeout[0]),
        )
        try:
            async with httpx.AsyncClient(
                timeout=timeout_config,
                proxy=cls._proxy_url(proxies),
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=json_payload,
                    data=form_data,
                    files=files,
                    headers={"Accept": "application/json"},
                ) as response:
                    if 300 <= response.status_code < 400:
                        raise BotProviderTransportError(
                            f"{provider_name} API redirects are not accepted."
                        )
                    raw_body = await cls._read_bounded(response, provider_name)
                    if response.status_code >= 400:
                        raise BotProviderTransportError(
                            f"{provider_name} API returned an error."
                        )
                    try:
                        encoding = response.encoding or "utf-8"
                        body = json.loads(raw_body.decode(encoding))
                    except (LookupError, UnicodeDecodeError, json.JSONDecodeError):
                        raise BotProviderTransportError(
                            f"{provider_name} API returned invalid JSON."
                        ) from None
                    if not isinstance(body, dict):
                        raise BotProviderTransportError(
                            f"{provider_name} API returned an invalid response."
                        )
                    return body
        except BotProviderTransportError:
            raise
        except httpx.HTTPError:
            raise BotProviderTransportError(
                f"{provider_name} API transport error."
            ) from None

    @classmethod
    async def _read_bounded(
        cls,
        response: httpx.Response,
        provider_name: str,
    ) -> bytes:
        max_bytes = max(
            1024,
            min(
                int(
                    getattr(
                        settings,
                        "BOT_PROVIDER_MAX_RESPONSE_BYTES",
                        cls.DEFAULT_MAX_RESPONSE_BYTES,
                    )
                ),
                5 * 1024 * 1024,
            ),
        )
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    raise BotProviderTransportError(
                        f"{provider_name} API response is too large."
                    )
            except ValueError:
                pass

        body = bytearray()
        async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > max_bytes:
                raise BotProviderTransportError(
                    f"{provider_name} API response is too large."
                )
        return bytes(body)

    @staticmethod
    def _proxy_url(proxies: dict[str, str] | None) -> str | None:
        if not proxies:
            return None
        return proxies.get("https") or proxies.get("http")

    @classmethod
    def _validate_method(cls, method_name: str) -> None:
        if not cls._METHOD_PATTERN.fullmatch(str(method_name or "")):
            raise BotProviderTransportError("Invalid bot API method name.")
