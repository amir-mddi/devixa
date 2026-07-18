from __future__ import annotations

from importlib import import_module

from django.apps import AppConfig
from django.conf import settings


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.common"

    def ready(self) -> None:
        if getattr(settings, "PROMETHEUS_ENABLED", False):
            # Register collectors and signal receivers only after Django settings
            # and app loading are ready.
            from backend.apps.common.observability.prometheus.metrics import get_metrics

            get_metrics()
            import_module("backend.apps.common.observability.prometheus.signals")
