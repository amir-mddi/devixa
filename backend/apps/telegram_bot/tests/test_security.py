import json
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.telegram_bot.models import TelegramUpdateLog
from backend.apps.telegram_bot.repositories.adapters.bot_http_transport import (
    BotProviderHttpTransport,
    BotProviderTransportError,
)
from backend.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import (
    TelegramBotPostgresAdapter,
)


class _FakeAsyncResponse:
    def __init__(self, payload, *, status_code=200, headers=None):
        self.status_code = status_code
        self.encoding = "utf-8"
        self.headers = headers or {}
        self.closed = False
        self._body = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload).encode("utf-8")
        )

    async def aiter_bytes(self, chunk_size=64 * 1024):
        for offset in range(0, len(self._body), chunk_size):
            yield self._body[offset : offset + chunk_size]


class _FakeStreamContext:
    def __init__(self, response: _FakeAsyncResponse):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        self.response.closed = True


class _FakeAsyncClient:
    def __init__(self, response: _FakeAsyncResponse):
        self.response = response
        self.stream_kwargs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def stream(self, *args, **kwargs):
        self.stream_kwargs = kwargs
        return _FakeStreamContext(self.response)


class BotProviderHttpTransportSecurityTests(SimpleTestCase):
    @patch(
        "backend.apps.telegram_bot.repositories.adapters.bot_http_transport.httpx.AsyncClient"
    )
    def test_provider_error_does_not_expose_tokenized_url_or_response_body(
        self,
        client_mock,
    ):
        response = _FakeAsyncResponse(
            {"description": "provider-body-secret"},
            status_code=500,
        )
        client_mock.return_value = _FakeAsyncClient(response)

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
    @patch(
        "backend.apps.telegram_bot.repositories.adapters.bot_http_transport.httpx.AsyncClient"
    )
    def test_oversized_bot_provider_response_is_rejected(self, client_mock):
        response = _FakeAsyncResponse(b"{" + b"x" * 2048 + b"}")
        client_mock.return_value = _FakeAsyncClient(response)

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
    @patch(
        "backend.apps.telegram_bot.views.BotRuntimeConfigProvider.get_env",
        return_value="expected-secret",
    )
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
