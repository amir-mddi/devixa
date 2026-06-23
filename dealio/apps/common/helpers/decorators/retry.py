import time
import logging
from functools import wraps

logger = logging.getLogger("dealio")


def retry(
    tries=3,
    delay=0,
    backoff=2,
    max_delay=60,
    exceptions=(Exception,),
    raise_error=True,
    default_return=None,
):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, tries + 1):
                try:
                    return f(*args, **kwargs)

                except exceptions as exc:
                    last_exception = exc

                    logger.exception(
                        "Error occurred in %s.%s attempt=%s/%s error=%r",
                        f.__module__,
                        f.__qualname__,
                        attempt,
                        tries,
                        str(exc),
                    )

                    if attempt == tries:
                        break

                    if current_delay > 0:
                        time.sleep(current_delay)
                        current_delay = min(current_delay * backoff, max_delay)

            if raise_error and last_exception is not None:
                raise last_exception

            return default_return

        return f_retry

    return deco_retry

