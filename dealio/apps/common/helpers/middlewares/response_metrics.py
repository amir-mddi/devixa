import logging
import os
import time

from django.urls import resolve, Resolver404
from prometheus_client import Histogram, Counter

from dealio.apps.common.response_utils import CommonJsonResponse
from dealio.apps.core_models.vo.common_vo import ResponseVO

logger = logging.getLogger("dealio")

REQUEST_LATENCY = Histogram(
    "django_request_latency_seconds",
    "Response time in seconds for requests",
    ["endpoint", "method", "process_id"],
    buckets=[0.1, 0.2, 0.5, 1, 2, 5, 10]
)
EXCEPTION_COUNT = Counter(
    "django_request_exceptions_total",
    "Total exceptions raised by endpoint",
    ["endpoint", "method"]
)


class ResponseMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            resolve(request.path)
        except Resolver404:
            return CommonJsonResponse(status_code=404, status=ResponseVO.failed, message=ResponseVO.invalid_url_msg,
                                      code=ResponseVO.invalid_url_code)
        start_time = time.time()
        endpoint = request.path
        method = request.method
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            EXCEPTION_COUNT.labels(endpoint=endpoint, method=method).inc()
            logger.error(f"Exception raised with detail: {e}")
            if os.environ.get('ENV', 'DEV') == 'PROD':
                return CommonJsonResponse(status_code=500, status=ResponseVO.failed,
                                          message=ResponseVO.invalid_internal_error_msg,
                                          code=ResponseVO.invalid_internal_error_code)
            raise e
        finally:
            elapsed_time = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=endpoint, method=method, process_id=os.getpid()).observe(elapsed_time)
