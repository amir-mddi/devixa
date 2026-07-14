from __future__ import annotations

import logging

from django.contrib.auth.models import AnonymousUser

from dealio.apps.common.adapters.http_error_response_adapter import (
    HttpErrorResponseAdapter,
)
from dealio.apps.common.logic.http_error_logic import CsrfFailureErrorLogic

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
