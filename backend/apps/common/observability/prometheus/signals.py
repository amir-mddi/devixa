from __future__ import annotations

import threading
import time

from celery import signals as celery_signals
from django.conf import settings
from django.core.signals import got_request_exception
from django.dispatch import receiver

from .metrics import get_metrics, is_prometheus_enabled
from .middleware import is_excluded_path, resolve_route_label

_task_started_at: dict[str, float] = {}
_task_lock = threading.Lock()


def _celery_metrics_enabled() -> bool:
    config = getattr(settings, "PROMETHEUS_CONFIG", None)
    return is_prometheus_enabled() and bool(
        getattr(config, "enable_celery_metrics", False)
    )


def _task_name(sender=None, task=None, **kwargs) -> str:
    candidate = sender or task
    return str(
        getattr(candidate, "name", None)
        or getattr(candidate, "__name__", None)
        or "unknown"
    )


def _task_id(task_id=None, request=None, **kwargs) -> str | None:
    return str(task_id or getattr(request, "id", "") or "") or None


@receiver(got_request_exception, dispatch_uid="prometheus_request_exception")
def record_request_exception(sender, request, **kwargs):
    del sender
    if (
        not is_prometheus_enabled()
        or request is None
        or is_excluded_path(request.path)
        or getattr(request, "_prometheus_exception_recorded", False)
    ):
        return

    exception = kwargs.get("exception")
    if exception is None:
        import sys

        exception = sys.exc_info()[1]

    get_metrics().http_exceptions.labels(
        method=request.method.upper(),
        route=resolve_route_label(request),
        exception=(exception.__class__.__name__ if exception else "UnknownException"),
    ).inc()
    request._prometheus_exception_recorded = True


@celery_signals.task_prerun.connect(
    weak=False,
    dispatch_uid="prometheus_celery_task_prerun",
)
def record_task_prerun(sender=None, task_id=None, task=None, **kwargs):
    del kwargs
    if not _celery_metrics_enabled():
        return

    name = _task_name(sender=sender, task=task)
    identifier = _task_id(task_id=task_id)
    if identifier:
        with _task_lock:
            _task_started_at[identifier] = time.perf_counter()
    get_metrics().celery_tasks_in_progress.labels(task=name).inc()


@celery_signals.task_postrun.connect(
    weak=False,
    dispatch_uid="prometheus_celery_task_postrun",
)
def record_task_postrun(
    sender=None,
    task_id=None,
    task=None,
    state=None,
    **kwargs,
):
    del kwargs
    if not _celery_metrics_enabled():
        return

    name = _task_name(sender=sender, task=task)
    identifier = _task_id(task_id=task_id)
    started_at = None
    if identifier:
        with _task_lock:
            started_at = _task_started_at.pop(identifier, None)

    metrics = get_metrics()
    metrics.celery_tasks_in_progress.labels(task=name).dec()
    metrics.celery_tasks.labels(task=name, state=str(state or "UNKNOWN").lower()).inc()
    if started_at is not None:
        metrics.celery_task_duration.labels(task=name).observe(
            max(0.0, time.perf_counter() - started_at)
        )


@celery_signals.worker_process_shutdown.connect(
    weak=False,
    dispatch_uid="prometheus_celery_worker_process_shutdown",
)
def mark_celery_process_dead(pid=None, **kwargs):
    del kwargs
    if not _celery_metrics_enabled():
        return

    import os
    from prometheus_client import multiprocess

    multiprocess_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "").strip()
    if multiprocess_dir:
        multiprocess.mark_process_dead(int(pid or os.getpid()))
