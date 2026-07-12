from unittest.mock import MagicMock, patch

from django.test import TestCase

from dealio.apps.accounts.dtos.password_recovery_dto import ResetPasswordDTO, SendPasswordRecoveryCodeDTO
from dealio.apps.accounts.dtos.session_auth_dto import LoginUserDTO, RegisterUserDTO
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.tests.factories import UserFactory
from dealio.tests.mixins import IsolatedServiceTestMixin


class AccountLogicRepositoryTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.repository = AccountLogicRepository()
        self.repository.postgres_adapter = MagicMock()
        self.repository.gmail_adapter = MagicMock()

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

    def test_reset_password_updates_hash_after_valid_code(self):
        user = UserFactory.create()
        self.repository.postgres_adapter.fetch_user_base_email.return_value = user
        self.repository.gmail_adapter.verify_forget_password_code.return_value = True

        result = self.repository.reset_forget_password_by_email(
            ResetPasswordDTO(email=user.email, code="123456", new_password="NewStrongPass123!")
        )

        user.refresh_from_db()
        self.assertTrue(result.is_success)
        self.assertTrue(user.check_password("NewStrongPass123!"))
