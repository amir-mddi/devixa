from functools import wraps

from django.http import JsonResponse
from rest_framework.exceptions import MethodNotAllowed

from dealio.apps.common.utils.common_utils import CommonUtils

special_character_for_skip = "*"


def allowed_methods(methods):
    allowed = {method.upper() for method in methods}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if special_character_for_skip in allowed:
                return func(*args, **kwargs)
            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)
            method = request.method.upper()

            if method not in allowed:
                return JsonResponse(
                    {"detail": f"Method {method} not allowed."},
                    status=405,
                )
                # raise MethodNotAllowed(method)

            return func(*args, **kwargs)

        return wrapper

    return decorator
