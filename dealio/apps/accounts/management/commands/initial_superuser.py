from dealio.apps.common.utils.common_utils import CommonUtils

from django.contrib.auth import get_user_model

from dealio.apps.accounts.models import Role
from dealio.apps.core_models.dtos.setup_config import general_config
from dealio.apps.core_models.vo.common_vo import UserRoleVO

logger = CommonUtils.get_project_logger(__name__)

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "create superuser"

    def handle(self, *args, **options):
        self.create_superuser()

    @staticmethod
    def create_superuser(username=general_config.admin_username, email=general_config.admin_email,
                         password=general_config.admin_password, phone_number=general_config.admin_phone_number):
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            role, _ = Role.objects.get_or_create(symbol=UserRoleVO.ADMIN)
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                phone_number=phone_number,
                role=role
            )
            logger.info(f"Superuser with username {username} successfully created.")
        else:
            logger.info(f"Superuser with username {username} already exists.")
