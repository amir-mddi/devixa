from django.contrib.auth import get_user_model

from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from dealio.apps.core_models.constants.runtime_config import RuntimeConfig

User = get_user_model()


class AccountRepositoryHandler:
    def __init__(self):
        self.runtime_config = RuntimeConfig()

    def generate_password(self):
        return self.runtime_config.generate_random_password()

    def generate_verification_code(self):
        return self.runtime_config.generate_verification_code()

    def validate_verification_code(self, verification_code, phone_number):
        try:
            user = User.objects.get(
                phone_number=phone_number,
                verification_code=verification_code
            )
            if user.created_verified < timezone.now() - timedelta(minutes=2):
                raise ValidationError("Verification code has expired.")
            return user
        except User.DoesNotExist:
            raise ValidationError("Invalid phone number or verification code.")
