from unittest.mock import MagicMock, patch

from django.test import TestCase

from dealio.apps.accounts.dtos.phone_verification_dto import (
    PhoneVerificationResultDTO,
)
from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationErrorCodeVO,
)
from dealio.apps.telegram_bot.bale_services import BaleBotService
from dealio.apps.telegram_bot.rubika_services import RubikaBotService
from dealio.apps.telegram_bot.services import TelegramBotService
from dealio.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO
from dealio.tests.factories import TelegramProfileFactory, UserFactory
from dealio.tests.mixins import IsolatedServiceTestMixin


class BotPhoneVerificationTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            phone_number="09121234567",
            phone_number_verified=False,
            email_verified=True,
        )
        self.profile = TelegramProfileFactory.create(
            user=self.user,
            is_verified=True,
            bot_language=TelegramBotLanguageVO.EN,
        )
        self.client = MagicMock()
        self.account_logic = MagicMock()
        self.service = TelegramBotService(
            client=self.client,
            account_logic=self.account_logic,
            commerce_logic=MagicMock(),
            channel_sync_logic=MagicMock(),
            notification_logic=MagicMock(),
            support_logic=MagicMock(),
        )
        self.web_app_patcher = patch.object(
            TelegramBotService,
            "web_app_url",
            return_value="",
        )
        self.web_app_patcher.start()
        self.addCleanup(self.web_app_patcher.stop)

    def test_start_phone_verification_delegates_to_account_logic_and_opens_code_flow(self):
        self.account_logic.send_phone_verification_code.return_value = (
            PhoneVerificationResultDTO.success()
        )

        self.service.start_verify_phone_flow(self.profile)

        dto = self.account_logic.send_phone_verification_code.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(self.user.id))
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_CODE,
        )
        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("09121234567", sent_text)

    def test_start_phone_verification_reports_missing_phone_without_opening_flow(self):
        self.user.phone_number = None
        self.user.save(update_fields=["phone_number"])
        self.profile.refresh_from_db()
        self.account_logic.send_phone_verification_code.return_value = (
            PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED,
            )
        )

        self.service.start_verify_phone_flow(self.profile)

        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("No phone number", sent_text)

    def test_invalid_phone_verification_code_keeps_flow_open(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_CODE,
        )
        self.account_logic.verify_phone_number.return_value = (
            PhoneVerificationResultDTO.failed(
                error_code=AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE,
            )
        )

        self.service.handle_verify_phone_code_text(self.profile, "123456")

        dto = self.account_logic.verify_phone_number.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(self.user.id))
        self.assertEqual(dto.code, "123456")
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_CODE,
        )
        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("Invalid or expired phone", sent_text)

    def test_successful_phone_verification_closes_flow_and_updates_menu_state(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_CODE,
        )
        self.account_logic.verify_phone_number.return_value = (
            PhoneVerificationResultDTO.success()
        )

        self.service.handle_verify_phone_code_text(self.profile, "654321")

        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        self.assertTrue(self.profile.user.phone_number_verified)
        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("verified successfully", sent_text)

    def test_phone_verification_button_is_visible_only_while_unverified(self):
        unverified_keyboard = self.service.main_menu_keyboard(self.profile)
        unverified_buttons = {
            button.get("text")
            for row in unverified_keyboard["keyboard"]
            for button in row
            if isinstance(button, dict)
        }

        self.assertIn(
            self.service.button(self.profile, "verify_phone"),
            unverified_buttons,
        )

        self.profile.user.phone_number_verified = True
        verified_keyboard = self.service.main_menu_keyboard(self.profile)
        verified_buttons = {
            button.get("text")
            for row in verified_keyboard["keyboard"]
            for button in row
            if isinstance(button, dict)
        }

        self.assertNotIn(
            self.service.button(self.profile, "verify_phone"),
            verified_buttons,
        )

    def test_phone_button_text_starts_flow(self):
        self.account_logic.send_phone_verification_code.return_value = (
            PhoneVerificationResultDTO.success()
        )

        handled = self.service._handle_menu_button(
            self.profile,
            self.service.button(self.profile, "verify_phone"),
        )

        self.assertTrue(handled)
        self.account_logic.send_phone_verification_code.assert_called_once()

    def test_account_view_shows_email_and_phone_verification_statuses(self):
        self.service.handle_account(self.profile, MagicMock())

        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("Email verified: <code>yes</code>", sent_text)
        self.assertIn("Phone verified: <code>no</code>", sent_text)

    def test_phone_verification_flow_is_available_to_all_messenger_services(self):
        service_classes = (TelegramBotService, BaleBotService, RubikaBotService)

        for service_class in service_classes:
            with self.subTest(service=service_class.__name__):
                client = MagicMock()
                service = service_class(client=client)
                service.account_logic = MagicMock()
                service.account_logic.send_phone_verification_code.return_value = (
                    PhoneVerificationResultDTO.success()
                )

                service.start_verify_phone_flow(self.profile)

                service.account_logic.send_phone_verification_code.assert_called_once()
                self.assertEqual(
                    service.get_action(self.profile.chat_id),
                    service.STATE_VERIFY_PHONE_CODE,
                )
                service.clear_action(self.profile.chat_id)
