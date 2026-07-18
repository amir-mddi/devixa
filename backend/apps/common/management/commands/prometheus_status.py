from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from backend.apps.common.observability.prometheus.exporter import render_metrics


class Command(BaseCommand):
    help = "Validate Prometheus configuration and render the current registry."

    def handle(self, *args, **options):
        del args, options
        config = settings.PROMETHEUS_CONFIG
        if not settings.PROMETHEUS_ENABLED:
            self.stdout.write(
                self.style.WARNING(
                    "Prometheus is disabled. Set USE_PROMETHEUS=true to enable it."
                )
            )
            return

        multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "").strip()
        if multiprocess_dir:
            path = Path(multiprocess_dir)
            if not path.is_dir():
                raise CommandError(
                    "PROMETHEUS_MULTIPROC_DIR does not exist: " f"{multiprocess_dir}"
                )
            if not os.access(path, os.W_OK):
                raise CommandError(
                    "PROMETHEUS_MULTIPROC_DIR is not writable: " f"{multiprocess_dir}"
                )

        try:
            payload = render_metrics()
        except Exception as exc:
            raise CommandError(f"Unable to render Prometheus metrics: {exc}") from exc

        auth_mode = "disabled" if not config.require_auth else "token/IP allowlist"
        self.stdout.write(
            self.style.SUCCESS(
                "Prometheus configuration is valid. "
                f"Rendered {len(payload)} bytes; auth={auth_mode}; "
                f"namespace={config.namespace}."
            )
        )
