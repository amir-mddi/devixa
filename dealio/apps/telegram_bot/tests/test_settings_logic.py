from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from dealio.apps.telegram_bot.dtos.bot_setting_dtos import BotSettingDefinitionDTO
from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingValueTypeEnum
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotSettingLogicRepository
from dealio.apps.telegram_bot.serializers import BotSettingsUpdateSerializer
from dealio.apps.telegram_bot.vo.bot_setting_vo import BotSecretMaskVO


class BotSettingsSerializerTests(SimpleTestCase):
    def test_accepts_database_only_update(self):
        serializer = BotSettingsUpdateSerializer(data={"settings": {"list_page_size": 10}})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_env_writes_and_disabled_database_writes(self):
        for payload in (
            {"settings": {}, "write_to_env": True},
            {"settings": {}, "write_to_database": False},
        ):
            with self.subTest(payload=payload):
                serializer = BotSettingsUpdateSerializer(data=payload)
                self.assertFalse(serializer.is_valid())


class BotSettingLogicTests(SimpleTestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.logic = BotSettingLogicRepository(repository=self.repository)

    def _definition(self, value_type, **overrides):
        values = {
            "provider": "telegram",
            "key": "test_key",
            "env_name": "TEST_KEY",
            "label": "Test",
            "value_type": value_type,
        }
        values.update(overrides)
        return BotSettingDefinitionDTO(**values)

    def test_normalize_boolean_integer_and_url_values(self):
        self.assertEqual(
            self.logic.normalize_value(definition=self._definition(BotSettingValueTypeEnum.BOOL.value), raw_value="YES"),
            "true",
        )
        self.assertEqual(
            self.logic.normalize_value(definition=self._definition(BotSettingValueTypeEnum.INT.value), raw_value="12"),
            "12",
        )
        self.assertEqual(
            self.logic.normalize_value(definition=self._definition(BotSettingValueTypeEnum.URL.value), raw_value="https://example.com"),
            "https://example.com",
        )

    def test_normalize_rejects_invalid_url(self):
        with self.assertRaises(ValidationError):
            self.logic.normalize_value(
                definition=self._definition(BotSettingValueTypeEnum.URL.value),
                raw_value="not-a-url",
            )

    def test_masked_secret_is_not_written_back(self):
        self.repository.get_value.return_value = None

        response = self.logic.update_provider_settings(
            provider="telegram",
            raw_settings={"bot_token": BotSecretMaskVO.MASK},
        )

        self.repository.set_value.assert_not_called()
        self.assertEqual(response["updated_keys"], [])

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.logic.provider_settings("unknown")
