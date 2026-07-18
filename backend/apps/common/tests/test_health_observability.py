from __future__ import annotations

from unittest import mock

from django.test import (
    RequestFactory,
    SimpleTestCase,
    TransactionTestCase,
    override_settings,
)

from backend.apps.common.observability.health.adapters import BaseHealthCheckAdapter
from backend.apps.common.observability.health.dtos import (
    HealthCheckResultDTO,
    HealthReportDTO,
)
from backend.apps.common.observability.health.enums import HealthStatusEnum
from backend.apps.common.observability.health.logic import HealthCheckLogic
from backend.apps.common.observability.health.views import liveness, readiness


class StubHealthCheck(BaseHealthCheckAdapter):
    def __init__(self, *, name: str, should_fail: bool = False):
        super().__init__(timeout_seconds=0.5)
        self.name = name
        self._should_fail = should_fail

    async def _check(self) -> None:
        if self._should_fail:
            raise RuntimeError("dependency unavailable")


class HealthCheckLogicTests(SimpleTestCase):
    async def test_readiness_is_healthy_when_all_critical_checks_pass(self):
        report = await HealthCheckLogic(
            checks=(StubHealthCheck(name="database"),)
        ).readiness()

        self.assertTrue(report.healthy)
        self.assertEqual(report.status, HealthStatusEnum.HEALTHY)

    async def test_readiness_fails_when_a_critical_check_fails(self):
        report = await HealthCheckLogic(
            checks=(StubHealthCheck(name="database", should_fail=True),)
        ).readiness()

        self.assertFalse(report.healthy)
        self.assertEqual(report.status, HealthStatusEnum.UNHEALTHY)
        self.assertNotIn("dependency unavailable", str(report.as_public_dict()))


class HealthViewTests(SimpleTestCase):
    @override_settings(HEALTH_CHECKS_ENABLED=True)
    async def test_liveness_does_not_check_dependencies(self):
        response = await liveness(RequestFactory().get("/health/live/"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "alive"})

    @override_settings(HEALTH_CHECKS_ENABLED=True)
    async def test_readiness_returns_503_for_failed_critical_dependency(self):
        report = HealthReportDTO(
            status=HealthStatusEnum.UNHEALTHY,
            checks=(
                HealthCheckResultDTO(
                    name="database",
                    status=HealthStatusEnum.UNHEALTHY,
                    duration_seconds=0.01,
                ),
            ),
        )
        request = RequestFactory().get("/health/ready/")
        with mock.patch(
            "backend.apps.common.observability.health.views."
            "HealthCheckLogic.readiness",
            new=mock.AsyncMock(return_value=report),
        ):
            response = await readiness(request)

        self.assertEqual(response.status_code, 503)
        self.assertIn("no-store", response["Cache-Control"])


class HealthEndpointIntegrationTests(TransactionTestCase):
    async def test_readiness_checks_test_database_and_cache(self):
        response = await self.async_client.get("/health/ready/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["checks"]["database"]["status"], "healthy")
        self.assertEqual(payload["checks"]["cache"]["status"], "healthy")
