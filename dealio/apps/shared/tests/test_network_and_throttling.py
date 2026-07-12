from types import SimpleNamespace

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase

from dealio.apps.shared.enums.network_enum import NetworkType
from dealio.apps.shared.throttling import ClientIP, FixedWindowLimiter, RateLimitExceeded, RateParser


class SharedEnumTests(SimpleTestCase):
    def test_network_type_exposes_codes_and_lookup(self):
        codes = NetworkType.get_codes()

        self.assertTrue(codes)
        first_code = codes[0]
        self.assertIsNotNone(NetworkType.get_network_by_code(first_code))


class ThrottlingTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_rate_parser_supports_named_periods_and_rejects_invalid_rate(self):
        rate = RateParser.parse("10/minute")

        self.assertEqual(rate.limit, 10)
        self.assertEqual(rate.duration, 60)
        with self.assertRaises(ValueError):
            RateParser.parse("bad")

    def test_fixed_window_limiter_blocks_after_limit(self):
        limiter = FixedWindowLimiter(scope="test", rate="2/minute")

        limiter.allow("User@example.com")
        limiter.allow("user@example.com")
        with self.assertRaises(RateLimitExceeded):
            limiter.allow("USER@example.com")

    def test_client_ip_prefers_first_forwarded_address(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2")

        self.assertEqual(ClientIP.get(request), "10.0.0.1")
