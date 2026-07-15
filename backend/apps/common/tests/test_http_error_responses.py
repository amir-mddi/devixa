from __future__ import annotations

from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.common.web.error_views import csrf_failure


class HttpErrorResponseTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_rate_limit_keeps_json_for_api_clients(self):
        @rate_limit(anonymous_limit=1, period=90)
        def endpoint(request):
            raise AssertionError("The throttled endpoint must not execute.")

        request = self.factory.post(
            "/api/example/",
            HTTP_ACCEPT="application/json",
            REMOTE_ADDR="127.0.0.1",
        )

        with patch(
            "backend.apps.common.helpers.decorators.rate_limit.is_rate_limit_allowed",
            return_value=False,
        ):
            response = endpoint(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response["Retry-After"], "90")
        self.assertJSONEqual(
            response.content,
            {
                "code": "rate_limit_exceeded",
                "detail": (
                    "تعداد درخواست‌های شما بیش از حد مجاز است. "
                    "لطفاً 90 ثانیه دیگر دوباره تلاش کنید."
                ),
                "waiting_time": 90,
            },
        )

    def test_csrf_failure_keeps_json_for_api_clients(self):
        request = self.factory.post(
            "/api/example/",
            HTTP_ACCEPT="application/json",
        )

        response = csrf_failure(request, reason="CSRF token missing.")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertJSONEqual(
            response.content,
            {
                "code": "csrf_token_missing",
                "detail": (
                    "توکن امنیتی فرم ارسال نشده است. صفحه را تازه‌سازی کنید "
                    "و فرم را دوباره بفرستید."
                ),
            },
        )
