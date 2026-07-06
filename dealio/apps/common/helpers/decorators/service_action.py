import hashlib
import json
from dealio.apps.common.utils.common_utils import CommonUtils
import time
from functools import wraps

import sentry_sdk
from django.core.cache import cache

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
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            started_at = time.perf_counter()

            cache_key = None

            if use_cache:
                cache_key = make_cache_key(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    prefix=cache_key_prefix,
                )

                cached_value = cache.get(cache_key, CACHE_MISS)

                if cached_value is not CACHE_MISS:
                    return cached_value

            current_delay = retry_delay
            last_exception = None

            try:
                for attempt in range(1, retry_tries + 1):
                    try:
                        result = func(*args, **kwargs)

                        if use_cache:
                            if result is not None or cache_none:
                                cache.set(
                                    cache_key,
                                    result,
                                    timeout=cache_timeout,
                                )

                        return result

                    except retry_exceptions as exc:
                        last_exception = exc

                        logger.exception(
                            "Exception in %s.%s attempt=%s/%s args=%r kwargs=%r",
                            func.__module__,
                            func.__qualname__,
                            attempt,
                            retry_tries,
                            args,
                            kwargs,
                        )

                        if send_to_sentry:
                            sentry_sdk.capture_exception(exc)

                        if attempt == retry_tries:
                            break

                        if current_delay > 0:
                            time.sleep(current_delay)
                            current_delay = min(
                                current_delay * retry_backoff,
                                retry_max_delay,
                            )

                if raise_error and last_exception is not None:
                    raise last_exception

                return default_return

            finally:
                if log_time:
                    duration = time.perf_counter() - started_at

                    logger.info(
                        "Function %s.%s executed in %.4f seconds",
                        func.__module__,
                        func.__qualname__,
                        duration,
                    )

        return wrapper

    return decorator
