from __future__ import annotations

from dealio.apps.common.enums.http_response_enum import HttpResponseFormatEnum
from dealio.apps.core_models.constants.common_vo import ExcludeViewResponseVO


class RequestFormatLogic:
    JSON_CONTENT_TYPES = (
        "application/json",
        "application/problem+json",
    )

    @classmethod
    def detect(cls, request) -> HttpResponseFormatEnum:
        if request is None:
            return HttpResponseFormatEnum.JSON

        path = str(getattr(request, "path", "") or "")
        api_prefix = ExcludeViewResponseVO.api_urls_include.rstrip("/")
        if path == api_prefix or path.startswith(f"{api_prefix}/"):
            return HttpResponseFormatEnum.JSON

        content_type = str(getattr(request, "content_type", "") or "").lower()
        if any(content_type.startswith(value) for value in cls.JSON_CONTENT_TYPES):
            return HttpResponseFormatEnum.JSON

        accept = str(request.META.get("HTTP_ACCEPT", "") or "").lower()
        accepts_html = "text/html" in accept or "application/xhtml+xml" in accept
        accepts_json = any(value in accept for value in cls.JSON_CONTENT_TYPES)
        if accepts_json and not accepts_html:
            return HttpResponseFormatEnum.JSON

        return HttpResponseFormatEnum.HTML

    @classmethod
    def wants_json(cls, request) -> bool:
        return cls.detect(request) == HttpResponseFormatEnum.JSON
