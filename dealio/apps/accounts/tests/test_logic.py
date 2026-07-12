from unittest.mock import MagicMock, patch

from django.test import TestCase

from dealio.apps.accounts.dtos.password_recovery_dto import (
    ResetPasswordBySmsDTO,
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
    SendSmsPasswordRecoveryCodeDTO,
)
from dealio.apps.accounts.dtos.phone_verification_dto import (
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberByTelegramDTO,
    VerifyPhoneNumberDTO,
)
from dealio.apps.accounts.dtos.session_auth_dto import LoginUserDTO, RegisterUserDTO
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.apps.accounts.vo.phone_verification_vo import AccountPhoneVerificationErrorCodeVO
from dealio.apps.core_models.vo.common_vo import KavenegarVo
from dealio.tests.factories import UserFactory
from dealio.tests.mixins import IsolatedServiceTestMixin


class AccountLogicRepositoryTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.repository = AccountLogicRepository()
        self.repository.postgres_adapter = MagicMock()
        self.repository.gmail_adapter = MagicMock()
        self.repository.verification_code_cache = MagicMock()
        self.repository.verification_code_cache.EXPIRATION_MINUTES = 5
        self.repository.shared_logic = MagicMock()

    @patch("dealio.apps.accounts.repositories.account_logic.authenticate")
    def test_authenticates_email_by_resolving_username(self, authenticate_mock):
        request = object()
        db_user = MagicMock(username="resolved-user")
        authenticated_user = MagicMock(is_active=True)
        self.repository.postgres_adapter.fetch_user_base_email.return_value = db_user
        authenticate_mock.return_value = authenticated_user

        result = self.repository.authenticate_user_by_identifier(
            request,
            LoginUserDTO(identifier="user@gmail.com", password="secret"),
        )

        self.assertTrue(result.is_success)
        authenticate_mock.assert_called_once_with(
            request=request,
            username="resolved-user",
            password="secret",
        )

    @patch("dealio.apps.accounts.repositories.account_logic.authenticate", return_value=None)
    def test_returns_invalid_credentials_when_authentication_fails(self, _authenticate_mock):
        result = self.repository.authenticate_user_by_identifier(
            None,
            LoginUserDTO(identifier="unknown", password="bad"),
        )

        self.assertFalse(result.is_success)
        self.assertEqual(result.error_code, AccountAuthErrorCodeVO.INVALID_CREDENTIALS)

    def test_register_rejects_duplicate_username_before_creating_user(self):
        self.repository.postgres_adapter.username_exists.return_value = True
        dto = RegisterUserDTO("علی", "رضایی", "duplicate", "new@gmail.com", "StrongPass123!")

        result = self.repository.register_user_account(dto)

        self.assertEqual(result.error_code, AccountAuthErrorCodeVO.USERNAME_EXISTS)
        self.repository.postgres_adapter.create_user_account.assert_not_called()

    def test_register_delegates_creation_for_unique_user(self):
        created_user = object()
        self.repository.postgres_adapter.username_exists.return_value = False
        self.repository.postgres_adapter.email_exists.return_value = False
        self.repository.postgres_adapter.create_user_account.return_value = created_user
        dto = RegisterUserDTO("علی", "رضایی", "new-user", "new@gmail.com", "StrongPass123!")

        result = self.repository.register_user_account(dto)

        self.assertTrue(result.is_success)
        self.assertIs(result.user, created_user)

    def test_forgot_password_send_is_non_enumerating(self):
        self.repository.postgres_adapter.fetch_user_base_email.return_value = None

        result = self.repository.send_forget_password_code_by_email(
            SendPasswordRecoveryCodeDTO(email="missing@gmail.com")
        )

        self.assertTrue(result.is_success)
        self.repository.gmail_adapter.send_forget_password_verification_code.assert_not_called()

    def test_reset_password_rejects_invalid_code(self):
        user = UserFactory.create()
        self.repository.postgres_adapter.fetch_user_base_email.return_value = user
        self.repository.gmail_adapter.verify_forget_password_code.return_value = False

        result = self.repository.reset_forget_password_by_email(
            ResetPasswordDTO(email=user.email, code="000000", new_password="NewStrongPass123!")
        )

        self.assertFalse(result.is_success)
        self.assertEqual(result.error_code, AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE)
        self.repository.postgres_adapter.update_user_password.assert_not_called()

    def test_reset_password_delegates_update_after_valid_email_code(self):
        user = UserFactory.create()
        self.repository.postgres_adapter.fetch_user_base_email.return_value = user
        self.repository.gmail_adapter.verify_forget_password_code.return_value = True

        result = self.repository.reset_forget_password_by_email(
            ResetPasswordDTO(email=user.email, code="123456", new_password="NewStrongPass123!")
        )

        self.assertTrue(result.is_success)
        self.repository.postgres_adapter.update_user_password.assert_called_once_with(
            user=user,
            password="NewStrongPass123!",
        )

    def test_send_phone_verification_rejects_user_without_phone_number(self):
        user = MagicMock(is_active=True, phone_number=None, phone_number_verified=False)
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user

        result = self.repository.send_phone_verification_code(
            SendPhoneVerificationCodeDTO(user_id="user-id")
        )

        self.assertFalse(result.is_success)
        self.assertEqual(result.error_code, AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED)
        self.repository.shared_logic.send_sms.assert_not_called()

    def test_send_phone_verification_uses_shared_sms_logic(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user
        self.repository.verification_code_cache.issue_code.return_value = "123456"

        result = self.repository.send_phone_verification_code(
            SendPhoneVerificationCodeDTO(user_id="user-id")
        )

        self.assertTrue(result.is_success)
        self.repository.shared_logic.send_sms.assert_called_once()
        sms_dto = self.repository.shared_logic.send_sms.call_args.args[0]
        self.assertEqual(sms_dto.recipient_phone_number, "09121234567")
        self.assertEqual(sms_dto.template_name, KavenegarVo.VERIFY_PHONE_NUMBER)
        self.assertEqual(sms_dto.token, "123456")
        self.assertEqual(sms_dto.token2, "5")

    def test_send_phone_verification_does_not_send_when_code_is_still_active(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user
        self.repository.verification_code_cache.issue_code.return_value = None

        result = self.repository.send_phone_verification_code(
            SendPhoneVerificationCodeDTO(user_id="user-id")
        )

        self.assertTrue(result.is_success)
        self.assertFalse(result.code_issued)
        self.repository.shared_logic.send_sms.assert_not_called()

    def test_verify_phone_number_by_telegram_updates_and_verifies_shared_phone(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number=None,
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user
        self.repository.postgres_adapter.phone_number_used_by_other_user.return_value = False

        result = self.repository.verify_phone_number_by_telegram(
            VerifyPhoneNumberByTelegramDTO(
                user_id="user-id",
                phone_number="09121234567",
            )
        )

        self.assertTrue(result.is_success)
        self.repository.postgres_adapter.update_and_verify_phone_number.assert_called_once_with(
            user=user,
            phone_number="09121234567",
        )

    def test_verify_phone_number_by_telegram_rejects_phone_owned_by_other_user(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number=None,
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user
        self.repository.postgres_adapter.phone_number_used_by_other_user.return_value = True

        result = self.repository.verify_phone_number_by_telegram(
            VerifyPhoneNumberByTelegramDTO(
                user_id="user-id",
                phone_number="09121234567",
            )
        )

        self.assertFalse(result.is_success)
        self.assertEqual(
            result.error_code,
            AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE,
        )
        self.repository.postgres_adapter.update_and_verify_phone_number.assert_not_called()

    def test_verify_phone_number_marks_user_verified_and_consumes_code(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_id.return_value = user
        self.repository.verification_code_cache.verify_code.return_value = True

        result = self.repository.verify_phone_number(
            VerifyPhoneNumberDTO(user_id="user-id", code="123456")
        )

        self.assertTrue(result.is_success)
        self.repository.verification_code_cache.verify_code.assert_called_once_with(
            cache_key="phone_verification:user-id:09121234567",
            code="123456",
        )
        self.repository.postgres_adapter.mark_phone_number_verified.assert_called_once_with(user=user)

    def test_forgot_password_sms_send_is_non_enumerating(self):
        self.repository.postgres_adapter.fetch_user_base_phone_number.return_value = None

        result = self.repository.send_forget_password_code_by_sms(
            SendSmsPasswordRecoveryCodeDTO(phone_number="09121234567")
        )

        self.assertTrue(result.is_success)
        self.repository.shared_logic.send_sms.assert_not_called()


    def test_forgot_password_sms_does_not_send_for_unverified_phone(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.repository.postgres_adapter.fetch_user_base_phone_number.return_value = user

        result = self.repository.send_forget_password_code_by_sms(
            SendSmsPasswordRecoveryCodeDTO(phone_number="09121234567")
        )

        self.assertTrue(result.is_success)
        self.repository.shared_logic.send_sms.assert_not_called()

    def test_forgot_password_sms_uses_password_template(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=True,
        )
        self.repository.postgres_adapter.fetch_user_base_phone_number.return_value = user
        self.repository.verification_code_cache.issue_code.return_value = "654321"

        result = self.repository.send_forget_password_code_by_sms(
            SendSmsPasswordRecoveryCodeDTO(phone_number="09121234567")
        )

        self.assertTrue(result.is_success)
        sms_dto = self.repository.shared_logic.send_sms.call_args.args[0]
        self.assertEqual(sms_dto.template_name, KavenegarVo.FORGOT_PASSWORD)
        self.assertEqual(sms_dto.token, "654321")

    def test_forgot_password_sms_does_not_send_while_previous_code_is_active(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=True,
        )
        self.repository.postgres_adapter.fetch_user_base_phone_number.return_value = user
        self.repository.verification_code_cache.issue_code.return_value = None

        result = self.repository.send_forget_password_code_by_sms(
            SendSmsPasswordRecoveryCodeDTO(phone_number="09121234567")
        )

        self.assertTrue(result.is_success)
        self.assertFalse(result.code_issued)
        self.repository.shared_logic.send_sms.assert_not_called()

    def test_reset_password_by_sms_delegates_update_after_valid_code(self):
        user = MagicMock(
            id="user-id",
            is_active=True,
            phone_number="09121234567",
            phone_number_verified=True,
        )
        self.repository.postgres_adapter.fetch_user_base_phone_number.return_value = user
        self.repository.verification_code_cache.verify_code.return_value = True

        result = self.repository.reset_forget_password_by_sms(
            ResetPasswordBySmsDTO(
                phone_number="09121234567",
                code="123456",
                new_password="NewStrongPass123!",
            )
        )

        self.assertTrue(result.is_success)
        self.repository.postgres_adapter.update_user_password.assert_called_once_with(
            user=user,
            password="NewStrongPass123!",
        )
