from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit

from django.conf import settings
from django.templatetags.static import static
from django.utils.encoding import iri_to_uri


class SeoRequestUrlAdapter:
    def __init__(self, request, canonical_origin: str | None = None):
        self._request = request
        candidates = (
            getattr(settings, "SEO_CANONICAL_ORIGIN", ""),
            canonical_origin,
            self._request.build_absolute_uri("/"),
        )
        self._canonical_origin = next(
            normalized
            for candidate in candidates
            if (normalized := self._normalize_origin(candidate))
        )

    @staticmethod
    def _normalize_origin(value: str | None) -> str | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None
        if not raw_value.startswith(("http://", "https://")):
            raw_value = f"https://{raw_value.strip('/')}"

        parts = urlsplit(raw_value)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return None
        return urlunsplit((parts.scheme, parts.netloc, "/", "", ""))

    @classmethod
    def from_project(cls, request, project) -> "SeoRequestUrlAdapter":
        email_domain = (
            project.get("email_domain", "")
            if hasattr(project, "get")
            else getattr(project, "email_domain", "")
        )
        return cls(request, canonical_origin=str(email_domain or ""))

    @property
    def origin(self) -> str:
        return self._canonical_origin.rstrip("/")

    def absolute_url(self, path_or_url: str | None) -> str:
        if not path_or_url:
            return self.origin + "/"
        value = str(path_or_url).strip()
        if value.startswith(("http://", "https://")):
            return iri_to_uri(value)
        return iri_to_uri(urljoin(self.origin + "/", value.lstrip("/")))

    def canonical_url(self, path: str | None = None) -> str:
        canonical_path = path or self._request.path or "/"
        return self.absolute_url(canonical_path)

    def static_url(self, static_path: str) -> str:
        return self.absolute_url(static(static_path))
