from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError

from dealio.apps.accounts.models import Role
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.core_models.dtos.setup_config import general_config
from dealio.apps.core_models.vo.common_vo import UserRoleVO

logger = CommonUtils.get_project_logger(__name__)


class Command(BaseCommand):
    help = "Create the initial superuser from configured environment values."

    def handle(self, *args, **options):
        created = self.create_superuser()
        message = "Initial superuser created." if created else "Initial superuser already exists."
        self.stdout.write(self.style.SUCCESS(message))

    @staticmethod
    def create_superuser(
        username=general_config.admin_username,
        email=general_config.admin_email,
        password=general_config.admin_password,
        phone_number=general_config.admin_phone_number,
    ) -> bool:
        username = str(username or "").strip()
        email = str(email or "").strip().lower()
        password = str(password or "")
        phone_number = str(phone_number or "").strip() or None
        if not username or not email or not password:
            raise CommandError(
                "DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and "
                "DJANGO_SUPERUSER_PASSWORD must be configured."
            )

        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            logger.info("Initial superuser already exists.")
            return False

        candidate = User(username=username, email=email, phone_number=phone_number)
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError("Configured superuser password is not strong enough.") from exc

        role, _ = Role.objects.get_or_create(
            symbol=UserRoleVO.ADMIN,
            defaults={"name": "مدیر سیستم"},
        )
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            role=role,
        )
        logger.info("Initial superuser created successfully.")
        return True
