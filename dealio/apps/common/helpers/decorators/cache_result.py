import hashlib
import json
from dealio.apps.common.utils.common_utils import CommonUtils
from functools import wraps

from django.core.cache import cache

logger = CommonUtils.get_project_logger(__name__)


CACHE_MISS = object()

def make_cache_key(func, args, kwargs, prefix="cache_result"):
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


def cache_result(
    *,
    timeout=300,
    key_prefix="cache_result",
    cache_none=False,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = make_cache_key(
                func=func,
                args=args,
                kwargs=kwargs,
                prefix=key_prefix,
            )

            cached_value = cache.get(cache_key, CACHE_MISS)

            if cached_value is not CACHE_MISS:
                return cached_value

            result = func(*args, **kwargs)

            if result is None and not cache_none:
                return result

            cache.set(cache_key, result, timeout=timeout)

            return result

        return wrapper

    return decorator
