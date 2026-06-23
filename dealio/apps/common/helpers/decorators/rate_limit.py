from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse

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
    if key is None:
        return False

    count = cache.get(key, 0)

    if count >= limit:
        return False

    added = cache.add(key, 1, timeout=period)

    if not added:
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=period)

    return True


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
                    return JsonResponse(
                        {
                            "detail": "Could not identify client for rate limiting.",
                            "waiting_time": period,
                        },
                        status=400,
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
                return JsonResponse(
                    {
                        "detail": "Too many requests. Try again later.",
                        "waiting_time": get_cache_ttl(key, period),
                    },
                    status=429,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
