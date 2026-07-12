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
            telegram_user_id="7001",
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

    def test_start_phone_verification_shows_sms_and_telegram_methods(self):
        self.service.start_verify_phone_flow(self.profile)

        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_METHOD,
        )
        self.account_logic.send_phone_verification_code.assert_not_called()
        reply_markup = self.client.send_message.call_args.kwargs["reply_markup"]
        buttons = [button for row in reply_markup["keyboard"] for button in row]
        self.assertIn(
            {"text": self.service.button(self.profile, "verify_phone_sms")},
            buttons,
        )
        self.assertIn(
            {
                "text": self.service.button(self.profile, "verify_phone_telegram"),
                "request_contact": True,
            },
            buttons,
        )

    def test_sms_method_delegates_to_account_logic_and_opens_code_flow(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_METHOD,
        )
        self.account_logic.send_phone_verification_code.return_value = (
            PhoneVerificationResultDTO.success(code_issued=True)
        )

        self.service.handle_verify_phone_method_text(
            self.profile,
            self.service.button(self.profile, "verify_phone_sms"),
        )

        dto = self.account_logic.send_phone_verification_code.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(self.user.id))
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_CODE,
        )
        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("09121234567", sent_text)

    def test_active_sms_code_is_not_requested_again(self):
        self.account_logic.send_phone_verification_code.return_value = (
            PhoneVerificationResultDTO.success(code_issued=False)
        )

        self.service._send_phone_verification_sms(self.profile)

        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("still active", sent_text)
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_CODE,
        )

    def test_missing_phone_shows_only_telegram_share_method(self):
        self.user.phone_number = None
        self.user.save(update_fields=["phone_number"])
        self.profile.refresh_from_db()

        self.service.start_verify_phone_flow(self.profile)

        reply_markup = self.client.send_message.call_args.kwargs["reply_markup"]
        buttons = [button for row in reply_markup["keyboard"] for button in row]
        self.assertNotIn(
            {"text": self.service.button(self.profile, "verify_phone_sms")},
            buttons,
        )
        self.assertIn(
            {
                "text": self.service.button(self.profile, "verify_phone_telegram"),
                "request_contact": True,
            },
            buttons,
        )

    def test_own_telegram_contact_verifies_and_updates_phone(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_METHOD,
        )
        self.account_logic.verify_phone_number_by_telegram.return_value = (
            PhoneVerificationResultDTO.success()
        )

        self.service.handle_verify_phone_contact(
            self.profile,
            contact={"user_id": 7001, "phone_number": "+989121234567"},
            sender_user_id=7001,
        )

        dto = self.account_logic.verify_phone_number_by_telegram.call_args.kwargs["dto"]
        self.assertEqual(dto.user_id, str(self.user.id))
        self.assertEqual(dto.phone_number, "09121234567")
        self.assertTrue(self.profile.user.phone_number_verified)
        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        self.assertIn("verified successfully", self.client.send_message.call_args.args[1])

    def test_forwarded_or_other_contact_is_rejected(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_METHOD,
        )

        self.service.handle_verify_phone_contact(
            self.profile,
            contact={"user_id": 9999, "phone_number": "+989121234567"},
            sender_user_id=7001,
        )

        self.account_logic.verify_phone_number_by_telegram.assert_not_called()
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_METHOD,
        )
        self.assertIn("your own Telegram contact", self.client.send_message.call_args.args[1])

    def test_contact_message_is_processed_only_in_expected_telegram_flow(self):
        self.account_logic.verify_phone_number_by_telegram.return_value = (
            PhoneVerificationResultDTO.success()
        )
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_VERIFY_PHONE_METHOD,
        )

        handled = self.service._handle_waiting_contact(
            self.profile,
            message={
                "contact": {
                    "user_id": 7001,
                    "phone_number": "+989121234567",
                }
            },
            telegram_user={"id": 7001},
        )

        self.assertTrue(handled)
        self.account_logic.verify_phone_number_by_telegram.assert_called_once()

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
        self.assertIn(
            "Invalid or expired phone",
            self.client.send_message.call_args.args[1],
        )

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

    def test_phone_button_text_starts_method_selection(self):
        handled = self.service._handle_menu_button(
            self.profile,
            self.service.button(self.profile, "verify_phone"),
        )

        self.assertTrue(handled)
        self.account_logic.send_phone_verification_code.assert_not_called()
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_VERIFY_PHONE_METHOD,
        )

    def test_account_view_shows_email_and_phone_verification_statuses(self):
        self.service.handle_account(self.profile, MagicMock())

        sent_text = self.client.send_message.call_args.args[1]
        self.assertIn("Email verified: <code>yes</code>", sent_text)
        self.assertIn("Phone verified: <code>no</code>", sent_text)

    def test_bale_and_rubika_continue_to_use_sms_verification(self):
        for service_class in (BaleBotService, RubikaBotService):
            with self.subTest(service=service_class.__name__):
                client = MagicMock()
                service = service_class(client=client)
                service.account_logic = MagicMock()
                service.account_logic.send_phone_verification_code.return_value = (
                    PhoneVerificationResultDTO.success(code_issued=True)
                )

                service.start_verify_phone_flow(self.profile)

                service.account_logic.send_phone_verification_code.assert_called_once()
                self.assertEqual(
                    service.get_action(self.profile.chat_id),
                    service.STATE_VERIFY_PHONE_CODE,
                )
                service.clear_action(self.profile.chat_id)
