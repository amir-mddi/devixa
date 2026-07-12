from unittest.mock import MagicMock

from django.test import SimpleTestCase, TestCase

from dealio.apps.telegram_bot.repositories.adapters.postgres_bot_adapter import TelegramBotPostgresAdapter
from dealio.apps.telegram_bot.repositories.bot_setting_repository import BotSettingRepository
from dealio.apps.telegram_bot.repositories.profile_repository import TelegramProfileRepository
from dealio.tests.factories import TelegramProfileFactory


class BotSettingRepositoryTests(SimpleTestCase):
    def setUp(self):
        self.postgres = MagicMock()
        self.cache = MagicMock()
        self.crypto = MagicMock()
        self.repository = BotSettingRepository(
            postgres_adapter=self.postgres,
            cache_adapter=self.cache,
            crypto_adapter=self.crypto,
        )

    def test_get_value_returns_cached_plain_value_without_database_call(self):
        self.cache.get.return_value = "cached"

        result = self.repository.get_value(provider="telegram", key="webhook_url")

        self.assertEqual(result, "cached")
        self.postgres.get_value.assert_not_called()

    def test_get_secret_decodes_cached_value(self):
        self.cache.get.return_value = "encoded"
        self.crypto.decode.return_value = "secret"

        result = self.repository.get_value(provider="telegram", key="bot_token", is_secret=True)

        self.assertEqual(result, "secret")
        self.crypto.decode.assert_called_once_with("encoded")

    def test_database_value_is_cached_before_returning(self):
        self.cache.get.return_value = None
        self.postgres.get_value.return_value = "db-value"

        result = self.repository.get_value(provider="telegram", key="webhook_url")

        self.assertEqual(result, "db-value")
        self.cache.set.assert_called_once_with("telegram", "webhook_url", "db-value")

    def test_set_secret_encodes_then_invalidates_cache(self):
        self.crypto.encode.return_value = "encoded"

        self.repository.set_value(
            provider="telegram",
            key="bot_token",
            value="secret",
            is_secret=True,
            user="actor",
        )

        self.postgres.upsert_value.assert_called_once_with(
            provider="telegram",
            key="bot_token",
            value="encoded",
            is_secret=True,
            user="actor",
        )
        self.cache.delete.assert_called_once_with("telegram", "bot_token")


class TelegramProfileRepositoryTests(TestCase):
    def test_upsert_updates_existing_profile_without_duplicate(self):
        profile = TelegramProfileFactory.create(
            messenger_provider="telegram",
            chat_id="55",
            username="old",
        )
        repository = TelegramProfileRepository(adapter=TelegramBotPostgresAdapter())

        updated = repository.upsert_profile(
            provider="telegram",
            chat_id="55",
            user_data={"id": 99, "username": "new", "first_name": "Ali"},
        )

        self.assertEqual(updated.pk, profile.pk)
        self.assertEqual(updated.username, "new")
        self.assertEqual(updated.telegram_user_id, "99")
