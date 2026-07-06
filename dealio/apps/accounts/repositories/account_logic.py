from dealio.apps.common.utils.common_utils import CommonUtils
from threading import Thread

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.timezone import now

from dealio.apps.accounts.dtos.password_recovery_dto import (
    PasswordRecoveryResultDTO,
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
)
from dealio.apps.accounts.dtos.session_auth_dto import AuthResultDTO, LoginUserDTO, RegisterUserDTO
from dealio.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter
from dealio.apps.accounts.repositories.adapters.kavenegar_adapter import KavenegarSmsAdapter
from dealio.apps.accounts.repositories.adapters.postgres_adapter import PostgresAdapter
from dealio.apps.accounts.repositories.adapters.redis_adapter import RedisAdapter
from dealio.apps.accounts.vo.auth_vo import (
    AccountAuthErrorCodeVO,
    AccountSmsFallbackVO,
    AccountUserFieldVO,
    AccountUserLookupVO,
)
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.core_models.vo.common_vo import KavenegarVo

logger = CommonUtils.get_project_logger(__name__)
User = get_user_model()


class AccountLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = PostgresAdapter()
        self.redis_adapter = RedisAdapter()
        self.kavenegar_sms = KavenegarSmsAdapter()
        self.gmail_adapter = AccountEmailAdapter()

    def authenticate_user_by_identifier(self, request, dto: LoginUserDTO) -> AuthResultDTO:
        username = dto.identifier.strip()

        if AccountUserLookupVO.EMAIL_SEPARATOR.value in username:
            user = self.postgres_adapter.fetch_user_base_email(username)
            if user:
                username = user.username

        user = authenticate(
            request=request,
            username=username,
            password=dto.password,
        )

        if not user:
            return AuthResultDTO.failed(
                error_code=AccountAuthErrorCodeVO.INVALID_CREDENTIALS,
            )

        if not user.is_active:
            return AuthResultDTO.failed(
                error_code=AccountAuthErrorCodeVO.INACTIVE_ACCOUNT,
            )

        return AuthResultDTO.success(user=user)

    @transaction.atomic
    def register_user_account(self, dto: RegisterUserDTO) -> AuthResultDTO:
        if self.postgres_adapter.username_exists(dto.username):
            return AuthResultDTO.failed(error_code=AccountAuthErrorCodeVO.USERNAME_EXISTS)

        if self.postgres_adapter.email_exists(dto.email):
            return AuthResultDTO.failed(error_code=AccountAuthErrorCodeVO.EMAIL_EXISTS)

        user = self.postgres_adapter.create_user_account(
            first_name=dto.first_name,
            last_name=dto.last_name,
            username=dto.username,
            email=dto.email,
            password=dto.password,
        )
        return AuthResultDTO.success(user=user)

    def send_verification_email_code(self, user: User):
        self.gmail_adapter.send_email_verification_code(user)

    def send_verification_forget_password_code(self, user: User):
        self.gmail_adapter.send_forget_password_verification_code(user)

    def check_email_validation_code(self, user: User, code: str):
        return self.gmail_adapter.verify_email_code(user, code)

    def check_forget_password_code(self, user: User, code: str):
        return self.gmail_adapter.verify_forget_password_code(user, code)

    def send_forget_password_code_by_email(
        self,
        dto: SendPasswordRecoveryCodeDTO,
    ) -> PasswordRecoveryResultDTO:
        user = self.postgres_adapter.fetch_user_base_email(dto.email)

        if user and user.is_active:
            self.send_verification_forget_password_code(user=user)

        return PasswordRecoveryResultDTO.success()

    @transaction.atomic
    def reset_forget_password_by_email(
        self,
        dto: ResetPasswordDTO,
    ) -> PasswordRecoveryResultDTO:
        user = self.postgres_adapter.fetch_user_base_email(dto.email)

        if not user:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        if not user.is_active:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT,
            )

        if not self.check_forget_password_code(user=user, code=dto.code):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        user.set_password(dto.new_password)
        user.save(update_fields=[AccountUserFieldVO.PASSWORD.value])

        return PasswordRecoveryResultDTO.success()

    def update_user_role(self, id, user):
        role = self.postgres_adapter.fetch_role_base_id(id)
        user.role = role
        user.save()

    def update_user_verification(self, verification_code, phone_number):
        user = self.postgres_adapter.fetch_user_base_phone_number(phone_number)
        user.verification_code = verification_code
        user.created_verified = now()
        user.save()

    def send_sms_kavenegar(self, recipient_phone_number, template_name, first_value=None, second_value=None):
        self.kavenegar_sms.send_sms(
            receptor=recipient_phone_number,
            value_first=first_value,
            value_second=second_value,
            template=template_name
        )

    def send_change_password_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.change_password,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_recovery_password_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.password_recovery,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_create_user_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.create_account,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_verification_code_in_separate_thread(self, phone_number, verification_code):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.create_account,
                    verification_code,
                    AccountSmsFallbackVO.VERIFICATION_CODE_USERNAME.value,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))
