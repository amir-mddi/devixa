from __future__ import annotations

import os
import time

from django.conf import settings
from prometheus_client import Counter, Histogram

from backend.apps.common.response_utils import CommonJsonResponse
from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.vo.common_vo import ResponseVO

logger = CommonUtils.get_project_logger(__name__)

REQUEST_LATENCY = Histogram(
    "django_request_latency_seconds",
    "Response time in seconds for requests",
    ["endpoint", "method", "process_id"],
    buckets=[0.1, 0.2, 0.5, 1, 2, 5, 10],
)
EXCEPTION_COUNT = Counter(
    "django_request_exceptions_total",
    "Total exceptions raised by endpoint",
    ["endpoint", "method"],
)


def _endpoint_label(request) -> str:
    """Use bounded route metadata instead of attacker-controlled raw paths."""
    match = getattr(request, "resolver_match", None)
    if match:
        return match.route or match.view_name or match.url_name or "resolved"
    return "unresolved"


class ResponseMetricsMiddleware(AsyncCompatibleMiddleware):
    def _record_latency(self, *, request, method: str, started_at: float) -> None:
        REQUEST_LATENCY.labels(
            endpoint=_endpoint_label(request),
            method=method,
            process_id=os.getpid(),
        ).observe(time.monotonic() - started_at)

    @staticmethod
    def _handle_exception(*, request, method: str):
        EXCEPTION_COUNT.labels(
            endpoint=_endpoint_label(request),
            method=method,
        ).inc()
        logger.exception("Unhandled request exception.")
        if not settings.DEBUG:
            return CommonJsonResponse(
                status_code=500,
                status=ResponseVO.failed,
                message=ResponseVO.invalid_internal_error_msg,
                code=ResponseVO.invalid_internal_error_code,
            )
        raise

    def process_sync(self, request):
        started_at = time.monotonic()
        method = request.method
        try:
            return self.get_response(request)
        except Exception:
            return self._handle_exception(request=request, method=method)
        finally:
            self._record_latency(
                request=request,
                method=method,
                started_at=started_at,
            )

    async def process_async(self, request):
        started_at = time.monotonic()
        method = request.method
        try:
            return await self.get_response(request)
        except Exception:
            return self._handle_exception(request=request, method=method)
        finally:
            self._record_latency(
                request=request,
                method=method,
                started_at=started_at,
            )
