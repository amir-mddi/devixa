from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.tests.factories import UserFactory


class TelegramWebhookAPITests(APITestCase):
    @patch("backend.apps.telegram_bot.views.BotRuntimeConfigProvider.get_env", return_value="expected-secret")
    def test_get_reports_endpoint_ready_with_valid_secret(self, _secret_mock):
        response = self.client.get(
            reverse("telegram-webhook"),
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="expected-secret",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["ok"])

    def test_get_hides_endpoint_when_secret_is_not_configured(self):
        response = self.client.get(reverse("telegram-webhook"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("backend.apps.telegram_bot.views.BotRuntimeConfigProvider.get_env", return_value="expected")
    def test_post_rejects_invalid_webhook_secret(self, _secret_mock):
        response = self.client.post(
            reverse("telegram-webhook"),
            {"update_id": 1},
            format="json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("backend.apps.telegram_bot.views.BotWebhookService.process", return_value=True)
    @patch("backend.apps.telegram_bot.views.TelegramWebhookAPIView.get_client")
    @patch("backend.apps.telegram_bot.views.BotRuntimeConfigProvider.get_env", return_value="expected-secret")
    def test_post_processes_configured_client(self, _secret_mock, client_mock, process_mock):
        client_mock.return_value = MagicMock(is_configured=True)

        response = self.client.post(
            reverse("telegram-webhook"),
            {"update_id": 1},
            format="json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="expected-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["processed"])
        process_mock.assert_called_once()


class BotSettingsAPITests(APITestCase):
    def test_settings_endpoint_requires_admin(self):
        self.client.force_authenticate(UserFactory.create())

        response = self.client.get(reverse("bot-settings"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("backend.apps.telegram_bot.views.BotSettingLogicRepository.list_all", return_value=[])
    def test_admin_can_list_settings(self, list_mock):
        self.client.force_authenticate(UserFactory.create_admin())

        response = self.client.get(reverse("bot-settings"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"items": []})
        list_mock.assert_called_once()
