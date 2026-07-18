from backend.apps.common.utils.common_utils import CommonUtils
from functools import wraps

from backend.apps.common.observability.sentry import SentryMonitoringAdapter

logger = CommonUtils.get_project_logger(__name__)


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
                    SentryMonitoringAdapter.capture_exception(exc)

                if raise_error:
                    raise

                return default_return

        return decorated

    return decorator
