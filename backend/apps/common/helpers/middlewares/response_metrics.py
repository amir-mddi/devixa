import os
import time

from django.conf import settings
from prometheus_client import Counter, Histogram

from backend.apps.common.response_utils import CommonJsonResponse
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


class ResponseMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()
        method = request.method
        try:
            response = self.get_response(request)
            return response
        except Exception:
            endpoint = _endpoint_label(request)
            EXCEPTION_COUNT.labels(endpoint=endpoint, method=method).inc()
            logger.exception("Unhandled request exception.")
            if not settings.DEBUG:
                return CommonJsonResponse(
                    status_code=500,
                    status=ResponseVO.failed,
                    message=ResponseVO.invalid_internal_error_msg,
                    code=ResponseVO.invalid_internal_error_code,
                )
            raise
        finally:
            endpoint = _endpoint_label(request)
            REQUEST_LATENCY.labels(
                endpoint=endpoint,
                method=method,
                process_id=os.getpid(),
            ).observe(time.monotonic() - start_time)
