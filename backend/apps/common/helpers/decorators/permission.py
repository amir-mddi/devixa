from functools import wraps

from django.http import JsonResponse

from backend.apps.common.utils.common_utils import CommonUtils
from django.conf import settings


def permission_required(
        permission_cls=getattr(settings, "DEFAULT_PERMISSION_CLS", None),
        required=False
):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not required:
                return func(*args, **kwargs)

            if permission_cls is None:
                raise PermissionError()

            perm_instance = permission_cls()

            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)

            view_name = getattr(func, "__class__", type(func)).__name__
            function_name = getattr(func, "__name__", None)

            has_permission = perm_instance.has_permission(request, func)

            if has_permission:
                return func(*args, **kwargs)

            return JsonResponse(
                {
                    "detail": f"You do not have permission to perform this action"},
                status=403,
            )

        return decorated_function

    return decorator
