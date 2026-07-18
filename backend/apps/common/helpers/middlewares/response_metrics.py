"""Backward-compatible import for the centralized Prometheus middleware."""

from backend.apps.common.observability.prometheus.middleware import (
    PrometheusRequestMetricsMiddleware,
    ResponseMetricsMiddleware,
)

__all__ = ["PrometheusRequestMetricsMiddleware", "ResponseMetricsMiddleware"]
