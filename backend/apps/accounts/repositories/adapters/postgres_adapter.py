from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from backend.apps.accounts.models import Role
from backend.apps.accounts.vo.auth_vo import (
    AccountDefaultRoleVO,
    AccountRoleFieldVO,
    AccountUserFieldVO,
    AccountUserQueryLookupVO,
)
from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.core_models.vo.common_vo import UserRoleVO

User = get_user_model()


class PostgresAdapter(metaclass=Singleton):
    @staticmethod
    def fetch_role_base_id(role_id):
        return Role.objects.get(id=role_id)

    @staticmethod
    def fetch_user_base_id(user_id):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def fetch_user_base_phone_number(phone_number: str):
        return User.objects.filter(phone_number=phone_number).first()

    @staticmethod
    def fetch_user_base_email(email: str):
        return User.objects.filter(
            **{AccountUserQueryLookupVO.EMAIL_IEXACT.value: email}
        ).first()

    @staticmethod
    def username_exists(username: str) -> bool:
        return User.objects.filter(
            **{AccountUserQueryLookupVO.USERNAME_IEXACT.value: username}
        ).exists()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(
            **{AccountUserQueryLookupVO.EMAIL_IEXACT.value: email}
        ).exists()

    @staticmethod
    def phone_number_used_by_other_user(*, phone_number: str, user_id: str) -> bool:
        return (
            User.objects
            .filter(phone_number=phone_number)
            .exclude(id=user_id)
            .exists()
        )

    @staticmethod
    def get_or_create_default_user_role() -> Role:
        role, _ = Role.objects.get_or_create(
            symbol=UserRoleVO.USER,
            defaults={AccountRoleFieldVO.NAME.value: AccountDefaultRoleVO.NAME.value},
        )
        return role

    def create_user_account(
        self,
        *,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
    ):
        return User.objects.create_user(
            **{
                AccountUserFieldVO.FIRST_NAME.value: first_name,
                AccountUserFieldVO.LAST_NAME.value: last_name,
                AccountUserFieldVO.USERNAME.value: username,
                AccountUserFieldVO.EMAIL.value: email,
                AccountUserFieldVO.PASSWORD.value: password,
                AccountUserFieldVO.ROLE.value: self.get_or_create_default_user_role(),
            }
        )

    @staticmethod
    def update_user_password(*, user, password: str) -> None:
        user.set_password(password)
        user.save(update_fields=[AccountUserFieldVO.PASSWORD.value, "updated_at"])
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for token in outstanding_tokens.iterator():
            BlacklistedToken.objects.get_or_create(token=token)

    @staticmethod
    def mark_phone_number_verified(*, user) -> None:
        user.phone_number_verified = True
        user.save(update_fields=["phone_number_verified"])

    @staticmethod
    def update_and_verify_phone_number(*, user, phone_number: str) -> None:
        # QuerySet.update intentionally bypasses CustomUser.save(), which resets
        # verification whenever the phone number changes. Telegram's own-contact
        # payload proves ownership, so both values must be persisted atomically.
        User.objects.filter(id=user.id).update(
            phone_number=phone_number,
            phone_number_verified=True,
        )
        user.phone_number = phone_number
        user.phone_number_verified = True
