from django.contrib.auth import get_user_model

from dealio.apps.accounts.models import Role
from dealio.apps.accounts.vo.auth_vo import (
    AccountDefaultRoleVO,
    AccountRoleFieldVO,
    AccountUserFieldVO,
    AccountUserQueryLookupVO,
)
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.core_models.vo.common_vo import UserRoleVO

User = get_user_model()


class PostgresAdapter(metaclass=Singleton):
    @staticmethod
    def fetch_role_base_id(id):
        return Role.objects.get(id=id)

    @staticmethod
    def fetch_user_base_phone_number(phone_number):
        return User.objects.get(phone_number=phone_number)

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
