from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import time
from functools import wraps

import sentry_sdk
from django.core.cache import cache

from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)
CACHE_MISS = object()


def make_cache_key(func, args, kwargs, prefix="service_action"):
    key_data = {
        "module": func.__module__,
        "name": func.__qualname__,
        "args": args,
        "kwargs": kwargs,
    }
    try:
        raw_key = json.dumps(key_data, sort_keys=True, default=str)
    except TypeError:
        raw_key = str(key_data)
    hashed_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    return f"{prefix}:{func.__module__}.{func.__qualname__}:{hashed_key}"


def service_action(
    *,
    use_cache=False,
    cache_timeout=300,
    cache_none=True,
    cache_key_prefix="service_action_",
    retry_tries=1,
    retry_delay=0,
    retry_backoff=2,
    retry_max_delay=60,
    retry_exceptions=(Exception,),
    raise_error=True,
    default_return=None,
    send_to_sentry=False,
    log_time=False,
):
    """Cross-cutting service decorator with native async support."""

    def decorator(func):
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                started_at = time.perf_counter()
                cache_key = _cache_key(
                    func,
                    args,
                    kwargs,
                    use_cache=use_cache,
                    prefix=cache_key_prefix,
                )
                try:
                    if cache_key:
                        cached_value = await cache.aget(cache_key, CACHE_MISS)
                        if cached_value is not CACHE_MISS:
                            return cached_value

                    result = await _run_async_with_retry(
                        func,
                        args,
                        kwargs,
                        retry_tries=retry_tries,
                        retry_delay=retry_delay,
                        retry_backoff=retry_backoff,
                        retry_max_delay=retry_max_delay,
                        retry_exceptions=retry_exceptions,
                        raise_error=raise_error,
                        default_return=default_return,
                        send_to_sentry=send_to_sentry,
                    )
                    if cache_key and (result is not None or cache_none):
                        await cache.aset(
                            cache_key,
                            result,
                            timeout=cache_timeout,
                        )
                    return result
                finally:
                    _log_duration(func, started_at, enabled=log_time)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            started_at = time.perf_counter()
            cache_key = _cache_key(
                func,
                args,
                kwargs,
                use_cache=use_cache,
                prefix=cache_key_prefix,
            )
            try:
                if cache_key:
                    cached_value = cache.get(cache_key, CACHE_MISS)
                    if cached_value is not CACHE_MISS:
                        return cached_value

                result = _run_sync_with_retry(
                    func,
                    args,
                    kwargs,
                    retry_tries=retry_tries,
                    retry_delay=retry_delay,
                    retry_backoff=retry_backoff,
                    retry_max_delay=retry_max_delay,
                    retry_exceptions=retry_exceptions,
                    raise_error=raise_error,
                    default_return=default_return,
                    send_to_sentry=send_to_sentry,
                )
                if cache_key and (result is not None or cache_none):
                    cache.set(cache_key, result, timeout=cache_timeout)
                return result
            finally:
                _log_duration(func, started_at, enabled=log_time)

        return sync_wrapper

    return decorator


def _cache_key(func, args, kwargs, *, use_cache: bool, prefix: str) -> str | None:
    if not use_cache:
        return None
    return make_cache_key(func=func, args=args, kwargs=kwargs, prefix=prefix)


async def _run_async_with_retry(
    func,
    args,
    kwargs,
    *,
    retry_tries,
    retry_delay,
    retry_backoff,
    retry_max_delay,
    retry_exceptions,
    raise_error,
    default_return,
    send_to_sentry,
):
    current_delay = retry_delay
    last_exception = None
    for attempt in range(1, retry_tries + 1):
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as exc:
            last_exception = exc
            _handle_failure(
                func,
                attempt,
                retry_tries,
                args,
                kwargs,
                exc,
                send_to_sentry=send_to_sentry,
            )
            if attempt == retry_tries:
                break
            if current_delay > 0:
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * retry_backoff, retry_max_delay)
    if raise_error and last_exception is not None:
        raise last_exception
    return default_return


def _run_sync_with_retry(
    func,
    args,
    kwargs,
    *,
    retry_tries,
    retry_delay,
    retry_backoff,
    retry_max_delay,
    retry_exceptions,
    raise_error,
    default_return,
    send_to_sentry,
):
    current_delay = retry_delay
    last_exception = None
    for attempt in range(1, retry_tries + 1):
        try:
            return func(*args, **kwargs)
        except retry_exceptions as exc:
            last_exception = exc
            _handle_failure(
                func,
                attempt,
                retry_tries,
                args,
                kwargs,
                exc,
                send_to_sentry=send_to_sentry,
            )
            if attempt == retry_tries:
                break
            if current_delay > 0:
                time.sleep(current_delay)
                current_delay = min(current_delay * retry_backoff, retry_max_delay)
    if raise_error and last_exception is not None:
        raise last_exception
    return default_return


def _handle_failure(
    func,
    attempt: int,
    tries: int,
    args,
    kwargs,
    exc: Exception,
    *,
    send_to_sentry: bool,
) -> None:
    logger.exception(
        "Exception in %s.%s attempt=%s/%s args=%r kwargs=%r",
        func.__module__,
        func.__qualname__,
        attempt,
        tries,
        args,
        kwargs,
    )
    if send_to_sentry:
        sentry_sdk.capture_exception(exc)


def _log_duration(func, started_at: float, *, enabled: bool) -> None:
    if not enabled:
        return
    logger.info(
        "Function %s.%s executed in %.4f seconds",
        func.__module__,
        func.__qualname__,
        time.perf_counter() - started_at,
    )
