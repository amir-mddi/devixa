from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from django.conf import settings
from prometheus_client import Counter, Gauge, Histogram

from .value_objects import PrometheusMetricVO


@dataclass(frozen=True, slots=True)
class PrometheusMetricSet:
    http_requests: Counter
    http_request_duration: Histogram
    http_requests_in_progress: Gauge
    http_response_size: Histogram
    http_exceptions: Counter
    health_status: Gauge
    health_duration: Histogram
    celery_tasks: Counter
    celery_task_duration: Histogram
    celery_tasks_in_progress: Gauge


def _configuration():
    return getattr(settings, "PROMETHEUS_CONFIG", None)


def is_prometheus_enabled() -> bool:
    return bool(getattr(settings, "PROMETHEUS_ENABLED", False))


@lru_cache(maxsize=1)
def get_metrics() -> PrometheusMetricSet:
    """Build the project's metric objects once per process.

    The factory is lazy so importing application modules while metrics are
    disabled does not register collectors or create multiprocess files.
    """

    config = _configuration()
    namespace = getattr(config, "namespace", "django_app")
    request_buckets = tuple(
        getattr(
            config,
            "request_duration_buckets",
            (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
    )
    response_size_buckets = tuple(
        getattr(
            config,
            "response_size_buckets",
            (256, 1024, 4096, 16384, 65536, 262144, 1048576, 4194304),
        )
    )
    health_buckets = tuple(
        getattr(
            config,
            "health_duration_buckets",
            (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
    )
    celery_buckets = tuple(
        getattr(
            config,
            "celery_duration_buckets",
            (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0),
        )
    )

    return PrometheusMetricSet(
        http_requests=Counter(
            PrometheusMetricVO.HTTP_REQUESTS,
            "Total HTTP responses produced by the Django application.",
            ("method", "route", "status"),
            namespace=namespace,
        ),
        http_request_duration=Histogram(
            PrometheusMetricVO.HTTP_REQUEST_DURATION,
            "HTTP request duration in seconds, excluding configured operational paths.",
            ("method", "route"),
            namespace=namespace,
            buckets=request_buckets,
        ),
        http_requests_in_progress=Gauge(
            PrometheusMetricVO.HTTP_REQUESTS_IN_PROGRESS,
            "HTTP requests currently being processed by method.",
            ("method",),
            namespace=namespace,
            multiprocess_mode="livesum",
        ),
        http_response_size=Histogram(
            PrometheusMetricVO.HTTP_RESPONSE_SIZE,
            "HTTP response body size in bytes for non-streaming responses.",
            ("method", "route"),
            namespace=namespace,
            buckets=response_size_buckets,
        ),
        http_exceptions=Counter(
            PrometheusMetricVO.HTTP_EXCEPTIONS,
            "Unhandled Django request exceptions.",
            ("method", "route", "exception"),
            namespace=namespace,
        ),
        health_status=Gauge(
            PrometheusMetricVO.HEALTH_STATUS,
            "Latest dependency health result: 1 for healthy and 0 for unhealthy.",
            ("dependency",),
            namespace=namespace,
            multiprocess_mode="livemin",
        ),
        health_duration=Histogram(
            PrometheusMetricVO.HEALTH_DURATION,
            "Dependency health-check duration in seconds.",
            ("dependency",),
            namespace=namespace,
            buckets=health_buckets,
        ),
        celery_tasks=Counter(
            PrometheusMetricVO.CELERY_TASKS,
            "Celery task executions by final state.",
            ("task", "state"),
            namespace=namespace,
        ),
        celery_task_duration=Histogram(
            PrometheusMetricVO.CELERY_TASK_DURATION,
            "Celery task execution duration in seconds.",
            ("task",),
            namespace=namespace,
            buckets=celery_buckets,
        ),
        celery_tasks_in_progress=Gauge(
            PrometheusMetricVO.CELERY_TASKS_IN_PROGRESS,
            "Celery tasks currently executing.",
            ("task",),
            namespace=namespace,
            multiprocess_mode="livesum",
        ),
    )


class PrometheusMetricsAdapter:
    """Provider boundary used by middleware, health checks, and task signals."""

    @staticmethod
    def enabled() -> bool:
        return is_prometheus_enabled()

    @classmethod
    def observe_health(
        cls,
        *,
        dependency: str,
        healthy: bool,
        duration_seconds: float,
    ) -> None:
        if not cls.enabled():
            return
        metrics = get_metrics()
        metrics.health_status.labels(dependency=dependency).set(1 if healthy else 0)
        metrics.health_duration.labels(dependency=dependency).observe(
            max(0.0, duration_seconds)
        )

    @classmethod
    def increment_exception(
        cls,
        *,
        method: str,
        route: str,
        exception_name: str,
    ) -> None:
        if not cls.enabled():
            return
        get_metrics().http_exceptions.labels(
            method=method,
            route=route,
            exception=exception_name,
        ).inc()

    @staticmethod
    def clear_cache_for_tests() -> None:
        """Reset only the lazy Python reference; collectors stay registered."""
        get_metrics.cache_clear()


def safe_content_length(response: Any) -> int | None:
    if getattr(response, "streaming", False):
        return None
    content = getattr(response, "content", None)
    if content is None:
        return None
    try:
        return len(content)
    except (TypeError, ValueError):
        return None
