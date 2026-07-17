from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from asgiref.sync import async_to_sync

from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.constants.proxy_urls import ProxyUrls
from backend.apps.core_models.enum.general_enum import RequestMethod

logger = CommonUtils.get_project_logger(__name__)

_METHOD_MAP = {
    RequestMethod.GET: "GET",
    RequestMethod.POST: "POST",
    RequestMethod.PUT: "PUT",
    RequestMethod.DELETE: "DELETE",
}


class HTTPRequestError(RuntimeError):
    """One exception type for all request failures and non-success responses."""

    def __init__(
        self,
        message: str,
        *,
        url: str,
        method: str,
        status_code: int | None = None,
        response_text: str | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.url = url
        self.method = method
        self.status_code = status_code
        self.response_text = response_text
        self.__cause__ = cause


@dataclass(frozen=True)
class RetryConfig:
    total: int = 5
    backoff_factor: float = 4.0
    status_forcelist: tuple[int, ...] = (408, 429, 500, 502, 503, 504)
    respect_retry_after_header: bool = True


class RequestUtils:
    """Async-first HTTP utility with a synchronous compatibility wrapper."""

    @staticmethod
    def _safe_log_params(params: Mapping[str, Any]) -> dict[str, Any]:
        safe = dict(params)

        if "headers" in safe and isinstance(safe["headers"], dict):
            headers = dict(safe["headers"])
            for key in list(headers.keys()):
                lowered = key.lower()
                if ("api" in lowered and "key" in lowered) or lowered == "authorization":
                    headers[key] = "***"
            safe["headers"] = headers

        if "params" in safe and isinstance(safe["params"], dict):
            params_copy = dict(safe["params"])
            for key, value in list(params_copy.items()):
                lowered = str(key).lower()
                if any(
                    part in lowered
                    for part in (
                        "token",
                        "password",
                        "secret",
                        "api_key",
                        "apikey",
                        "authorization",
                    )
                ):
                    params_copy[key] = "***"
                    continue
                text = str(value)
                if len(text) > 400:
                    params_copy[key] = text[:400] + "...(truncated)"
            safe["params"] = params_copy

        for key in ("data", "json", "files"):
            if safe.get(key) is not None:
                safe[key] = "<omitted>"
        return safe

    @staticmethod
    def _safe_url(url: str, *, redact_entire_url: bool = False) -> str:
        if redact_entire_url:
            try:
                parts = urlsplit(url)
                return urlunsplit((parts.scheme, parts.netloc, "/<redacted>", "", ""))
            except Exception:
                return "<redacted-url>"
        try:
            parts = urlsplit(url)
            safe_query = []
            for key, value in parse_qsl(parts.query, keep_blank_values=True):
                lowered = key.lower()
                safe_query.append(
                    (
                        key,
                        "***"
                        if any(
                            part in lowered
                            for part in (
                                "token",
                                "password",
                                "secret",
                                "key",
                                "authorization",
                            )
                        )
                        else value,
                    )
                )
            return urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(safe_query), "")
            )
        except Exception:
            return "<invalid-url>"

    @staticmethod
    def short_body(resp: httpx.Response | None, limit: int = 800) -> str:
        if resp is None:
            return "<no response>"
        try:
            text = resp.text or ""
        except Exception:
            try:
                text = (resp.content or b"")[:limit].decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                return "<unreadable body>"
        text = text.strip()
        return text if len(text) <= limit else text[:limit] + "...(truncated)"

    @classmethod
    async def arequest(
        cls,
        *,
        method: RequestMethod,
        url: str,
        headers: Optional[Mapping[str, str]] = None,
        params: Optional[Mapping[str, Any]] = None,
        data: Any = None,
        json: Any = None,
        files: Any = None,
        proxies: Optional[dict[str, str]] = None,
        timeout: Optional[float | Tuple[float, float]] = (3.0, 60.0),
        retry: RetryConfig = RetryConfig(),
        rotate_proxy_on_error: bool = True,
        raise_for_status: bool = True,
        auth=None,
        redact_url: bool = False,
    ) -> httpx.Response:
        try:
            method_str = _METHOD_MAP[method]
        except KeyError:
            raise NotImplementedError(f"Unsupported method: {method!r}") from None

        safe_url = cls._safe_url(url, redact_entire_url=redact_url)
        request_kwargs: dict[str, Any] = {
            "headers": dict(headers) if headers else None,
            "params": dict(params) if params else None,
            "data": data,
            "json": json,
            "files": files,
            "auth": auth,
        }
        attempts = max(1, int(retry.total) + 1)
        current_proxy = cls._proxy_url(proxies)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await cls._send(
                    method=method_str,
                    url=url,
                    request_kwargs=request_kwargs,
                    proxy=current_proxy,
                    timeout=timeout,
                )
                should_retry_status = (
                    response.status_code in retry.status_forcelist
                    and method_str in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}
                    and attempt < attempts
                )
                if should_retry_status:
                    await asyncio.sleep(cls._retry_delay(retry, attempt, response))
                    continue

                if not response.is_success:
                    safe = cls._safe_log_params(request_kwargs)
                    logger.warning(
                        "Non-success response | %s %s | status=%s | kwargs=%s",
                        method,
                        safe_url,
                        response.status_code,
                        safe,
                    )
                    if raise_for_status:
                        raise HTTPRequestError(
                            f"HTTP request failed with status={response.status_code}.",
                            url=safe_url,
                            method=str(method),
                            status_code=response.status_code,
                            response_text=None,
                        )
                return response
            except httpx.ProxyError as exc:
                last_error = exc
                safe = cls._safe_log_params(request_kwargs)
                logger.error(
                    "ProxyError | %s %s | %s | kwargs=%s",
                    method,
                    safe_url,
                    exc,
                    safe,
                )
                if rotate_proxy_on_error and attempt < attempts:
                    current_proxy = cls._proxy_url(ProxyUrls.get_proxy())
                    await asyncio.sleep(cls._retry_delay(retry, attempt, None))
                    continue
                break
            except HTTPRequestError:
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                safe = cls._safe_log_params(request_kwargs)
                logger.error(
                    "RequestException | %s %s | %s | kwargs=%s",
                    method,
                    safe_url,
                    exc,
                    safe,
                )
                if attempt < attempts:
                    await asyncio.sleep(cls._retry_delay(retry, attempt, None))
                    continue
                break

        raise HTTPRequestError(
            "Network/transport error while sending request.",
            url=safe_url,
            method=str(method),
            cause=last_error,
        ) from last_error

    @classmethod
    def request(cls, **kwargs: Any) -> httpx.Response:
        """Synchronous compatibility boundary for existing Django/adapter code."""

        return async_to_sync(cls.arequest)(**kwargs)

    @staticmethod
    async def _send(
        *,
        method: str,
        url: str,
        request_kwargs: dict[str, Any],
        proxy: str | None,
        timeout: Optional[float | Tuple[float, float]],
    ) -> httpx.Response:
        timeout_config = RequestUtils._timeout(timeout)
        async with httpx.AsyncClient(
            timeout=timeout_config,
            proxy=proxy,
            follow_redirects=False,
        ) as client:
            return await client.request(method=method, url=url, **request_kwargs)

    @staticmethod
    def _timeout(
        timeout: Optional[float | Tuple[float, float]],
    ) -> httpx.Timeout | None:
        if timeout is None:
            return None
        if isinstance(timeout, tuple):
            connect, read = timeout
            return httpx.Timeout(
                connect=float(connect),
                read=float(read),
                write=float(read),
                pool=float(connect),
            )
        return httpx.Timeout(float(timeout))

    @staticmethod
    def _proxy_url(proxies: Optional[dict[str, str]]) -> str | None:
        if not proxies:
            return None
        return proxies.get("https") or proxies.get("http")

    @staticmethod
    def _retry_delay(
        retry: RetryConfig,
        attempt: int,
        response: httpx.Response | None,
    ) -> float:
        if retry.respect_retry_after_header and response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(max(float(retry_after), 0.0), 60.0)
                except ValueError:
                    pass
        return min(max(retry.backoff_factor * (2 ** max(attempt - 1, 0)), 0.0), 60.0)
