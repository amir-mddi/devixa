from __future__ import annotations

from dealio.apps.common.utils.common_utils import CommonUtils
from dataclasses import dataclass
from typing import Any, Optional, Mapping
from typing import Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dealio.apps.core_models.constants.proxy_urls import ProxyUrls
from dealio.apps.core_models.enum.general_enum import RequestMethod
from dealio.apps.core_models.vo.common_vo import CommonVO

logger = CommonUtils.get_project_logger(__name__)

_METHOD_MAP = {
    RequestMethod.GET: "GET",
    RequestMethod.POST: "POST",
    RequestMethod.PUT: "PUT",
    RequestMethod.DELETE: "DELETE",
}


class HTTPRequestError(RuntimeError):
    """One exception type for all request failures (network + non-2xx)."""

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
    _sessions: dict[RetryConfig, requests.Session] = {}

    @classmethod
    def _get_session(cls, retry_cfg: RetryConfig) -> requests.Session:
        if retry_cfg in cls._sessions:
            return cls._sessions[retry_cfg]

        retry = Retry(
            total=retry_cfg.total,
            connect=retry_cfg.total,
            read=retry_cfg.total,
            status=retry_cfg.total,
            backoff_factor=retry_cfg.backoff_factor,
            status_forcelist=list(retry_cfg.status_forcelist),
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]),
            raise_on_status=False,
            respect_retry_after_header=retry_cfg.respect_retry_after_header,
        )

        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()
        session.mount(CommonVO.http, adapter)
        session.mount(CommonVO.https, adapter)

        cls._sessions[retry_cfg] = session
        return session

    @staticmethod
    def _safe_log_params(params: Mapping[str, Any]) -> dict[str, Any]:
        safe = dict(params)

        if "headers" in safe and isinstance(safe["headers"], dict):
            headers = dict(safe["headers"])
            for k in list(headers.keys()):
                lk = k.lower()
                if "api" in lk and "key" in lk:
                    headers[k] = "***"
                if lk in ("authorization",):
                    headers[k] = "***"
            safe["headers"] = headers

        if "params" in safe and isinstance(safe["params"], dict):
            p = dict(safe["params"])
            for k, v in list(p.items()):
                lowered_key = str(k).lower()
                if any(part in lowered_key for part in ("token", "password", "secret", "api_key", "apikey", "authorization")):
                    p[k] = "***"
                    continue
                text = str(v)
                if len(text) > 400:
                    p[k] = text[:400] + "...(truncated)"
            safe["params"] = p

        if safe.get("data") is not None:
            safe["data"] = "<omitted>"
        if safe.get("json") is not None:
            safe["json"] = "<omitted>"
        if safe.get("files") is not None:
            safe["files"] = "<omitted>"

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
                lowered_key = key.lower()
                safe_query.append((
                    key,
                    "***" if any(part in lowered_key for part in ("token", "password", "secret", "key", "authorization")) else value,
                ))
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(safe_query), ""))
        except Exception:
            return "<invalid-url>"

    @staticmethod
    def short_body(resp: requests.Response, limit: int = 800) -> str:
        if resp is None:
            return "<no response>"
        try:
            text = resp.text or ""
        except Exception:
            try:
                raw = resp.content or b""
                text = raw[:limit].decode("utf-8", errors="replace")
            except Exception:
                return "<unreadable body>"

        text = text.strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "...(truncated)"

    @staticmethod
    def _short_body(resp: requests.Response, limit: int = 800) -> str:
        try:
            text = resp.text or ""
        except Exception:
            return "<unreadable body>"
        return text if len(text) <= limit else text[:limit] + "...(truncated)"

    @classmethod
    def request(
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
    ) -> requests.Response:
        session = cls._get_session(retry)
        safe_url = cls._safe_url(url, redact_entire_url=redact_url)

        request_kwargs: dict[str, Any] = {
            "headers": dict(headers) if headers else None,
            "params": dict(params) if params else None,
            "data": data,
            "json": json,
            "files": files,
            "proxies": proxies,
            "timeout": timeout,
            "auth": auth,
        }

        try:
            resp = cls._send(session, method, url, request_kwargs)
        except requests.exceptions.ProxyError as exc:
            safe = cls._safe_log_params(request_kwargs)
            logger.error("ProxyError | %s %s | %s | kwargs=%s", method, safe_url, exc, safe)

            if not rotate_proxy_on_error:
                raise HTTPRequestError(
                    "Proxy error while sending request.",
                    url=safe_url,
                    method=str(method),
                    cause=exc,
                ) from exc

            request_kwargs["proxies"] = ProxyUrls.get_proxy()
            safe2 = cls._safe_log_params(request_kwargs)
            logger.info("Retrying with rotated proxy | %s %s | kwargs=%s", method, safe_url, safe2)

            try:
                resp = cls._send(session, method, url, request_kwargs)
            except Exception as exc2:
                raise HTTPRequestError(
                    "Request failed even after rotating proxy.",
                    url=safe_url,
                    method=str(method),
                    cause=exc2,
                ) from exc2

        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as exc:
            safe = cls._safe_log_params(request_kwargs)
            logger.error("RequestException | %s %s | %s | kwargs=%s", method, safe_url, exc, safe)
            raise HTTPRequestError(
                "Network/transport error while sending request.",
                url=safe_url,
                method=str(method),
                cause=exc,
            ) from exc

        if not resp.ok:
            safe = cls._safe_log_params(request_kwargs)
            # Provider responses can contain credentials, OTPs or PII. Keep
            # operational logs limited to metadata and sanitized request data.
            logger.warning(
                "Non-success response | %s %s | status=%s | kwargs=%s",
                method,
                safe_url,
                resp.status_code,
                safe,
            )

            if raise_for_status:
                raise HTTPRequestError(
                    f"HTTP request failed with status={resp.status_code}.",
                    url=safe_url,
                    method=str(method),
                    status_code=resp.status_code,
                    response_text=None,
                )

        return resp

    @staticmethod
    def _send(session: requests.Session, method: RequestMethod, url: str, kwargs: dict[str, Any]) -> requests.Response:
        try:
            method_str = _METHOD_MAP[method]
        except KeyError:
            raise NotImplementedError(f"Unsupported method: {method!r}")
        return session.request(method=method_str, url=url, **kwargs)
