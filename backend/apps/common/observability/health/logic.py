from __future__ import annotations

import asyncio

from django.conf import settings

from .adapters import (
    BaseHealthCheckAdapter,
    CacheHealthCheckAdapter,
    CeleryBrokerHealthCheckAdapter,
    DatabaseHealthCheckAdapter,
)
from .dtos import HealthReportDTO
from .enums import HealthStatusEnum


class HealthCheckLogic:
    """Build and execute dependency checks without coupling views to providers."""

    def __init__(self, checks: tuple[BaseHealthCheckAdapter, ...] | None = None):
        self._checks = checks if checks is not None else self._build_checks()

    @staticmethod
    def _build_checks() -> tuple[BaseHealthCheckAdapter, ...]:
        config = settings.HEALTH_CHECK_CONFIG
        checks: list[BaseHealthCheckAdapter] = []

        if config.check_database:
            checks.append(
                DatabaseHealthCheckAdapter(
                    alias=config.database_alias,
                    timeout_seconds=config.timeout_seconds,
                )
            )
        if config.check_cache:
            checks.append(
                CacheHealthCheckAdapter(
                    alias=config.cache_alias,
                    timeout_seconds=config.timeout_seconds,
                )
            )
        if config.check_celery_broker:
            checks.append(
                CeleryBrokerHealthCheckAdapter(
                    timeout_seconds=config.timeout_seconds,
                )
            )
        return tuple(checks)

    async def readiness(self) -> HealthReportDTO:
        results = tuple(
            await asyncio.gather(*(check.check() for check in self._checks))
        )
        healthy = all(result.healthy or not result.critical for result in results)
        return HealthReportDTO(
            status=(
                HealthStatusEnum.HEALTHY if healthy else HealthStatusEnum.UNHEALTHY
            ),
            checks=results,
        )
