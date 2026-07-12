from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from dealio.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from dealio.tests.mixins import IsolatedServiceTestMixin


class VerificationCodeCacheAdapterTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.adapter = VerificationCodeCacheAdapter()

    def test_generated_code_is_always_six_digits(self):
        for _ in range(20):
            code = self.adapter.generate_code()
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isdigit())

    @patch.object(VerificationCodeCacheAdapter, "generate_code", return_value="123456")
    def test_issue_code_stores_only_hash(self, _generate_mock):
        code = self.adapter.issue_code(cache_key="verification:test")

        self.assertEqual(code, "123456")
        self.assertEqual(
            cache.get("verification:test"),
            self.adapter.hash_code("123456"),
        )
        self.assertNotEqual(cache.get("verification:test"), "123456")


    @patch.object(VerificationCodeCacheAdapter, "generate_code", side_effect=["123456", "654321"])
    def test_issue_code_does_not_replace_unexpired_code(self, _generate_mock):
        first_code = self.adapter.issue_code(cache_key="verification:test")
        second_code = self.adapter.issue_code(cache_key="verification:test")

        self.assertEqual(first_code, "123456")
        self.assertIsNone(second_code)
        self.assertEqual(
            cache.get("verification:test"),
            self.adapter.hash_code("123456"),
        )

    def test_wrong_code_does_not_consume_valid_code(self):
        self.adapter.store_code(cache_key="verification:test", code="123456")

        is_valid = self.adapter.verify_code(
            cache_key="verification:test",
            code="999999",
        )

        self.assertFalse(is_valid)
        self.assertIsNotNone(cache.get("verification:test"))

    def test_valid_code_is_consumed_once(self):
        self.adapter.store_code(cache_key="verification:test", code="123456")

        self.assertTrue(
            self.adapter.verify_code(
                cache_key="verification:test",
                code="123456",
            )
        )
        self.assertFalse(
            self.adapter.verify_code(
                cache_key="verification:test",
                code="123456",
            )
        )
