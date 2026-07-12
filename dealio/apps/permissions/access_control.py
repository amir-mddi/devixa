from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission

from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.shared.initial_data.initial_data.intial_access import InitialAccessCache

logger = CommonUtils.get_project_logger(__name__)


class AccessLimitPermission(BasePermission):
    """Role/access permission that trusts only the authenticated database user.

    JWT claims are intentionally not decoded here. DRF authentication verifies the
    token first and exposes the current user, whose role is the source of truth.
    """

    @classmethod
    def config(cls, request, view_name):
        user = getattr(request, "user", None)
        role = getattr(user, "role", None) if user and user.is_authenticated else None
        user_group = str(getattr(role, "symbol", "") or "")
        pattern = f"{user_group}|{view_name}|{request.method.lower()}|"

        permissions = getattr(settings, "PERMISSIONS", None)
        if not permissions:
            permissions = InitialAccessCache.initial_accesses()
            settings.PERMISSIONS = permissions

        return user, pattern, permissions, user_group

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        try:
            user, pattern, permissions, user_group = self.config(
                request,
                view.__class__.__name__,
            )
            if not user or not user.is_authenticated or not user.is_active:
                return False
            if user.is_superuser:
                return True
            if not user_group:
                return False
            return any(
                pattern + scope in permissions
                for scope in ("any", "self")
            )
        except ObjectDoesNotExist:
            logger.warning("Access check failed because the authenticated user no longer exists.")
        except Exception:
            logger.exception("Unexpected access-control failure.")
        return False

    @classmethod
    def has_access_to_action(cls, view, request):
        user, pattern, permissions, _ = cls.config(
            request,
            view.__class__.__name__,
        )
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (user.is_superuser or pattern + "any" in permissions)
        )
