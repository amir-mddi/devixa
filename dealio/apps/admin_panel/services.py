from django.core.exceptions import PermissionDenied

from dealio.apps.admin_panel.value_objects import AdminPanelMessageVO


class AdminPanelPermissionService:
    ADMIN_ROLE_SYMBOLS = frozenset({"admin", "super_admin"})

    @classmethod
    def has_access(cls, user) -> bool:
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser or user.is_staff:
            return True
        role = getattr(user, "role", None)
        return str(getattr(role, "symbol", "") or "").lower() in cls.ADMIN_ROLE_SYMBOLS

    @classmethod
    def ensure_access(cls, user) -> None:
        if not cls.has_access(user):
            raise PermissionDenied(AdminPanelMessageVO.PERMISSION_DENIED.value)
