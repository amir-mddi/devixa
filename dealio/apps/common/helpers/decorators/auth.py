from functools import wraps

from django.http import JsonResponse

from dealio.apps.common.utils.common_utils import CommonUtils


def authentication_required(
        *,
        staff_required=False,
        superuser_required=False,
        required=False,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not required:
                return func(*args, **kwargs)

            request = CommonUtils.get_request_from_args_kwargs(*args, **kwargs)
            user = getattr(request, "user", None)

            if user is None or not user.is_authenticated:
                return JsonResponse(
                    {"detail": "Authentication credentials were not provided."},
                    status=401,
                )

            if staff_required and not user.is_staff:
                return JsonResponse(
                    {"detail": "You do not have permission to perform this action."},
                    status=403,
                )

            if superuser_required and not user.is_superuser:
                return JsonResponse(
                    {"detail": "You do not have permission to perform this action."},
                    status=403,
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator
