from __future__ import annotations

import logging
from pathlib import Path

import sentry_sdk
from django.core.exceptions import DisallowedHost, ImproperlyConfigured
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.scrubber import EventScrubber

from backend.apps.common.observability.sentry.filters import (
    build_before_send,
    build_before_send_transaction,
)
from backend.apps.common.observability.sentry.value_objects import (
    SentrySensitiveFieldVO,
)
from backend.apps.core_models.dtos.setup_config import SentryConfiguration


def initialize_sentry(
    config: SentryConfiguration,
    *,
    project_root: Path,
) -> bool:
    """Initialize Sentry once and return whether monitoring is enabled."""

    if not config.use_sentry:
        return False

    if not config.dsn:
        raise ImproperlyConfigured(
            "SENTRY_DSN is required when USE_SENTRY=true."
        )

    if sentry_sdk.is_initialized():
        return True

    integrations = [
        DjangoIntegration(
            transaction_style=config.transaction_style,
            middleware_spans=config.middleware_spans,
            signals_spans=config.signals_spans,
            cache_spans=config.cache_spans,
            db_transaction_spans=config.db_transaction_spans,
        ),
        CeleryIntegration(
            propagate_traces=config.celery_propagate_traces,
            monitor_beat_tasks=config.monitor_celery_beat_tasks,
        ),
        RedisIntegration(max_data_size=config.redis_max_data_size),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
            sentry_logs_level=logging.INFO,
        ),
    ]

    sentry_sdk.init(
        dsn=config.dsn,
        environment=config.environment,
        release=config.release or None,
        server_name=config.server_name or None,
        integrations=integrations,
        sample_rate=config.error_sample_rate,
        traces_sample_rate=(
            config.traces_sample_rate if config.enable_tracing else None
        ),
        profiles_sample_rate=(
            config.profiles_sample_rate
            if config.enable_tracing and config.profiles_sample_rate > 0
            else None
        ),
        send_default_pii=config.send_default_pii,
        event_scrubber=EventScrubber(
            denylist=list(SentrySensitiveFieldVO.DEFAULT_DENYLIST),
            recursive=True,
            send_default_pii=config.send_default_pii,
        ),
        ignore_errors=[DisallowedHost, BrokenPipeError, ConnectionResetError],
        before_send=build_before_send(config.ignored_path_prefixes),
        before_send_transaction=build_before_send_transaction(
            config.ignored_path_prefixes
        ),
        enable_logs=config.enable_logs,
        debug=config.debug,
        attach_stacktrace=config.attach_stacktrace,
        include_local_variables=config.include_local_variables,
        max_request_body_size=config.max_request_body_size,
        max_breadcrumbs=config.max_breadcrumbs,
        shutdown_timeout=config.shutdown_timeout_seconds,
        trace_propagation_targets=config.trace_propagation_targets,
        strict_trace_continuation=config.strict_trace_continuation,
        project_root=str(project_root),
        in_app_include=["backend"],
    )
    return True
