from dataclasses import FrozenInstanceError
from django.test import SimpleTestCase

from dealio.apps.accounts.dtos.password_recovery_dto import PasswordRecoveryResultDTO
from dealio.apps.accounts.dtos.session_auth_dto import AuthResultDTO, LoginUserDTO
from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.apps.accounts.web.presenters import (
    AccountWebAuthErrorPresenter,
    AccountWebPasswordRecoveryErrorPresenter,
)
from dealio.apps.accounts.web.value_objects import AccountWebFieldNameVO, AccountWebValidationMessageVO


class AccountDTOTests(SimpleTestCase):
    def test_auth_result_success_and_failure_factories(self):
        user = object()

        success = AuthResultDTO.success(user=user)
        failure = AuthResultDTO.failed(error_code=AccountAuthErrorCodeVO.INVALID_CREDENTIALS)

        self.assertTrue(success.is_success)
        self.assertIs(success.user, user)
        self.assertFalse(failure.is_success)
        self.assertEqual(failure.error_code, AccountAuthErrorCodeVO.INVALID_CREDENTIALS)

    def test_login_dto_is_immutable(self):
        dto = LoginUserDTO(identifier="user", password="secret")

        with self.assertRaises(FrozenInstanceError):
            dto.identifier = "changed"

    def test_password_recovery_factories(self):
        success = PasswordRecoveryResultDTO.success()
        failure = PasswordRecoveryResultDTO.failed(
            error_code=AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT
        )

        self.assertTrue(success.is_success)
        self.assertFalse(failure.is_success)
        self.assertEqual(failure.error_code, AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT)


class AccountPresenterTests(SimpleTestCase):
    def test_auth_presenter_maps_duplicate_email_to_email_field(self):
        self.assertEqual(
            AccountWebAuthErrorPresenter.field_for(AccountAuthErrorCodeVO.EMAIL_EXISTS),
            AccountWebFieldNameVO.EMAIL.value,
        )
        self.assertEqual(
            AccountWebAuthErrorPresenter.message_for(AccountAuthErrorCodeVO.EMAIL_EXISTS),
            AccountWebValidationMessageVO.EMAIL_EXISTS.value,
        )

    def test_password_recovery_presenter_hides_user_enumeration_details(self):
        message = AccountWebPasswordRecoveryErrorPresenter.message_for(
            AccountPasswordRecoveryErrorCodeVO.USER_NOT_FOUND
        )

        self.assertEqual(message, AccountWebValidationMessageVO.INVALID_OR_EXPIRED_RECOVERY_CODE.value)
