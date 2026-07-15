from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from backend.apps.admin_panel.repositories import AdminPanelRepository
from backend.apps.admin_panel.value_objects import AdminPanelMessageVO


class AdminUserLogic:
    def __init__(self, repository: AdminPanelRepository | None = None):
        self.repository = repository or AdminPanelRepository()

    def list_users(self, *, search: str = "", role_id: str = "", active: str = ""):
        return self.repository.list_users(search=search, role_id=role_id, active=active)

    def get_user(self, user_id, *, actor=None):
        user = self.repository.get_user(user_id)
        if actor is not None:
            self._ensure_manageable(actor=actor, user=user)
        return user

    def list_roles(self, *, actor=None):
        roles = self.repository.list_roles()
        if actor is None or actor.is_superuser:
            return roles
        return [
            role
            for role in roles
            if str(role.symbol or "").strip().lower() not in {"admin", "super_admin"}
        ]

    @transaction.atomic
    def create_user(self, *, actor, dto):
        self._validate_unique_fields(dto=dto)
        role = self.repository.get_role(dto.role_id)
        self._ensure_can_assign_access(actor=actor, role=role, is_staff=dto.is_staff)
        user = self.repository.create_user(dto=dto, role=role)
        user.user_created_object = actor
        user.user_updated_object = actor
        user.save(
            update_fields=["user_created_object", "user_updated_object", "updated_at"]
        )
        return user

    @transaction.atomic
    def update_user(self, *, actor, dto):
        user = self.repository.get_user(dto.user_id)
        if user.id == actor.id and not dto.is_active:
            raise ValidationError(AdminPanelMessageVO.CANNOT_DEACTIVATE_SELF.value)
        self._ensure_manageable(actor=actor, user=user)
        self._validate_unique_fields(dto=dto, exclude_user_id=user.id)
        role = self.repository.get_role(dto.role_id)
        self._ensure_can_assign_access(actor=actor, role=role, is_staff=dto.is_staff)
        return self.repository.update_user(user=user, dto=dto, role=role, actor=actor)

    def toggle_user(self, *, actor, user_id):
        user = self.repository.get_user(user_id)
        if user.id == actor.id and user.is_active:
            raise ValidationError(AdminPanelMessageVO.CANNOT_DEACTIVATE_SELF.value)
        self._ensure_manageable(actor=actor, user=user)
        return self.repository.set_user_active(
            user=user,
            is_active=not user.is_active,
            actor=actor,
        )

    def delete_user(self, *, actor, user_id):
        user = self.repository.get_user(user_id)
        if user.id == actor.id:
            raise ValidationError(AdminPanelMessageVO.CANNOT_DELETE_SELF.value)
        self._ensure_manageable(actor=actor, user=user)
        return self.repository.soft_delete_user(user=user, actor=actor)

    @staticmethod
    def _ensure_manageable(*, actor, user):
        role_symbol = (
            str(getattr(getattr(user, "role", None), "symbol", "") or "")
            .strip()
            .lower()
        )
        is_privileged = (
            user.is_superuser
            or user.is_staff
            or role_symbol in {"admin", "super_admin"}
        )
        if is_privileged and not actor.is_superuser:
            raise PermissionDenied(
                AdminPanelMessageVO.CANNOT_MANAGE_PRIVILEGED_USER.value
            )

    @staticmethod
    def _ensure_can_assign_access(*, actor, role, is_staff: bool):
        role_symbol = str(getattr(role, "symbol", "") or "").strip().lower()
        if not actor.is_superuser and (
            is_staff or role_symbol in {"admin", "super_admin"}
        ):
            raise ValidationError(
                AdminPanelMessageVO.CANNOT_GRANT_PRIVILEGED_ACCESS.value
            )

    def _validate_unique_fields(self, *, dto, exclude_user_id=None):
        if self.repository.username_exists(
            username=dto.username,
            exclude_user_id=exclude_user_id,
        ):
            raise ValidationError({"username": "این نام کاربری قبلاً ثبت شده است."})
        if self.repository.email_exists(
            email=dto.email,
            exclude_user_id=exclude_user_id,
        ):
            raise ValidationError({"email": "این ایمیل قبلاً ثبت شده است."})
        if self.repository.phone_exists(
            phone_number=dto.phone_number,
            exclude_user_id=exclude_user_id,
        ):
            raise ValidationError(
                {"phone_number": "این شماره موبایل قبلاً ثبت شده است."}
            )
