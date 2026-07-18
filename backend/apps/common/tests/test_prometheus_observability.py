from __future__ import annotations

import os
from unittest import mock

from asgiref.sync import iscoroutinefunction
from django.http import Http404, HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from backend.apps.common.observability.prometheus.exporter import build_registry
from backend.apps.common.observability.prometheus.metrics import get_metrics
from backend.apps.common.observability.prometheus.middleware import (
    PrometheusRequestMetricsMiddleware,
)
from backend.apps.common.observability.prometheus.views import prometheus_metrics
from backend.apps.core_models.dtos.setup_config import PrometheusConfiguration


class PrometheusConfigurationTests(SimpleTestCase):
    def test_master_switch_defaults_to_disabled(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = PrometheusConfiguration()
        self.assertFalse(config.use_prometheus)

    def test_namespace_is_normalized(self):
        with mock.patch.dict(
            os.environ,
            {"PROMETHEUS_NAMESPACE": "my-app"},
            clear=True,
        ):
            config = PrometheusConfiguration()
        self.assertEqual(config.namespace, "my_app")

    def test_invalid_bucket_order_is_rejected(self):
        with mock.patch.dict(
            os.environ,
            {"PROMETHEUS_REQUEST_DURATION_BUCKETS": "1,0.5"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                PrometheusConfiguration()


class PrometheusMiddlewareTests(SimpleTestCase):
    @override_settings(PROMETHEUS_ENABLED=True)
    def test_records_request_count_latency_and_size(self):
        request = RequestFactory().get("/observed-metric/")
        labels = {
            "method": "GET",
            "route": "__not_found__",
            "status": "204",
        }
        counter = get_metrics().http_requests.labels(**labels)
        before = counter._value.get()

        middleware = PrometheusRequestMetricsMiddleware(
            lambda _request: HttpResponse(status=204)
        )
        response = middleware(request)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(counter._value.get(), before + 1)

    @override_settings(PROMETHEUS_ENABLED=True)
    async def test_preserves_native_async_chain(self):
        request = RequestFactory().get("/observed-async-metric/")

        async def get_response(_request):
            return HttpResponse("ok")

        middleware = PrometheusRequestMetricsMiddleware(get_response)
        self.assertTrue(iscoroutinefunction(middleware))
        response = await middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(PROMETHEUS_ENABLED=True)
    def test_exception_is_counted_and_reraised(self):
        request = RequestFactory().get("/failing-metric/")
        counter = get_metrics().http_exceptions.labels(
            method="GET",
            route="__not_found__",
            exception="RuntimeError",
        )
        before = counter._value.get()

        def get_response(_request):
            raise RuntimeError("boom")

        middleware = PrometheusRequestMetricsMiddleware(get_response)
        with self.assertRaises(RuntimeError):
            middleware(request)

        self.assertEqual(counter._value.get(), before + 1)
        self.assertTrue(request._prometheus_exception_recorded)

    @override_settings(PROMETHEUS_ENABLED=False)
    def test_disabled_metrics_do_not_register_request(self):
        request = RequestFactory().get("/disabled-metric/")
        middleware = PrometheusRequestMetricsMiddleware(
            lambda _request: HttpResponse("ok")
        )
        response = middleware(request)
        self.assertEqual(response.status_code, 200)


class PrometheusExporterViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.config = PrometheusConfiguration.model_validate(
            {
                "use_prometheus": True,
                "namespace": "devixa",
                "require_auth": True,
                "metrics_token": "strong-test-token",
                "metrics_allowed_ips": [],
            }
        )

    @override_settings(PROMETHEUS_ENABLED=True)
    async def test_metrics_endpoint_accepts_bearer_token(self):
        request = self.factory.get(
            "/metrics/",
            HTTP_AUTHORIZATION="Bearer strong-test-token",
        )
        with override_settings(PROMETHEUS_CONFIG=self.config):
            response = await prometheus_metrics(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn(b"devixa_http_requests_total", response.content)

    @override_settings(PROMETHEUS_ENABLED=True)
    async def test_metrics_endpoint_hides_itself_without_credentials(self):
        request = self.factory.get("/metrics/")
        with override_settings(PROMETHEUS_CONFIG=self.config):
            with self.assertRaises(Http404):
                await prometheus_metrics(request)

    @override_settings(PROMETHEUS_ENABLED=False)
    async def test_metrics_endpoint_is_not_available_when_disabled(self):
        request = self.factory.get("/metrics/")
        with self.assertRaises(Http404):
            await prometheus_metrics(request)

    def test_single_process_exporter_uses_default_registry(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            registry = build_registry()
        self.assertIsNotNone(registry)
