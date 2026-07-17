from __future__ import annotations

import asyncio
import inspect
import time
from functools import wraps

from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


def retry(
    tries=3,
    delay=0,
    backoff=2,
    max_delay=60,
    exceptions=(Exception,),
    raise_error=True,
    default_return=None,
):
    """Retry decorator that preserves native sync or async execution."""

    def deco_retry(func):
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_retry(*args, **kwargs):
                current_delay = delay
                last_exception = None

                for attempt in range(1, tries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        last_exception = exc
                        _log_failure(func, attempt, tries, exc)
                        if attempt == tries:
                            break
                        if current_delay > 0:
                            await asyncio.sleep(current_delay)
                            current_delay = min(
                                current_delay * backoff,
                                max_delay,
                            )

                if raise_error and last_exception is not None:
                    raise last_exception
                return default_return

            return async_retry

        @wraps(func)
        def sync_retry(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    _log_failure(func, attempt, tries, exc)
                    if attempt == tries:
                        break
                    if current_delay > 0:
                        time.sleep(current_delay)
                        current_delay = min(current_delay * backoff, max_delay)

            if raise_error and last_exception is not None:
                raise last_exception
            return default_return

        return sync_retry

    return deco_retry


def _log_failure(func, attempt: int, tries: int, exc: Exception) -> None:
    logger.exception(
        "Error occurred in %s.%s attempt=%s/%s error=%r",
        func.__module__,
        func.__qualname__,
        attempt,
        tries,
        str(exc),
    )
