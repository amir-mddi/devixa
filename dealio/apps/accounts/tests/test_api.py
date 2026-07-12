from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dealio.apps.accounts.dtos.password_recovery_dto import PasswordRecoveryResultDTO
from dealio.tests.factories import UserFactory


class AccountAPITests(APITestCase):
    def setUp(self):
        super().setUp()
        self.rate_limit_patcher = patch(
            "dealio.apps.common.helpers.decorators.rate_limit.is_rate_limit_allowed",
            return_value=True,
        )
        self.rate_limit_patcher.start()
        self.addCleanup(self.rate_limit_patcher.stop)

    def test_email_verification_send_requires_authentication(self):
        response = self.client.post(reverse("send-email-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("dealio.apps.accounts.views.AccountLogicRepository.send_verification_email_code")
    def test_email_verification_send_delegates_for_authenticated_user(self, send_mock):
        user = UserFactory.create(email_verified=False)
        self.client.force_authenticate(user)

        response = self.client.post(reverse("send-email-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once_with(user)

    @patch("dealio.apps.accounts.views.AccountLogicRepository.send_forget_password_code_by_email")
    def test_forgot_password_endpoint_returns_generic_success(self, send_mock):
        send_mock.return_value = PasswordRecoveryResultDTO.success()

        response = self.client.post(
            reverse("send-forgot-password-code"),
            {"email": "missing@gmail.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once()

    @patch("dealio.apps.accounts.views.AccountLogicRepository.reset_forget_password_by_email")
    def test_password_reset_endpoint_returns_bad_request_for_invalid_code(self, reset_mock):
        from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO

        reset_mock.return_value = PasswordRecoveryResultDTO.failed(
            error_code=AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE
        )

        response = self.client.post(
            reverse("verify-forgot-password-code"),
            {
                "email": "user@gmail.com",
                "code": "123456",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
