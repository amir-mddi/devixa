from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from prometheus_client import CollectorRegistry, REGISTRY, generate_latest, multiprocess


def build_registry():
    """Return the correct registry for single- or multi-process deployment."""

    multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "").strip()
    if not multiprocess_dir:
        return REGISTRY

    path = Path(multiprocess_dir)
    if not path.is_dir():
        raise ImproperlyConfigured(
            "PROMETHEUS_MULTIPROC_DIR must point to an existing directory. "
            "Create and wipe it before starting application processes."
        )

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return registry


def render_metrics() -> bytes:
    return generate_latest(build_registry())
