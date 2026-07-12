from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dealio.apps.accounts.dtos.password_recovery_dto import PasswordRecoveryResultDTO
from dealio.apps.accounts.dtos.phone_verification_dto import PhoneVerificationResultDTO
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.apps.accounts.vo.phone_verification_vo import AccountPhoneVerificationErrorCodeVO
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

    @patch("dealio.apps.accounts.views.account_logic.send_verification_email_code")
    def test_email_verification_send_delegates_for_authenticated_user(self, send_mock):
        user = UserFactory.create(email_verified=False)
        self.client.force_authenticate(user)

        response = self.client.post(reverse("send-email-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once_with(user)

    @patch("dealio.apps.accounts.views.account_logic.send_forget_password_code_by_email")
    def test_forgot_password_endpoint_returns_generic_success(self, send_mock):
        send_mock.return_value = PasswordRecoveryResultDTO.success()

        response = self.client.post(
            reverse("send-forgot-password-code"),
            {"email": "missing@gmail.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_mock.assert_called_once()

    @patch("dealio.apps.accounts.views.account_logic.reset_forget_password_by_email")
    def test_password_reset_endpoint_returns_bad_request_for_invalid_code(self, reset_mock):
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

    def test_phone_verification_send_requires_authentication(self):
        response = self.client.post(reverse("send-phone-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("dealio.apps.accounts.views.account_logic.send_phone_verification_code")
    def test_phone_verification_send_delegates_to_logic(self, send_mock):
        user = UserFactory.create(
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.client.force_authenticate(user)
        send_mock.return_value = PhoneVerificationResultDTO.success()

        response = self.client.post(reverse("send-phone-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dto = send_mock.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(user.id))

    @patch("dealio.apps.accounts.views.account_logic.send_phone_verification_code")
    def test_phone_verification_send_returns_validation_error(self, send_mock):
        user = UserFactory.create(phone_number=None, phone_number_verified=False)
        self.client.force_authenticate(user)
        send_mock.return_value = PhoneVerificationResultDTO.failed(
            error_code=AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED,
        )

        response = self.client.post(reverse("send-phone-verification-code"), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("dealio.apps.accounts.views.account_logic.verify_phone_number")
    def test_phone_verification_rejects_non_six_digit_code_before_logic(self, verify_mock):
        user = UserFactory.create(phone_number="09121234568")
        self.client.force_authenticate(user)

        response = self.client.post(
            reverse("verify-phone-code"),
            {"code": "12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        verify_mock.assert_not_called()

    @patch("dealio.apps.accounts.views.account_logic.verify_phone_number")
    def test_phone_verification_verify_delegates_to_logic(self, verify_mock):
        user = UserFactory.create(phone_number="09121234569")
        self.client.force_authenticate(user)
        verify_mock.return_value = PhoneVerificationResultDTO.success()

        response = self.client.post(
            reverse("verify-phone-code"),
            {"code": "123456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dto = verify_mock.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(user.id))
        self.assertEqual(dto.code, "123456")

    @patch("dealio.apps.accounts.views.account_logic.send_forget_password_code_by_sms")
    def test_forgot_password_sms_send_normalizes_phone_number(self, send_mock):
        send_mock.return_value = PasswordRecoveryResultDTO.success()

        response = self.client.post(
            reverse("send-forgot-password-sms-code"),
            {"phone_number": "+989121234567"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dto = send_mock.call_args.kwargs["dto"]
        self.assertEqual(dto.phone_number, "09121234567")

    @patch("dealio.apps.accounts.views.account_logic.reset_forget_password_by_sms")
    def test_forgot_password_sms_verify_delegates_to_logic(self, reset_mock):
        reset_mock.return_value = PasswordRecoveryResultDTO.success()

        response = self.client.post(
            reverse("verify-forgot-password-sms-code"),
            {
                "phone_number": "989121234567",
                "code": "123456",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dto = reset_mock.call_args.kwargs["dto"]
        self.assertEqual(dto.phone_number, "09121234567")
        self.assertEqual(dto.code, "123456")
