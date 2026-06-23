
from django.conf import settings
from django.core.checks import Error, register
from rest_framework.permissions import BasePermission


@register()
def check_default_permission_cls(app_configs, **kwargs):
    errors = []

    permission_cls = getattr(settings, "DEFAULT_PERMISSION_CLS", None)

    if permission_cls is None:
        errors.append(
            Error(
                "DEFAULT_PERMISSION_CLS must not be None.",
                hint="Set DEFAULT_PERMISSION_CLS in settings.py",
                id="dealio.E001",
            )
        )
        return errors

    if not isinstance(permission_cls, type):
        errors.append(
            Error(
                "DEFAULT_PERMISSION_CLS must be a class, not an instance.",
                hint="Use DEFAULT_PERMISSION_CLS = class , not class().",
                id="dealio.E002",
            )
        )
        return errors

    if not issubclass(permission_cls, BasePermission):
        errors.append(
            Error(
                "DEFAULT_PERMISSION_CLS must inherit from rest_framework.permissions.BasePermission.",
                hint="Make your permission class inherit from BasePermission.",
                id="dealio.E003",
            )
        )

    return errors