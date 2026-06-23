from django.contrib.auth import get_user_model

from dealio.apps.accounts.models import Role
from dealio.apps.common.helpers.metaclasses.singleton import Singleton

User = get_user_model()


class PostgresAdapter(metaclass=Singleton):
    @staticmethod
    def fetch_role_base_id(id):
        return Role.objects.get(id=id)

    @staticmethod
    def fetch_user_base_phone_number(phone_number):
        return User.objects.get(phone_number=phone_number)
