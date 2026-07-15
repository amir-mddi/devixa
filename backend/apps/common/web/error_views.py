from __future__ import annotations

import logging

from django.contrib.auth.models import AnonymousUser

from backend.apps.common.adapters.http_error_response_adapter import (
    HttpErrorResponseAdapter,
)
from backend.apps.common.logic.http_error_logic import (
    CsrfFailureErrorLogic,
    NotFoundErrorLogic,
)
from backend.apps.common.project_config import get_request_project_context
from backend.apps.common.vo.http_error_vo import HttpErrorTextVO
from backend.apps.common.web.seo.dtos.seo_dtos import SeoMetadataOverrideDTO
from backend.apps.common.web.seo.enums.seo_enums import SeoRobotsDirectiveEnum
from backend.apps.common.web.seo.logic.metadata_logic import SeoMetadataLogic
from backend.apps.common.web.seo.mixins import SEO_REQUEST_ATTRIBUTE

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    """Content-negotiated CSRF failure response for browser pages and APIs."""

    if not hasattr(request, "user"):
        request.user = AnonymousUser()

    error = CsrfFailureErrorLogic.from_reason(reason)
    logger.warning(
        "CSRF validation failed path=%s origin=%s referer=%s code=%s",
        getattr(request, "path", ""),
        request.META.get("HTTP_ORIGIN", ""),
        request.META.get("HTTP_REFERER", ""),
        error.code,
    )
    return HttpErrorResponseAdapter.build(request=request, error=error)


def page_not_found(request, exception):
    """Render the same safe 404 response for unknown URLs and missing objects."""

    if not hasattr(request, "user"):
        request.user = AnonymousUser()

    error = NotFoundErrorLogic.from_exception(exception)
    seo = SeoMetadataLogic().build(
        request=request,
        project_mapping=get_request_project_context(request),
        override=SeoMetadataOverrideDTO(
            title=error.title,
            description=error.message,
            robots=SeoRobotsDirectiveEnum.NOINDEX.value,
        ),
    )
    setattr(request, SEO_REQUEST_ATTRIBUTE, seo)

    logger.info(
        "Page not found path=%s code=%s exception_type=%s",
        getattr(request, "path", ""),
        error.code,
        type(exception).__name__,
    )

    response = HttpErrorResponseAdapter.build(
        request=request,
        error=error,
        template_name="web/errors/404.html",
        context={
            "seo": seo,
            "not_found_text": HttpErrorTextVO,
        },
        allow_view_override=False,
    )
    response["X-Robots-Tag"] = SeoRobotsDirectiveEnum.NOINDEX.value
    return response

