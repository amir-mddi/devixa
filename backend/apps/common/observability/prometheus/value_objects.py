from __future__ import annotations


class PrometheusMetricVO:
    HTTP_REQUESTS = "http_requests_total"
    HTTP_REQUEST_DURATION = "http_request_duration_seconds"
    HTTP_REQUESTS_IN_PROGRESS = "http_requests_in_progress"
    HTTP_RESPONSE_SIZE = "http_response_size_bytes"
    HTTP_EXCEPTIONS = "http_request_exceptions_total"
    HEALTH_STATUS = "health_check_status"
    HEALTH_DURATION = "health_check_duration_seconds"
    CELERY_TASKS = "celery_tasks_total"
    CELERY_TASK_DURATION = "celery_task_duration_seconds"
    CELERY_TASKS_IN_PROGRESS = "celery_tasks_in_progress"


class PrometheusLabelVO:
    METHOD = "method"
    ROUTE = "route"
    STATUS = "status"
    STATUS_CLASS = "status_class"
    EXCEPTION = "exception"
    DEPENDENCY = "dependency"
    TASK = "task"
    STATE = "state"


class PrometheusRouteVO:
    UNRESOLVED = "__unresolved__"
    NOT_FOUND = "__not_found__"


class PrometheusHeaderVO:
    TOKEN = "X-Metrics-Token"
    AUTHORIZATION = "Authorization"
    BEARER_PREFIX = "Bearer "
    CACHE_CONTROL = "no-store"


class PrometheusContentVO:
    DISABLED = "Prometheus metrics are disabled."
    UNAVAILABLE = "Prometheus metrics are unavailable."
