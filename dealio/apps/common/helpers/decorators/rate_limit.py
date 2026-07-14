from functools import wraps

from django.core.cache import cache

from dealio.apps.common.adapters.http_error_response_adapter import (
    HttpErrorResponseAdapter,
)
from dealio.apps.common.logic.http_error_logic import RateLimitErrorLogic
from dealio.apps.common.utils.common_utils import CommonUtils


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


def is_rate_limit_allowed(*, key, limit, period):
    if key is None or limit <= 0 or period <= 0:
        return False

    if cache.add(key, 1, timeout=period):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            # The key may have expired between add() and incr(). Retry once.
            if cache.add(key, 1, timeout=period):
                count = 1
            else:
                count = cache.incr(key)

    return count <= limit


def rate_limit(
        *,
        key_func=None,
        authenticated_limit=100,
        anonymous_limit=20,
        period=60,
        block_if_no_key=True,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)

            key = (
                key_func(request, func, *args, **kwargs)
                if key_func
                else default_rate_limit_key(request, func, *args, **kwargs)
            )

            if key is None:
                if block_if_no_key:
                    error = RateLimitErrorLogic.client_unknown(waiting_time=period)
                    return HttpErrorResponseAdapter.build(
                        request=request,
                        error=error,
                    )

                return func(*args, **kwargs)

            limit = (
                authenticated_limit
                if CommonUtils.is_authenticated_request(request)
                else anonymous_limit
            )

            allowed = is_rate_limit_allowed(
                key=key,
                limit=limit,
                period=period,
            )

            if not allowed:
                error = RateLimitErrorLogic.exceeded(
                    waiting_time=get_cache_ttl(key, period),
                )
                return HttpErrorResponseAdapter.build(
                    request=request,
                    error=error,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
