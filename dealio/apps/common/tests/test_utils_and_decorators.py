from unittest.mock import Mock

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from rest_framework.exceptions import ValidationError

from dealio.apps.common.helpers.decorators.cache_result import cache_result, make_cache_key
from dealio.apps.common.helpers.decorators.retry import retry
from dealio.apps.common.helpers.decorators.validate_http_methods import allowed_methods
from dealio.apps.common.helpers.validators.account_validators import (
    validate_english_username,
    validate_gmail_email,
    validate_iranian_phone_number,
    validate_persian_text,
)
from dealio.apps.common.utils.common_utils import CommonUtils, PayloadNormalizer


class CommonUtilsTests(SimpleTestCase):
    @override_settings(PROJECT_STATIC_ASSET_ROOT="static/project-assets")
    def test_static_path_is_normalized_without_duplicate_prefix(self):
        self.assertEqual(CommonUtils.build_project_static_path("/images/logo.svg"), "project-assets/images/logo.svg")
        self.assertEqual(CommonUtils.build_project_static_path("project-assets/css/app.css"), "project-assets/css/app.css")

    def test_payload_normalizer_decodes_nested_binary_values_and_keys(self):
        payload = {b"key": [b"value", {b"nested": bytearray(b"ok")}]} 

        self.assertEqual(
            PayloadNormalizer.decode_messages_of_response(payload),
            {"key": ["value", {"nested": "ok"}]},
        )

    def test_get_client_ip_prefers_forwarded_header(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2", REMOTE_ADDR="3.3.3.3")

        self.assertEqual(CommonUtils.get_client_ip(request), "1.1.1.1")


class CommonValidatorTests(SimpleTestCase):
    def test_validators_normalize_supported_values(self):
        self.assertEqual(validate_iranian_phone_number(" 09123456789 "), "09123456789")
        self.assertEqual(validate_gmail_email(" USER@GMAIL.COM "), "user@gmail.com")
        self.assertEqual(validate_persian_text(" علی رضایی "), "علی رضایی")
        self.assertEqual(validate_english_username(" Amir.dev "), "Amir.dev")

    def test_validators_reject_invalid_values(self):
        invalid_calls = [
            lambda: validate_iranian_phone_number("123"),
            lambda: validate_gmail_email("user@example.com"),
            lambda: validate_persian_text("Ali"),
            lambda: validate_english_username("1invalid"),
        ]

        for call in invalid_calls:
            with self.subTest(call=call), self.assertRaises(ValidationError):
                call()


class DecoratorTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_cache_result_executes_function_once_per_argument_set(self):
        calls = []

        @cache_result(timeout=60)
        def calculate(value):
            calls.append(value)
            return value * 2

        self.assertEqual(calculate(3), 6)
        self.assertEqual(calculate(3), 6)
        self.assertEqual(calls, [3])

    def test_make_cache_key_is_stable_for_equivalent_calls(self):
        def target(value):
            return value

        first = make_cache_key(target, (1,), {"name": "x"})
        second = make_cache_key(target, (1,), {"name": "x"})

        self.assertEqual(first, second)

    def test_retry_returns_after_transient_failures(self):
        attempts = []

        def operation():
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("transient")
            return "ok"

        wrapped = retry(tries=3, delay=0)(operation)

        self.assertEqual(wrapped(), "ok")
        self.assertEqual(len(attempts), 3)

    def test_allowed_methods_returns_405_for_disallowed_method(self):
        @allowed_methods(["POST"])
        def endpoint(request):
            return "ok"

        response = endpoint(RequestFactory().get("/"))

        self.assertEqual(response.status_code, 405)
