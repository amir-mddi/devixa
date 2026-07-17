from __future__ import annotations

import inspect
from functools import wraps

from asgiref.sync import sync_to_async
from django.core.cache import cache

from backend.apps.common.adapters.http_error_response_adapter import (
    HttpErrorResponseAdapter,
)
from backend.apps.common.logic.http_error_logic import RateLimitErrorLogic
from backend.apps.common.utils.common_utils import CommonUtils


def default_rate_limit_key(request, func, *args, **kwargs):
    if request is None:
        return None

    user = getattr(request, "user", None)
    if CommonUtils.is_authenticated_request(request):
        return f"rate_limit:{func.__module__}.{func.__qualname__}:user:{user.pk}"

    ip = CommonUtils.get_client_ip(request)
    if ip:
        return f"rate_limit:{func.__module__}.{func.__qualname__}:ip:{ip}"
    return None


def get_cache_ttl(key, default):
    ttl_func = getattr(cache, "ttl", None)
    if callable(ttl_func):
        ttl = ttl_func(key)
        if isinstance(ttl, int) and ttl > 0:
            return ttl
    return default


async def get_cache_ttl_async(key, default):
    ttl_func = getattr(cache, "ttl", None)
    if not callable(ttl_func):
        return default
    ttl = await sync_to_async(ttl_func, thread_sensitive=True)(key)
    return ttl if isinstance(ttl, int) and ttl > 0 else default


def is_rate_limit_allowed(*, key, limit, period):
    if key is None or limit <= 0 or period <= 0:
        return False

    if cache.add(key, 1, timeout=period):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            if cache.add(key, 1, timeout=period):
                count = 1
            else:
                count = cache.incr(key)
    return count <= limit


async def is_rate_limit_allowed_async(*, key, limit, period):
    if key is None or limit <= 0 or period <= 0:
        return False

    if await cache.aadd(key, 1, timeout=period):
        count = 1
    else:
        try:
            count = await cache.aincr(key)
        except ValueError:
            if await cache.aadd(key, 1, timeout=period):
                count = 1
            else:
                count = await cache.aincr(key)
    return count <= limit


def rate_limit(
    *,
    key_func=None,
    authenticated_limit=100,
    anonymous_limit=20,
    period=60,
    block_if_no_key=True,
):
    """Rate-limit sync and async Django/DRF callables without blocking ASGI.

    ``method_decorator(..., name="dispatch")`` wraps ADRF's regular ``dispatch``
    method even when the selected request handler is async. The runtime check for
    ``view_is_async`` handles that case and returns an awaitable wrapper.
    """

    def decorator(func):
        async def enforce_async(*args, **kwargs):
            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)
            key_builder = key_func or default_rate_limit_key
            if inspect.iscoroutinefunction(key_builder):
                key = await key_builder(request, func, *args, **kwargs)
            else:
                key = await sync_to_async(
                    key_builder,
                    thread_sensitive=True,
                )(request, func, *args, **kwargs)
            if inspect.isawaitable(key):
                key = await key

            if key is None:
                if block_if_no_key:
                    error = RateLimitErrorLogic.client_unknown(waiting_time=period)
                    return HttpErrorResponseAdapter.build(request=request, error=error)
                result = func(*args, **kwargs)
                return await result if inspect.isawaitable(result) else result

            is_authenticated = await sync_to_async(
                CommonUtils.is_authenticated_request,
                thread_sensitive=True,
            )(request)
            limit = authenticated_limit if is_authenticated else anonymous_limit
            allowed = await is_rate_limit_allowed_async(
                key=key,
                limit=limit,
                period=period,
            )
            if not allowed:
                error = RateLimitErrorLogic.exceeded(
                    waiting_time=await get_cache_ttl_async(key, period),
                )
                return HttpErrorResponseAdapter.build(request=request, error=error)

            result = func(*args, **kwargs)
            return await result if inspect.isawaitable(result) else result

        if inspect.iscoroutinefunction(func):
            return wraps(func)(enforce_async)

        @wraps(func)
        def sync_or_async_wrapper(*args, **kwargs):
            instance = args[0] if args else None
            if getattr(instance, "view_is_async", False):
                return enforce_async(*args, **kwargs)

            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)
            key = (
                key_func(request, func, *args, **kwargs)
                if key_func
                else default_rate_limit_key(request, func, *args, **kwargs)
            )
            if key is None:
                if block_if_no_key:
                    error = RateLimitErrorLogic.client_unknown(waiting_time=period)
                    return HttpErrorResponseAdapter.build(request=request, error=error)
                return func(*args, **kwargs)

            limit = (
                authenticated_limit
                if CommonUtils.is_authenticated_request(request)
                else anonymous_limit
            )
            if not is_rate_limit_allowed(key=key, limit=limit, period=period):
                error = RateLimitErrorLogic.exceeded(
                    waiting_time=get_cache_ttl(key, period),
                )
                return HttpErrorResponseAdapter.build(request=request, error=error)
            return func(*args, **kwargs)

        return sync_or_async_wrapper

    return decorator
