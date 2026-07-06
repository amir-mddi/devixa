import time
from dealio.apps.common.utils.common_utils import CommonUtils
from functools import wraps

logger = CommonUtils.get_project_logger(__name__)


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        started_at = time.perf_counter()

        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - started_at

            instance = args[0] if args else None

            if instance is not None:
                class_name = instance.__class__.__name__
                module_name = instance.__class__.__module__
                function_name = func.__name__
            else:
                class_name = None
                module_name = func.__module__
                function_name = func.__qualname__

            logger.info(
                f"Function {module_name}.{class_name}.{function_name} "
                f"executed in {duration:.4f} seconds"
            )

    return wrapper
