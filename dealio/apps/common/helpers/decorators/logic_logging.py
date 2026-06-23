import logging
from functools import wraps

import sentry_sdk

logger = logging.getLogger("dealio")


def logic_logging(*, raise_error=True, default_return=None, send_to_sentry=True):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.exception(
                    "Exception in %s.%s with args=%r kwargs=%r",
                    func.__module__,
                    func.__qualname__,
                    args,
                    kwargs,
                )

                if send_to_sentry:
                    sentry_sdk.capture_exception(exc)

                if raise_error:
                    raise

                return default_return

        return decorated

    return decorator