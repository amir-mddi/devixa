import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dealio.apps.telegram_bot.models import TelegramUpdateLog
from dealio.apps.telegram_bot.repositories.adapters.bot_http_transport import (
    BotProviderHttpTransport,
    BotProviderTransportError,
)
from dealio.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import (
    TelegramBotPostgresAdapter,
)


class _FakeResponse:
    def __init__(self, payload, *, status_code=200, headers=None):
        self.status_code = status_code
        self.encoding = "utf-8"
        self.headers = headers or {}
        self.closed = False
        self._body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()

    def iter_content(self, chunk_size=64 * 1024):
        for offset in range(0, len(self._body), chunk_size):
            yield self._body[offset:offset + chunk_size]

    def close(self):
        self.closed = True


class BotProviderHttpTransportSecurityTests(SimpleTestCase):
    @patch("dealio.apps.telegram_bot.repositories.adapters.bot_http_transport.requests.post")
    def test_provider_error_does_not_expose_tokenized_url_or_response_body(self, post_mock):
        response = _FakeResponse(
            {"description": "provider-body-secret"},
            status_code=500,
        )
        post_mock.return_value = response

        with self.assertRaises(BotProviderTransportError) as raised:
            BotProviderHttpTransport.post_json(
                url="https://api.telegram.org/botSUPER-SECRET-TOKEN/sendMessage",
                method_name="sendMessage",
                payload={"chat_id": "1"},
                timeout=(3, 10),
                proxies=None,
                provider_name="Telegram",
            )

        message = str(raised.exception)
        self.assertNotIn("SUPER-SECRET-TOKEN", message)
        self.assertNotIn("provider-body-secret", message)
        self.assertTrue(response.closed)

    @override_settings(BOT_PROVIDER_MAX_RESPONSE_BYTES=1024)
    @patch("dealio.apps.telegram_bot.repositories.adapters.bot_http_transport.requests.post")
    def test_oversized_bot_provider_response_is_rejected(self, post_mock):
        response = _FakeResponse(b"{" + b"x" * 2048 + b"}")
        post_mock.return_value = response

        with self.assertRaises(BotProviderTransportError):
            BotProviderHttpTransport.post_json(
                url="https://api.telegram.org/botTOKEN/getMe",
                method_name="getMe",
                payload={},
                timeout=(3, 10),
                proxies=None,
                provider_name="Telegram",
            )

        self.assertTrue(response.closed)

    def test_invalid_method_name_is_rejected_before_request(self):
        with self.assertRaises(BotProviderTransportError):
            BotProviderHttpTransport.post_json(
                url="https://api.telegram.org/botTOKEN/getMe",
                method_name="../getMe",
                payload={},
                timeout=(3, 10),
                proxies=None,
                provider_name="Telegram",
            )


class BotUpdateLogPrivacyTests(TestCase):
    def test_raw_message_contact_and_code_are_not_persisted(self):
        payload = {
            "update_id": 123,
            "message": {
                "text": "123456",
                "contact": {"phone_number": "+989121234567"},
            },
        }

        update_log, created = TelegramBotPostgresAdapter.get_or_create_update_log(
            provider="telegram",
            update_id=123,
            payload=payload,
        )

        self.assertTrue(created)
        self.assertEqual(update_log.payload["event_type"], "message")
        persisted = json.dumps(update_log.payload)
        self.assertNotIn("123456", persisted)
        self.assertNotIn("989121234567", persisted)
        self.assertNotIn("contact", persisted)

    def test_invalid_update_id_is_rejected(self):
        with self.assertRaises(ValueError):
            TelegramBotPostgresAdapter.get_or_create_update_log(
                provider="telegram",
                update_id="not-an-integer",
                payload={},
            )


class BotWebhookPayloadSecurityTests(APITestCase):
    @patch("dealio.apps.telegram_bot.views.BotRuntimeConfigProvider.get_env", return_value="expected-secret")
    def test_missing_update_id_is_rejected_before_processing(self, _secret_mock):
        response = self.client.post(
            reverse("telegram-webhook"),
            {"message": {"text": "hello"}},
            format="json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="expected-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertFalse(TelegramUpdateLog.objects.exists())
