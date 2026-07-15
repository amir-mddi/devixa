from __future__ import annotations

from backend.apps.common.web.performance.value_objects.cache_policy_vo import (
    PublicPageCachePolicyVO,
    PublicPagePathVO,
)


class PublicPageCachePolicyLogic:
    """Choose a browser-cache policy without exposing private application pages."""

    def __init__(self) -> None:
        self._public_prefixes = tuple(item.value for item in PublicPagePathVO)

    def cache_control_for(self, *, path: str, method: str, content_type: str) -> str | None:
        if method not in {"GET", "HEAD"}:
            return None
        if not content_type.lower().startswith("text/html"):
            return None
        if path == "/":
            return PublicPageCachePolicyVO.CACHE_CONTROL.value
        if any(path.startswith(prefix) for prefix in self._public_prefixes if prefix != "/"):
            return PublicPageCachePolicyVO.CACHE_CONTROL.value
        return None
