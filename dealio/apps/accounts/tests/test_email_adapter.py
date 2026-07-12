from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from dealio.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter
from dealio.tests.factories import UserFactory


class AccountEmailAdapterTests(TestCase):
    def setUp(self):
        cache.clear()
        self.adapter = AccountEmailAdapter()
        self.user = UserFactory.create(email_verified=False)

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_generated_code_has_six_digits(self):
        code = self.adapter.generate_verification_code()

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    @patch("dealio.apps.accounts.repositories.adapters.email_adapter.send_html_email_async")
    @patch.object(AccountEmailAdapter, "generate_verification_code", return_value="123456")
    def test_send_verification_stores_hashed_code_and_sends_email(self, _code_mock, email_mock):
        self.adapter.send_email_verification_code(self.user)

        cache_key = self.adapter.get_email_verification_cache_key(self.user.id, self.user.email)
        self.assertEqual(cache.get(cache_key), self.adapter.hash_code("123456"))
        email_mock.assert_called_once()


    @patch("dealio.apps.accounts.repositories.adapters.email_adapter.send_html_email_async")
    @patch.object(AccountEmailAdapter, "generate_verification_code", side_effect=["123456", "654321"])
    def test_does_not_send_new_email_while_previous_code_is_active(self, _code_mock, email_mock):
        first_sent = self.adapter.send_email_verification_code(self.user)
        second_sent = self.adapter.send_email_verification_code(self.user)

        cache_key = self.adapter.get_email_verification_cache_key(self.user.id, self.user.email)
        self.assertTrue(first_sent)
        self.assertFalse(second_sent)
        self.assertEqual(cache.get(cache_key), self.adapter.hash_code("123456"))
        email_mock.assert_called_once()

    def test_verify_email_code_marks_user_verified_and_consumes_code(self):
        cache_key = self.adapter.get_email_verification_cache_key(self.user.id, self.user.email)
        cache.set(cache_key, self.adapter.hash_code("123456"), timeout=60)

        valid = self.adapter.verify_email_code(self.user, "123456")

        self.user.refresh_from_db()
        self.assertTrue(valid)
        self.assertTrue(self.user.email_verified)
        self.assertIsNone(cache.get(cache_key))

    def test_check_code_rejects_wrong_value_without_consuming_valid_code(self):
        cache_key = self.adapter.get_email_verification_cache_key(self.user.id, self.user.email)
        cache.set(cache_key, self.adapter.hash_code("123456"), timeout=60)

        self.assertFalse(self.adapter.check_code(self.user, cache_key, "999999"))
        self.assertIsNotNone(cache.get(cache_key))
