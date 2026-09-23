from __future__ import annotations

from typing import Mapping
from urllib.parse import urlsplit, urlunsplit


_ALLOWED_PROXY_SCHEMES = {"http", "https", "socks5", "socks5h"}


def normalize_proxy_url(proxy_url: str | None) -> str | None:
    """Return a httpx-compatible proxy URL or ``None``.

    The local dev environment sometimes uses ``socks://`` in env vars, while
    httpx expects ``socks5://``/``socks5h://``. This helper normalizes that
    legacy value and quietly ignores malformed/unsupported proxy strings rather
    than crashing web requests such as login + reCAPTCHA.
    """

    value = str(proxy_url or "").strip().strip('"').strip("'")
    if not value:
        return None

    if value.startswith("socks://"):
        value = "socks5://" + value[len("socks://"):]

    try:
        parts = urlsplit(value)
    except Exception:
        return None

    scheme = (parts.scheme or "").lower()
    if scheme not in _ALLOWED_PROXY_SCHEMES:
        return None
    if not parts.netloc:
        return None

    return urlunsplit((scheme, parts.netloc, parts.path, parts.query, parts.fragment))


def normalize_proxy_mapping(proxies: Mapping[str, str] | None) -> dict[str, str] | None:
    if not proxies:
        return None
    https_proxy = normalize_proxy_url(proxies.get("https"))
    http_proxy = normalize_proxy_url(proxies.get("http"))
    if not https_proxy and not http_proxy:
        return None
    resolved = https_proxy or http_proxy
    return {"http": http_proxy or resolved, "https": https_proxy or resolved}
