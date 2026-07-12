from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dealio.apps.accounts.models import SocialAccount, SocialAuthProvider
from dealio.tests.factories import AccessFactory, RoleFactory, UserFactory


class AccountModelTests(TestCase):
    def test_role_can_receive_accesses_and_has_readable_string(self):
        access = AccessFactory.create(name="courses.read")
        role = RoleFactory.create(name="Admin", symbol="admin", accesses=[access])

        self.assertEqual(str(role), "Admin")
        self.assertQuerySetEqual(role.accesses.all(), [access])

    def test_user_phone_validator_rejects_invalid_iranian_number(self):
        user = UserFactory.create(phone_number="123")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_username_is_unique_case_insensitively(self):
        UserFactory.create(username="AmirDev")
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserFactory.create(username="amirdev")

    def test_email_is_unique_case_insensitively(self):
        UserFactory.create(email="User@Gmail.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserFactory.create(email="user@gmail.com")

    def test_social_account_provider_identity_is_unique(self):
        first_user = UserFactory.create()
        second_user = UserFactory.create()
        SocialAccount.objects.create(
            user=first_user,
            provider=SocialAuthProvider.GOOGLE,
            provider_user_id="provider-user-1",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            SocialAccount.objects.create(
                user=second_user,
                provider=SocialAuthProvider.GOOGLE,
                provider_user_id="provider-user-1",
            )

    def test_social_account_string_is_provider_and_identifier(self):
        social = SocialAccount.objects.create(
            user=UserFactory.create(),
            provider=SocialAuthProvider.GITHUB,
            provider_user_id="42",
        )
        self.assertEqual(str(social), "github:42")

    def test_changing_phone_number_resets_verification_status(self):
        user = UserFactory.create(phone_number="09121234567", phone_number_verified=True)
        user.phone_number = "09121234568"
        user.save(update_fields=["phone_number"])
        user.refresh_from_db()
        self.assertFalse(user.phone_number_verified)
