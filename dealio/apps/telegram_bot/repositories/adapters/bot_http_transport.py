from __future__ import annotations

import json
import re
from typing import Any

import requests
from django.conf import settings

from dealio.apps.common.utils.network_security import (
    UnsafeOutboundUrlError,
    validate_public_https_url,
)


class BotProviderTransportError(RuntimeError):
    pass


class BotProviderHttpTransport:
    """Shared bounded HTTP transport for bot provider adapters.

    Provider tokens commonly live in URL paths, so exceptions and response
    bodies are deliberately replaced with generic errors at this boundary.
    """

    _METHOD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,99}$")
    DEFAULT_MAX_RESPONSE_BYTES = 1024 * 1024

    @classmethod
    def post_json(
        cls,
        *,
        url: str,
        method_name: str,
        payload: dict[str, Any],
        timeout: tuple[float, float],
        proxies: dict[str, str] | None,
        provider_name: str,
    ) -> dict[str, Any]:
        return cls._post(
            url=url,
            method_name=method_name,
            timeout=timeout,
            proxies=proxies,
            provider_name=provider_name,
            json_payload=payload,
        )

    @classmethod
    def post_multipart(
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
        return cls._post(
            url=url,
            method_name=method_name,
            timeout=timeout,
            proxies=proxies,
            provider_name=provider_name,
            form_data=data,
            files=files,
        )

    @classmethod
    def _post(
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
            validate_public_https_url(
                url,
                resolve_dns=bool(getattr(settings, "IS_PROD", False)),
            )
        except UnsafeOutboundUrlError:
            raise BotProviderTransportError(
                f"{provider_name} API endpoint configuration is unsafe."
            ) from None

        response = None
        try:
            response = requests.post(
                url,
                json=json_payload,
                data=form_data,
                files=files,
                timeout=timeout,
                proxies=proxies,
                allow_redirects=False,
                stream=True,
            )
            if 300 <= response.status_code < 400:
                raise BotProviderTransportError(
                    f"{provider_name} API redirects are not accepted."
                )
            raw_body = cls._read_bounded(response, provider_name)
            if response.status_code >= 400:
                raise BotProviderTransportError(
                    f"{provider_name} API returned an error."
                )
            try:
                body = json.loads(raw_body.decode(response.encoding or "utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise BotProviderTransportError(
                    f"{provider_name} API returned invalid JSON."
                ) from None
            if not isinstance(body, dict):
                raise BotProviderTransportError(
                    f"{provider_name} API returned an invalid response."
                )
            return body
        except requests.RequestException:
            raise BotProviderTransportError(
                f"{provider_name} API transport error."
            ) from None
        finally:
            if response is not None:
                response.close()

    @classmethod
    def _read_bounded(cls, response: requests.Response, provider_name: str) -> bytes:
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
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > max_bytes:
                raise BotProviderTransportError(
                    f"{provider_name} API response is too large."
                )
        return bytes(body)

    @classmethod
    def _validate_method(cls, method_name: str) -> None:
        if not cls._METHOD_PATTERN.fullmatch(str(method_name or "")):
            raise BotProviderTransportError("Invalid bot API method name.")
