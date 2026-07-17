from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction

from backend.apps.accounts.dtos.password_recovery_dto import (
    PasswordRecoveryResultDTO,
    ResetPasswordBySmsDTO,
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
    SendSmsPasswordRecoveryCodeDTO,
)
from backend.apps.accounts.dtos.phone_verification_dto import (
    PhoneVerificationResultDTO,
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberByTelegramDTO,
    VerifyPhoneNumberDTO,
)
from backend.apps.accounts.dtos.session_auth_dto import (
    AuthResultDTO,
    LoginUserDTO,
    RegisterUserDTO,
)
from backend.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter
from backend.apps.accounts.repositories.adapters.postgres_adapter import PostgresAdapter
from backend.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from backend.apps.accounts.vo.auth_vo import (
    AccountAuthErrorCodeVO,
    AccountUserLookupVO,
)
from backend.apps.accounts.vo.password_recovery_vo import (
    AccountPasswordRecoveryCacheVO,
    AccountPasswordRecoveryErrorCodeVO,
)
from backend.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationCacheVO,
    AccountPhoneVerificationErrorCodeVO,
)
from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.dtos.sms_providers.kavenegar_params_dto import (
    KavenegarTemplateSmsDTO,
)
from backend.apps.core_models.vo.common_vo import KavenegarVo
from backend.apps.shared.repositories.logic import SharedApplicationLogic

logger = CommonUtils.get_project_logger(__name__)
User = get_user_model()


class AccountLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = PostgresAdapter()
        self.gmail_adapter = AccountEmailAdapter()
        self.verification_code_cache = VerificationCodeCacheAdapter()
        self.shared_logic = SharedApplicationLogic()

    async def async_authenticate_user_by_identifier(self, request, dto: LoginUserDTO) -> AuthResultDTO:
        return await sync_to_async(
            self.authenticate_user_by_identifier,
            thread_sensitive=True,
        )(request, dto)

    async def async_register_user_account(self, dto: RegisterUserDTO) -> AuthResultDTO:
        return await sync_to_async(
            self.register_user_account,
            thread_sensitive=True,
        )(dto)

    async def async_send_verification_email_code(self, user: User) -> bool:
        return await sync_to_async(
            self.send_verification_email_code,
            thread_sensitive=True,
        )(user)

    async def async_send_verification_forget_password_code(self, user: User) -> bool:
        return await sync_to_async(
            self.send_verification_forget_password_code,
            thread_sensitive=True,
        )(user)

    async def async_check_email_validation_code(self, user: User, code: str) -> bool:
        return await sync_to_async(
            self.check_email_validation_code,
            thread_sensitive=True,
        )(user, code)

    async def async_check_forget_password_code(self, user: User, code: str) -> bool:
        return await sync_to_async(
            self.check_forget_password_code,
            thread_sensitive=True,
        )(user, code)

    async def async_send_forget_password_code_by_email(
        self,
        dto: SendPasswordRecoveryCodeDTO,
    ) -> PasswordRecoveryResultDTO:
        return await sync_to_async(
            self.send_forget_password_code_by_email,
            thread_sensitive=True,
        )(dto)

    async def async_reset_forget_password_by_email(
        self,
        dto: ResetPasswordDTO,
    ) -> PasswordRecoveryResultDTO:
        return await sync_to_async(
            self.reset_forget_password_by_email,
            thread_sensitive=True,
        )(dto)

    async def async_send_phone_verification_code(
        self,
        dto: SendPhoneVerificationCodeDTO,
    ) -> PhoneVerificationResultDTO:
        return await sync_to_async(
            self.send_phone_verification_code,
            thread_sensitive=True,
        )(dto)

    async def async_verify_phone_number(
        self,
        dto: VerifyPhoneNumberDTO,
    ) -> PhoneVerificationResultDTO:
        return await sync_to_async(
            self.verify_phone_number,
            thread_sensitive=True,
        )(dto)

    async def async_verify_phone_number_by_telegram(
        self,
        dto: VerifyPhoneNumberByTelegramDTO,
    ) -> PhoneVerificationResultDTO:
        return await sync_to_async(
            self.verify_phone_number_by_telegram,
            thread_sensitive=True,
        )(dto)

    async def async_send_forget_password_code_by_sms(
        self,
        dto: SendSmsPasswordRecoveryCodeDTO,
    ) -> PasswordRecoveryResultDTO:
        return await sync_to_async(
            self.send_forget_password_code_by_sms,
            thread_sensitive=True,
        )(dto)

    async def async_reset_forget_password_by_sms(
        self,
        dto: ResetPasswordBySmsDTO,
    ) -> PasswordRecoveryResultDTO:
        return await sync_to_async(
            self.reset_forget_password_by_sms,
            thread_sensitive=True,
        )(dto)

    async def async_change_password(self, *, user, new_password: str) -> None:
        await sync_to_async(
            self.change_password,
            thread_sensitive=True,
        )(user=user, new_password=new_password)

    async def async_update_user_role(self, role_id, user) -> None:
        await sync_to_async(
            self.update_user_role,
            thread_sensitive=True,
        )(role_id, user)

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

        if not user.is_active or getattr(user, "is_deleted", False) is True:
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

        try:
            # The inner savepoint handles races between the pre-check and the
            # database's case-insensitive uniqueness constraints.
            with transaction.atomic():
                user = self.postgres_adapter.create_user_account(
                    first_name=dto.first_name,
                    last_name=dto.last_name,
                    username=dto.username,
                    email=dto.email,
                    password=dto.password,
                )
        except IntegrityError:
            if self.postgres_adapter.username_exists(dto.username):
                return AuthResultDTO.failed(error_code=AccountAuthErrorCodeVO.USERNAME_EXISTS)
            if self.postgres_adapter.email_exists(dto.email):
                return AuthResultDTO.failed(error_code=AccountAuthErrorCodeVO.EMAIL_EXISTS)
            logger.exception("User registration failed because of a database integrity constraint.")
            raise
        return AuthResultDTO.success(user=user)

    def send_verification_email_code(self, user: User) -> bool:
        return self.gmail_adapter.send_email_verification_code(user)

    def send_verification_forget_password_code(self, user: User) -> bool:
        return self.gmail_adapter.send_forget_password_verification_code(user)

    def check_email_validation_code(self, user: User, code: str) -> bool:
        return self.gmail_adapter.verify_email_code(user, code)

    def check_forget_password_code(self, user: User, code: str) -> bool:
        return self.gmail_adapter.verify_forget_password_code(user, code)

    def send_forget_password_code_by_email(
        self,
        dto: SendPasswordRecoveryCodeDTO,
    ) -> PasswordRecoveryResultDTO:
        user = self.postgres_adapter.fetch_user_base_email(dto.email)
        code_issued = None

        if user and user.is_active and not getattr(user, "is_deleted", False) is True:
            code_issued = self.send_verification_forget_password_code(user=user)

        # Keep the public response account-enumeration safe.
        return PasswordRecoveryResultDTO.success(code_issued=code_issued)

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

        if not user.is_active or getattr(user, "is_deleted", False) is True:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT,
            )

        cache_key = self.gmail_adapter.get_forget_password_verification_cache_key(str(user.id), user.email)
        if not self.verification_code_cache.verify_code(
            cache_key=cache_key,
            code=dto.code,
            consume=False,
        ):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )
        if not self._is_valid_new_password(user=user, password=dto.new_password):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_PASSWORD,
            )
        if not self.verification_code_cache.verify_code(cache_key=cache_key, code=dto.code):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        self.postgres_adapter.update_user_password(
            user=user,
            password=dto.new_password,
        )
        return PasswordRecoveryResultDTO.success()

    def send_phone_verification_code(
        self,
        dto: SendPhoneVerificationCodeDTO,
    ) -> PhoneVerificationResultDTO:
        user = self.postgres_adapter.fetch_user_base_id(dto.user_id)
        validation_error = self._validate_phone_verification_user(user)
        if validation_error:
            return PhoneVerificationResultDTO.failed(error_code=validation_error)

        cache_key = self._phone_verification_cache_key(user)
        code_issued = self._issue_and_send_sms_code(
            phone_number=user.phone_number,
            template_name=KavenegarVo.VERIFY_PHONE_NUMBER,
            cache_key=cache_key,
        )
        return PhoneVerificationResultDTO.success(code_issued=code_issued)

    @transaction.atomic
    def verify_phone_number(
        self,
        dto: VerifyPhoneNumberDTO,
    ) -> PhoneVerificationResultDTO:
        user = self.postgres_adapter.fetch_user_base_id(dto.user_id)
        validation_error = self._validate_phone_verification_user(user)
        if validation_error:
            return PhoneVerificationResultDTO.failed(error_code=validation_error)

        cache_key = self._phone_verification_cache_key(user)
        if not self.verification_code_cache.verify_code(
            cache_key=cache_key,
            code=dto.code,
        ):
            return PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        self.postgres_adapter.mark_phone_number_verified(user=user)
        return PhoneVerificationResultDTO.success()

    @transaction.atomic
    def verify_phone_number_by_telegram(
        self,
        dto: VerifyPhoneNumberByTelegramDTO,
    ) -> PhoneVerificationResultDTO:
        user = self.postgres_adapter.fetch_user_base_id(dto.user_id)
        if not user:
            return PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND,
            )
        if not user.is_active or getattr(user, "is_deleted", False) is True:
            return PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT,
            )
        if user.phone_number_verified and user.phone_number == dto.phone_number:
            return PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED,
            )
        if self.postgres_adapter.phone_number_used_by_other_user(
            phone_number=dto.phone_number,
            user_id=str(user.id),
        ):
            return PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE,
            )

        old_cache_key = self._phone_verification_cache_key(user) if user.phone_number else None
        self.postgres_adapter.update_and_verify_phone_number(
            user=user,
            phone_number=dto.phone_number,
        )
        if old_cache_key:
            self.verification_code_cache.delete_code(cache_key=old_cache_key)

        return PhoneVerificationResultDTO.success()

    def send_forget_password_code_by_sms(
        self,
        dto: SendSmsPasswordRecoveryCodeDTO,
    ) -> PasswordRecoveryResultDTO:
        user = self.postgres_adapter.fetch_user_base_phone_number(dto.phone_number)
        code_issued = None

        if user and user.is_active and not getattr(user, "is_deleted", False) is True and user.phone_number_verified:
            cache_key = self._sms_password_recovery_cache_key(user)
            code_issued = self._issue_and_send_sms_code(
                phone_number=user.phone_number,
                template_name=KavenegarVo.FORGOT_PASSWORD,
                cache_key=cache_key,
            )

        # Do not reveal whether an account exists for the submitted phone number.
        return PasswordRecoveryResultDTO.success(code_issued=code_issued)

    @transaction.atomic
    def reset_forget_password_by_sms(
        self,
        dto: ResetPasswordBySmsDTO,
    ) -> PasswordRecoveryResultDTO:
        user = self.postgres_adapter.fetch_user_base_phone_number(dto.phone_number)

        if not user:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        if not user.is_active or getattr(user, "is_deleted", False) is True:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT,
            )

        if not user.phone_number_verified:
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        cache_key = self._sms_password_recovery_cache_key(user)
        if not self.verification_code_cache.verify_code(
            cache_key=cache_key,
            code=dto.code,
            consume=False,
        ):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )
        if not self._is_valid_new_password(user=user, password=dto.new_password):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_PASSWORD,
            )
        if not self.verification_code_cache.verify_code(cache_key=cache_key, code=dto.code):
            return PasswordRecoveryResultDTO.failed(
                error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )

        self.postgres_adapter.update_user_password(
            user=user,
            password=dto.new_password,
        )
        return PasswordRecoveryResultDTO.success()

    def change_password(self, *, user, new_password: str) -> None:
        if not self._is_valid_new_password(user=user, password=new_password):
            raise DjangoValidationError("New password does not meet security requirements.")
        self.postgres_adapter.update_user_password(user=user, password=new_password)

    @staticmethod
    def _is_valid_new_password(*, user, password: str) -> bool:
        if user.check_password(password):
            return False
        try:
            validate_password(password, user=user)
        except DjangoValidationError:
            return False
        return True

    def update_user_role(self, role_id, user) -> None:
        role = self.postgres_adapter.fetch_role_base_id(role_id)
        user.role = role
        user.save(update_fields=["role"])

    def _issue_and_send_sms_code(
        self,
        *,
        phone_number: str,
        template_name: str,
        cache_key: str,
    ) -> bool:
        code = self.verification_code_cache.issue_code(cache_key=cache_key)
        if code is None:
            return False

        self.shared_logic.send_sms(
            KavenegarTemplateSmsDTO(
                recipient_phone_number=phone_number,
                template_name=template_name,
                token=code,
                token2=str(self.verification_code_cache.EXPIRATION_MINUTES),
            )
        )
        return True

    @staticmethod
    def _phone_verification_cache_key(user) -> str:
        return AccountPhoneVerificationCacheVO.KEY_TEMPLATE.value.format(
            user_id=user.id,
            identifier_fingerprint=VerificationCodeCacheAdapter.fingerprint_identifier(user.phone_number),
        )

    @staticmethod
    def _sms_password_recovery_cache_key(user) -> str:
        return AccountPasswordRecoveryCacheVO.SMS_KEY_TEMPLATE.value.format(
            user_id=user.id,
            identifier_fingerprint=VerificationCodeCacheAdapter.fingerprint_identifier(user.phone_number),
        )

    @staticmethod
    def _validate_phone_verification_user(user) -> AccountPhoneVerificationErrorCodeVO | None:
        if not user:
            return AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND
        if not user.is_active or getattr(user, "is_deleted", False) is True:
            return AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT
        if not user.phone_number:
            return AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED
        if user.phone_number_verified:
            return AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED
        return None
