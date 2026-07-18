from __future__ import annotations

from dataclasses import dataclass

from .enums import HealthStatusEnum


@dataclass(frozen=True, slots=True)
class HealthCheckResultDTO:
    name: str
    status: HealthStatusEnum
    duration_seconds: float
    critical: bool = True

    @property
    def healthy(self) -> bool:
        return self.status is HealthStatusEnum.HEALTHY

    def as_public_dict(self) -> dict[str, str | float | bool]:
        return {
            "status": self.status.value,
            "duration_ms": round(self.duration_seconds * 1000, 2),
            "critical": self.critical,
        }


@dataclass(frozen=True, slots=True)
class HealthReportDTO:
    status: HealthStatusEnum
    checks: tuple[HealthCheckResultDTO, ...]

    @property
    def healthy(self) -> bool:
        return self.status is HealthStatusEnum.HEALTHY

    def as_public_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checks": {check.name: check.as_public_dict() for check in self.checks},
        }
