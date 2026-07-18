from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import sentry_sdk


class SentryMonitoringAdapter:
    """Small provider boundary for optional manual Sentry reporting.

    Django and Celery integrations automatically capture unhandled failures.
    Use this adapter only for exceptions that are intentionally swallowed or
    for adding explicit context around an important workflow.
    """

    @staticmethod
    def is_enabled() -> bool:
        return sentry_sdk.is_initialized()

    @classmethod
    def capture_exception(
        cls,
        exception: BaseException,
        *,
        tags: Mapping[str, str | int | float | bool] | None = None,
        contexts: Mapping[str, Mapping[str, Any]] | None = None,
        extras: Mapping[str, Any] | None = None,
    ) -> str | None:
        if not cls.is_enabled():
            return None

        with sentry_sdk.new_scope() as scope:
            for key, value in (tags or {}).items():
                scope.set_tag(key, value)
            for key, value in (contexts or {}).items():
                scope.set_context(key, dict(value))
            for key, value in (extras or {}).items():
                scope.set_extra(key, value)
            event_id = sentry_sdk.capture_exception(exception)
        return str(event_id) if event_id else None

    @classmethod
    def capture_message(
        cls,
        message: str,
        *,
        level: str = "info",
        tags: Mapping[str, str | int | float | bool] | None = None,
    ) -> str | None:
        if not cls.is_enabled():
            return None

        with sentry_sdk.new_scope() as scope:
            for key, value in (tags or {}).items():
                scope.set_tag(key, value)
            event_id = sentry_sdk.capture_message(message, level=level)
        return str(event_id) if event_id else None

    @staticmethod
    def flush(timeout_seconds: float = 2.0) -> None:
        if sentry_sdk.is_initialized():
            sentry_sdk.flush(timeout=timeout_seconds)
