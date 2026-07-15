from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from backend.apps.accounts.web.forms import (
    ForgotPasswordTemplateForm,
    LoginTemplateForm,
    RecoverPasswordTemplateForm,
    RegisterTemplateForm,
)
from backend.apps.accounts.web.validators import AccountWebInputValidator


class AccountWebValidatorTests(SimpleTestCase):
    def test_normalizes_valid_username_and_gmail(self):
        self.assertEqual(AccountWebInputValidator.validate_english_username("  Amir_12  "), "Amir_12")
        self.assertEqual(AccountWebInputValidator.validate_gmail_email(" USER@GMAIL.COM "), "user@gmail.com")

    def test_rejects_non_gmail_address(self):
        with self.assertRaises(ValidationError):
            AccountWebInputValidator.validate_gmail_email("user@example.com")

    def test_rejects_invalid_recovery_code(self):
        with self.assertRaises(ValidationError):
            AccountWebInputValidator.validate_recovery_code("12ab")


class AccountWebFormTests(SimpleTestCase):
    def test_login_form_builds_trimmed_dto(self):
        form = LoginTemplateForm(data={"identifier": "  user@gmail.com ", "password": "secret"})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.to_dto().identifier, "user@gmail.com")

    def test_register_form_builds_dto_for_valid_data(self):
        form = RegisterTemplateForm(
            data={
                "first_name": "علی",
                "last_name": "رضایی",
                "username": "amir_dev",
                "email": "amir@gmail.com",
                "password": "VeryStrongPass123!",
                "password_confirm": "VeryStrongPass123!",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        dto = form.to_dto()
        self.assertEqual(dto.username, "amir_dev")
        self.assertEqual(dto.email, "amir@gmail.com")

    def test_register_form_rejects_password_mismatch(self):
        form = RegisterTemplateForm(
            data={
                "first_name": "علی",
                "last_name": "رضایی",
                "username": "amir_dev",
                "email": "amir@gmail.com",
                "password": "VeryStrongPass123!",
                "password_confirm": "DifferentPass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password_confirm", form.errors)

    def test_password_recovery_forms_build_dtos(self):
        forgot_form = ForgotPasswordTemplateForm(data={"email": "user@gmail.com"})
        recover_form = RecoverPasswordTemplateForm(
            data={
                "email": "user@gmail.com",
                "code": "123456",
                "new_password": "VeryStrongPass123!",
                "password_confirm": "VeryStrongPass123!",
            }
        )

        self.assertTrue(forgot_form.is_valid(), forgot_form.errors)
        self.assertTrue(recover_form.is_valid(), recover_form.errors)
        self.assertEqual(forgot_form.to_dto().email, "user@gmail.com")
        self.assertEqual(recover_form.to_dto().code, "123456")

    def test_sms_password_recovery_forms_build_dtos(self):
        forgot_form = ForgotPasswordTemplateForm(
            data={
                "method": "sms",
                "phone_number": "09121234567",
            }
        )
        recover_form = RecoverPasswordTemplateForm(
            data={
                "method": "sms",
                "phone_number": "09121234567",
                "code": "123456",
                "new_password": "VeryStrongPass123!",
                "password_confirm": "VeryStrongPass123!",
            }
        )

        self.assertTrue(forgot_form.is_valid(), forgot_form.errors)
        self.assertTrue(recover_form.is_valid(), recover_form.errors)
        self.assertEqual(forgot_form.to_dto().phone_number, "09121234567")
        self.assertEqual(recover_form.to_dto().phone_number, "09121234567")

    def test_recovery_form_requires_only_selected_identifier(self):
        email_form = ForgotPasswordTemplateForm(
            data={"method": "email", "phone_number": "invalid"}
        )
        sms_form = ForgotPasswordTemplateForm(
            data={"method": "sms", "email": "not-an-email"}
        )

        self.assertFalse(email_form.is_valid())
        self.assertIn("email", email_form.errors)
        self.assertNotIn("phone_number", email_form.errors)
        self.assertFalse(sms_form.is_valid())
        self.assertIn("phone_number", sms_form.errors)
        self.assertNotIn("email", sms_form.errors)
