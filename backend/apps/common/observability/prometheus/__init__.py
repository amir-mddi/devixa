"""Switchable Prometheus instrumentation for Django and Celery."""

from .metrics import PrometheusMetricsAdapter, is_prometheus_enabled

__all__ = ["PrometheusMetricsAdapter", "is_prometheus_enabled"]
