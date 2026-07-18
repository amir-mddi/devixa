from __future__ import annotations

import time

from django.conf import settings
from django.urls import Resolver404, resolve

from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware

from .metrics import get_metrics, is_prometheus_enabled, safe_content_length
from .value_objects import PrometheusRouteVO


def resolve_route_label(request) -> str:
    """Return bounded URL metadata and never use attacker-controlled raw paths."""

    match = getattr(request, "resolver_match", None)
    if match is None:
        try:
            match = resolve(getattr(request, "path_info", request.path))
        except Resolver404:
            return PrometheusRouteVO.NOT_FOUND
        except Exception:
            return PrometheusRouteVO.UNRESOLVED

    return (
        getattr(match, "view_name", None)
        or getattr(match, "route", None)
        or getattr(match, "url_name", None)
        or PrometheusRouteVO.UNRESOLVED
    )


def is_excluded_path(path: str) -> bool:
    config = getattr(settings, "PROMETHEUS_CONFIG", None)
    prefixes = getattr(config, "excluded_path_prefixes", ())
    return any(path.startswith(prefix) for prefix in prefixes)


class PrometheusRequestMetricsMiddleware(AsyncCompatibleMiddleware):
    """Record bounded HTTP metrics without changing response behavior."""

    @staticmethod
    def _should_measure(request) -> bool:
        return is_prometheus_enabled() and not is_excluded_path(request.path)

    @staticmethod
    def _finish(
        *, request, response, started_at: float, status_code: int | None = None
    ) -> None:
        metrics = get_metrics()
        method = request.method.upper()
        route = resolve_route_label(request)
        status = str(
            status_code
            if status_code is not None
            else getattr(response, "status_code", 500)
        )

        metrics.http_requests.labels(
            method=method,
            route=route,
            status=status,
        ).inc()
        metrics.http_request_duration.labels(
            method=method,
            route=route,
        ).observe(max(0.0, time.perf_counter() - started_at))

        response_size = safe_content_length(response) if response is not None else None
        if response_size is not None:
            metrics.http_response_size.labels(
                method=method,
                route=route,
            ).observe(response_size)

    def process_sync(self, request):
        if not self._should_measure(request):
            return self.get_response(request)

        method = request.method.upper()
        metrics = get_metrics()
        started_at = time.perf_counter()
        metrics.http_requests_in_progress.labels(method=method).inc()
        try:
            response = self.get_response(request)
        except Exception as exception:
            route = resolve_route_label(request)
            metrics.http_exceptions.labels(
                method=method,
                route=route,
                exception=exception.__class__.__name__,
            ).inc()
            request._prometheus_exception_recorded = True
            self._finish(
                request=request,
                response=None,
                started_at=started_at,
                status_code=500,
            )
            raise
        else:
            self._finish(request=request, response=response, started_at=started_at)
            return response
        finally:
            metrics.http_requests_in_progress.labels(method=method).dec()

    async def process_async(self, request):
        if not self._should_measure(request):
            return await self.get_response(request)

        method = request.method.upper()
        metrics = get_metrics()
        started_at = time.perf_counter()
        metrics.http_requests_in_progress.labels(method=method).inc()
        try:
            response = await self.get_response(request)
        except Exception as exception:
            route = resolve_route_label(request)
            metrics.http_exceptions.labels(
                method=method,
                route=route,
                exception=exception.__class__.__name__,
            ).inc()
            request._prometheus_exception_recorded = True
            self._finish(
                request=request,
                response=None,
                started_at=started_at,
                status_code=500,
            )
            raise
        else:
            self._finish(request=request, response=response, started_at=started_at)
            return response
        finally:
            metrics.http_requests_in_progress.labels(method=method).dec()


# Backward-compatible import path used by the existing project tests.
ResponseMetricsMiddleware = PrometheusRequestMetricsMiddleware
