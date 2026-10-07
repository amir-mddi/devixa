from unittest.mock import patch

from django.test import SimpleTestCase

from backend.apps.shared.repositories.adapters.project_public_env_adapter import (
    ProjectPublicEnvAdapter,
)


class ProjectPublicEnvAdapterTests(SimpleTestCase):
    def test_reads_public_contact_channel_and_bot_values_from_env(self):
        env = {
            "PROJECT_CONTACT_EMAIL": "hello@acdevixa.ir",
            "PROJECT_PHONE": "+989121234567",
            "PROJECT_TELEGRAM_URL": "https://t.me/devixa",
            "PROJECT_BALE_URL": "https://ble.ir/devixa",
            "PROJECT_INSTAGRAM_URL": "https://instagram.com/devixa",
            "PROJECT_TELEGRAM_BOT_URL": "https://t.me/devixa_bot",
            "PROJECT_BALE_BOT_URL": "https://ble.ir/devixa_bot",
            "PROJECT_RUBIKA_BOT_URL": "https://rubika.ir/devixa_bot",
        }

        with patch.dict("os.environ", env, clear=True):
            result = ProjectPublicEnvAdapter().read()

        self.assertEqual(result.contact_email, env["PROJECT_CONTACT_EMAIL"])
        self.assertEqual(result.phone, env["PROJECT_PHONE"])
        self.assertEqual(result.telegram_url, env["PROJECT_TELEGRAM_URL"])
        self.assertEqual(result.telegram_bot_url, env["PROJECT_TELEGRAM_BOT_URL"])
        self.assertEqual(result.rubika_bot_url, env["PROJECT_RUBIKA_BOT_URL"])

    def test_upgrades_http_public_links_to_https(self):
        with patch.dict(
            "os.environ",
            {"PROJECT_TELEGRAM_URL": "http://t.me/devixa"},
            clear=True,
        ):
            result = ProjectPublicEnvAdapter().read()

        self.assertEqual(result.telegram_url, "https://t.me/devixa")

    def test_discards_private_or_invalid_public_links(self):
        with patch.dict(
            "os.environ",
            {"PROJECT_TELEGRAM_URL": "http://127.0.0.1/private"},
            clear=True,
        ):
            result = ProjectPublicEnvAdapter().read()

        self.assertEqual(result.telegram_url, "")
