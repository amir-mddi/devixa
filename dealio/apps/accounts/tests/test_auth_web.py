from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from dealio.apps.accounts.enums.oauth_enums import OAuthSessionKeyEnum
from dealio.apps.accounts.web.oauth_views import (
    GoogleOAuthWebCallbackView,
    GoogleOAuthWebStartView,
)
from dealio.apps.accounts.web.views import ForgotPasswordPageView, LoginPageView
from dealio.apps.accounts.enums.recaptcha_enums import RecaptchaFailureReasonEnum
from dealio.apps.accounts.entities.recaptcha_entity import RecaptchaVerificationResultEntity
from dealio.tests.factories import ProjectConfigFactory, UserFactory


class FakeOAuthLogic:
    def build_authorization_url(self, dto):
        return f"https://provider.example/authorize?state={dto.state}"


class FakeOAuthService:
    user = None

    def authenticate(self, *, provider: str, code: str, redirect_uri: str):
        return SimpleNamespace(user=self.user)


class FakePasswordRecoveryLogic:
    last_sms_dto = None

    def send_forget_password_code_by_sms(self, *, dto):
        type(self).last_sms_dto = dto
        return SimpleNamespace(is_success=True)


class FakeRejectedRecaptchaLogic:
    last_dto = None

    def verify(self, dto):
        type(self).last_dto = dto
        return RecaptchaVerificationResultEntity(
            is_allowed=False,
            reason=RecaptchaFailureReasonEnum.SCORE_TOO_LOW,
            score=0.1,
            hostname="acdevixa.ir",
        )


class AccountAuthWebTests(TestCase):
    def setUp(self):
        ProjectConfigFactory.create()
        self.rate_limit_patcher = patch(
            "dealio.apps.common.helpers.decorators.rate_limit.is_rate_limit_allowed",
            return_value=True,
        )
        self.rate_limit_patcher.start()
        self.addCleanup(self.rate_limit_patcher.stop)


    def test_login_rate_limit_is_rendered_inside_login_page(self):
        with patch(
            "dealio.apps.common.helpers.decorators.rate_limit.is_rate_limit_allowed",
            return_value=False,
        ):
            response = self.client.post(
                reverse("accounts_web:login"),
                {
                    "identifier": "user@gmail.com",
                    "password": "password",
                },
                HTTP_ACCEPT="text/html",
            )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")
        self.assertEqual(response["Retry-After"], "300")
        self.assertContains(response, "تعداد درخواست‌های شما بیش از حد مجاز است", status_code=429)
        self.assertContains(response, 'name="identifier"', status_code=429)
        self.assertNotContains(response, '"detail"', status_code=429)

    def test_missing_csrf_token_is_rendered_inside_login_page(self):
        csrf_client = Client(enforce_csrf_checks=True)

        response = csrf_client.post(
            reverse("accounts_web:login"),
            {
                "identifier": "user@gmail.com",
                "password": "password",
            },
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")
        self.assertContains(response, "توکن امنیتی فرم ارسال نشده است", status_code=403)
        self.assertContains(response, 'name="identifier"', status_code=403)
        self.assertNotContains(response, "CSRF verification failed", status_code=403)

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="",
        GOOGLE_OAUTH_CLIENT_SECRET="",
        GITHUB_OAUTH_CLIENT_ID="",
        GITHUB_OAUTH_CLIENT_SECRET="",
    )
    def test_login_page_always_shows_oauth_providers(self):
        response = self.client.get(reverse("accounts_web:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("accounts_web:oauth_google_start"))
        self.assertContains(response, reverse("accounts_web:oauth_github_start"))
        self.assertContains(response, "Google")
        self.assertContains(response, "GitHub")

    def test_forgot_password_can_send_sms_recovery_code(self):
        FakePasswordRecoveryLogic.last_sms_dto = None
        with patch.object(
            ForgotPasswordPageView,
            "account_logic_repository_class",
            FakePasswordRecoveryLogic,
        ):
            response = self.client.post(
                reverse("accounts_web:forgot_password"),
                {
                    "method": "sms",
                    "phone_number": "09121234567",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("method=sms", response.url)
        self.assertIn("phone_number=09121234567", response.url)
        self.assertEqual(
            FakePasswordRecoveryLogic.last_sms_dto.phone_number,
            "09121234567",
        )

    @override_settings(
        OAUTH_ALLOWED_REDIRECT_URIS=[
            "https://example.test/oauth/google/callback/",
        ],
        GOOGLE_OAUTH_WEB_REDIRECT_URI="https://example.test/oauth/google/callback/",
    )
    def test_google_oauth_browser_flow_logs_in_existing_user(self):
        user = UserFactory.create(email="existing@gmail.com")
        FakeOAuthService.user = user

        with patch.object(
            GoogleOAuthWebStartView,
            "oauth_logic_class",
            FakeOAuthLogic,
        ):
            start_response = self.client.get(
                reverse("accounts_web:oauth_google_start")
            )

        self.assertEqual(start_response.status_code, 302)
        self.assertTrue(start_response.url.startswith("https://provider.example/"))
        state = self.client.session[OAuthSessionKeyEnum.FLOW.value][
            OAuthSessionKeyEnum.STATE.value
        ]

        with patch.object(
            GoogleOAuthWebCallbackView,
            "oauth_service_class",
            FakeOAuthService,
        ):
            callback_response = self.client.get(
                reverse("accounts_web:oauth_google_callback"),
                {"state": state, "code": "provider-code"},
            )

        self.assertEqual(callback_response.status_code, 302)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(user.pk),
        )
        self.assertNotIn(OAuthSessionKeyEnum.FLOW.value, self.client.session)

    @override_settings(
        OAUTH_ALLOWED_REDIRECT_URIS=[
            "https://example.test/oauth/google/callback/",
        ],
        GOOGLE_OAUTH_WEB_REDIRECT_URI="https://example.test/oauth/google/callback/",
    )
    def test_invalid_oauth_state_does_not_consume_active_session_state(self):
        with patch.object(
            GoogleOAuthWebStartView,
            "oauth_logic_class",
            FakeOAuthLogic,
        ):
            self.client.get(reverse("accounts_web:oauth_google_start"))

        response = self.client.get(
            reverse("accounts_web:oauth_google_callback"),
            {"state": "invalid-state", "code": "provider-code"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(OAuthSessionKeyEnum.FLOW.value, self.client.session)

    @override_settings(
        RECAPTCHA_ENABLED=True,
        RECAPTCHA_SITE_KEY="public-test-key",
        RECAPTCHA_SECRET_KEY="private-test-key",
        RECAPTCHA_MIN_SCORE=0.5,
        RECAPTCHA_ALLOWED_HOSTNAMES=["acdevixa.ir"],
        RECAPTCHA_SEND_REMOTE_IP=True,
    )
    def test_login_page_renders_recaptcha_v3_configuration(self):
        response = self.client.get(reverse("accounts_web:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "public-test-key")
        self.assertContains(response, 'data-recaptcha-action="login"')
        self.assertContains(response, "google.com/recaptcha/api.js")

    @override_settings(
        RECAPTCHA_ENABLED=True,
        RECAPTCHA_SITE_KEY="public-test-key",
        RECAPTCHA_SECRET_KEY="private-test-key",
        RECAPTCHA_MIN_SCORE=0.5,
        RECAPTCHA_ALLOWED_HOSTNAMES=["acdevixa.ir"],
        RECAPTCHA_SEND_REMOTE_IP=True,
    )
    def test_login_is_blocked_when_recaptcha_is_rejected(self):
        FakeRejectedRecaptchaLogic.last_dto = None
        with patch.object(
            LoginPageView,
            "recaptcha_logic_class",
            FakeRejectedRecaptchaLogic,
        ):
            response = self.client.post(
                reverse("accounts_web:login"),
                {
                    "identifier": "user@gmail.com",
                    "password": "password",
                    "recaptcha_token": "provider-token",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اعتبارسنجی امنیتی ناموفق بود")
        self.assertEqual(
            FakeRejectedRecaptchaLogic.last_dto.expected_action.value,
            "login",
        )

