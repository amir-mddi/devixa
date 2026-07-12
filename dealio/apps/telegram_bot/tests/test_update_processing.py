from unittest.mock import MagicMock

from django.test import SimpleTestCase

from dealio.apps.telegram_bot.application_services.webhook_service import BotWebhookService
from dealio.apps.telegram_bot.dtos.bot_update_dtos import BotUpdateProcessDTO
from dealio.apps.telegram_bot.logic.update_process_logic import BotUpdateProcessLogic


class BotWebhookServiceTests(SimpleTestCase):
    def test_empty_expected_secret_fails_closed(self):
        self.assertFalse(BotWebhookService.validate_secret(expected_secret="", provided_secret="anything"))

    def test_configured_secret_requires_constant_time_match(self):
        self.assertTrue(BotWebhookService.validate_secret(expected_secret="secret", provided_secret="secret"))
        self.assertFalse(BotWebhookService.validate_secret(expected_secret="secret", provided_secret="wrong"))


class BotUpdateProcessLogicTests(SimpleTestCase):
    def setUp(self):
        self.runtime_repository = MagicMock()
        self.update_log_repository = MagicMock()
        self.logic = BotUpdateProcessLogic(
            runtime_repository=self.runtime_repository,
            update_log_repository=self.update_log_repository,
        )
        self.dto = BotUpdateProcessDTO(provider="telegram", update={"update_id": 10}, update_id=10)

    def test_process_marks_new_update_as_processed(self):
        update_log = MagicMock(processed=False)
        self.update_log_repository.get_or_create.return_value = (update_log, True)

        result = self.logic.process(self.dto)

        self.assertTrue(result)
        self.runtime_repository.process_update.assert_called_once_with(self.dto.update)
        self.update_log_repository.mark_processed.assert_called_once_with(update_log)

    def test_process_skips_already_processed_duplicate(self):
        update_log = MagicMock(processed=True)
        self.update_log_repository.get_or_create.return_value = (update_log, False)

        result = self.logic.process(self.dto)

        self.assertFalse(result)
        self.runtime_repository.process_update.assert_not_called()

    def test_process_records_error_and_reraises(self):
        update_log = MagicMock(processed=False)
        self.update_log_repository.get_or_create.return_value = (update_log, True)
        self.runtime_repository.process_update.side_effect = RuntimeError("boom")

        with self.assertRaisesMessage(RuntimeError, "boom"):
            self.logic.process(self.dto)

        self.update_log_repository.mark_error.assert_called_once_with(update_log, "RuntimeError")
        self.update_log_repository.mark_processed.assert_not_called()

    def test_process_without_update_id_does_not_create_log(self):
        dto = BotUpdateProcessDTO(provider="telegram", update={"message": {}}, update_id=None)

        self.assertTrue(self.logic.process(dto))
        self.update_log_repository.get_or_create.assert_not_called()
