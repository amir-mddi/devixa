from unittest.mock import MagicMock

from django.test import TestCase

from backend.apps.accounts.dtos.profile_dto import (
    UpdateAccountContactDTO,
    UpdateAccountProfileDTO,
)
from backend.apps.accounts.enums.profile_enums import AccountProfileErrorCodeEnum
from backend.apps.accounts.logic.profile_logic import AccountProfileLogic
from backend.tests.factories import UserFactory


class AccountProfileLogicTests(TestCase):
    def setUp(self):
        self.logic = AccountProfileLogic()
        self.logic.verification_cache = MagicMock()
        self.logic.email_adapter = MagicMock()
        self.logic.email_adapter.get_email_verification_cache_key.return_value = (
            "old-email-key"
        )
        self.logic.verification_cache.fingerprint_identifier.return_value = (
            "phone-fingerprint"
        )

    def test_update_profile_changes_identity_without_touching_business_services(self):
        user = UserFactory.create(username="old-name")

        result = self.logic.update_profile(
            UpdateAccountProfileDTO(
                user_id=str(user.id),
                first_name="امیر",
                last_name="رضایی",
                username="new-name",
            )
        )

        user.refresh_from_db()
        self.assertTrue(result.is_success)
        self.assertEqual(user.username, "new-name")
        self.assertEqual(user.first_name, "امیر")

    def test_update_profile_rejects_case_insensitive_duplicate_username(self):
        UserFactory.create(username="ExistingUser")
        user = UserFactory.create(username="second-user")

        result = self.logic.update_profile(
            UpdateAccountProfileDTO(
                user_id=str(user.id),
                first_name=user.first_name,
                last_name=user.last_name,
                username="existinguser",
            )
        )

        self.assertFalse(result.is_success)
        self.assertEqual(
            result.error_code,
            AccountProfileErrorCodeEnum.USERNAME_ALREADY_IN_USE,
        )

    def test_contact_changes_reset_verification_and_clear_old_codes(self):
        user = UserFactory.create(
            email="old-address@gmail.com",
            phone_number="09121234567",
            email_verified=True,
            phone_number_verified=True,
        )

        result = self.logic.update_contacts(
            UpdateAccountContactDTO(
                user_id=str(user.id),
                email="new-address@gmail.com",
                phone_number="09121234568",
            )
        )

        user.refresh_from_db()
        self.assertTrue(result.is_success)
        self.assertTrue(result.email_changed)
        self.assertTrue(result.phone_number_changed)
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_number_verified)
        self.logic.verification_cache.delete_code.assert_any_call(
            cache_key="old-email-key"
        )
        self.assertEqual(self.logic.verification_cache.delete_code.call_count, 2)

    def test_unchanged_contacts_keep_existing_verification_status(self):
        user = UserFactory.create(
            email="verified@gmail.com",
            phone_number="09121234567",
            email_verified=True,
            phone_number_verified=True,
        )

        result = self.logic.update_contacts(
            UpdateAccountContactDTO(
                user_id=str(user.id),
                email="verified@gmail.com",
                phone_number="09121234567",
            )
        )

        user.refresh_from_db()
        self.assertTrue(result.is_success)
        self.assertFalse(result.email_changed)
        self.assertFalse(result.phone_number_changed)
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_number_verified)
        self.logic.verification_cache.delete_code.assert_not_called()
