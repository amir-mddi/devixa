from __future__ import annotations

import asyncio
import time
import uuid
from abc import ABC, abstractmethod

from asgiref.sync import sync_to_async
from celery import current_app
from django.core.cache import caches
from django.db import connections

from backend.apps.common.observability.prometheus import PrometheusMetricsAdapter

from .dtos import HealthCheckResultDTO
from .enums import HealthStatusEnum
from .value_objects import HealthDependencyVO


class BaseHealthCheckAdapter(ABC):
    name: str
    critical: bool = True

    def __init__(self, *, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds

    async def check(self) -> HealthCheckResultDTO:
        started_at = time.perf_counter()
        healthy = False
        try:
            await asyncio.wait_for(
                self._check(),
                timeout=self._timeout_seconds,
            )
            healthy = True
        except Exception:
            healthy = False

        duration = max(0.0, time.perf_counter() - started_at)
        PrometheusMetricsAdapter.observe_health(
            dependency=self.name,
            healthy=healthy,
            duration_seconds=duration,
        )
        return HealthCheckResultDTO(
            name=self.name,
            status=(
                HealthStatusEnum.HEALTHY if healthy else HealthStatusEnum.UNHEALTHY
            ),
            duration_seconds=duration,
            critical=self.critical,
        )

    @abstractmethod
    async def _check(self) -> None:
        raise NotImplementedError


class DatabaseHealthCheckAdapter(BaseHealthCheckAdapter):
    name = HealthDependencyVO.DATABASE

    def __init__(self, *, alias: str, timeout_seconds: float) -> None:
        super().__init__(timeout_seconds=timeout_seconds)
        self._alias = alias

    def _check_sync(self) -> None:
        connection = connections[self._alias]
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    async def _check(self) -> None:
        await sync_to_async(
            self._check_sync,
            thread_sensitive=True,
        )()


class CacheHealthCheckAdapter(BaseHealthCheckAdapter):
    name = HealthDependencyVO.CACHE

    def __init__(self, *, alias: str, timeout_seconds: float) -> None:
        super().__init__(timeout_seconds=timeout_seconds)
        self._cache = caches[alias]

    async def _check(self) -> None:
        key = f"health-check:{uuid.uuid4().hex}"
        expected = uuid.uuid4().hex

        if all(
            callable(getattr(self._cache, method, None))
            for method in ("aset", "aget", "adelete")
        ):
            await self._cache.aset(key, expected, timeout=10)
            actual = await self._cache.aget(key)
            await self._cache.adelete(key)
        else:
            actual = await sync_to_async(
                self._cache_round_trip,
                thread_sensitive=True,
            )(key, expected)

        if actual != expected:
            raise RuntimeError("Cache round-trip returned an unexpected value.")

    def _cache_round_trip(self, key: str, expected: str) -> str | None:
        self._cache.set(key, expected, timeout=10)
        try:
            return self._cache.get(key)
        finally:
            self._cache.delete(key)


class CeleryBrokerHealthCheckAdapter(BaseHealthCheckAdapter):
    name = HealthDependencyVO.CELERY_BROKER

    @staticmethod
    def _check_sync() -> None:
        connection = current_app.connection_for_read()
        try:
            connection.ensure_connection(max_retries=0)
        finally:
            connection.release()

    async def _check(self) -> None:
        await sync_to_async(
            self._check_sync,
            thread_sensitive=False,
        )()
