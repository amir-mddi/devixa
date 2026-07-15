from unittest.mock import MagicMock, patch

from django.test import TestCase

from backend.apps.telegram_bot.services import TelegramBotService
from backend.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO
from backend.tests.factories import TelegramProfileFactory, UserFactory
from backend.tests.mixins import IsolatedServiceTestMixin


class BotPasswordRecoveryTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            email="recovery@gmail.com",
            phone_number="09121234567",
            phone_number_verified=True,
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

    def test_forgot_password_flow_shows_email_and_phone_buttons(self):
        self.service.start_forgot_password_flow(self.profile)

        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )
        reply_markup = self.client.send_message.call_args.kwargs["reply_markup"]
        button_texts = {
            button["text"]
            for row in reply_markup["keyboard"]
            for button in row
        }
        self.assertIn(
            self.service.button(self.profile, "forgot_by_email"),
            button_texts,
        )
        self.assertIn(
            self.service.button(self.profile, "forgot_by_phone"),
            button_texts,
        )

    def test_linked_user_can_request_recovery_by_email(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )

        self.service.handle_forgot_password_method_text(
            self.profile,
            self.service.button(self.profile, "forgot_by_email"),
        )

        dto = self.account_logic.send_forget_password_code_by_email.call_args.args[0]
        self.assertEqual(dto.email, self.user.email)
        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        self.assertIn("email recovery code", self.client.send_message.call_args.args[1])

    def test_linked_user_can_request_recovery_by_verified_phone(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )

        self.service.handle_forgot_password_method_text(
            self.profile,
            self.service.button(self.profile, "forgot_by_phone"),
        )

        dto = self.account_logic.send_forget_password_code_by_sms.call_args.args[0]
        self.assertEqual(dto.phone_number, self.user.phone_number)
        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        self.assertIn("SMS recovery code", self.client.send_message.call_args.args[1])

    def test_phone_recovery_requires_verified_phone_for_linked_user(self):
        self.user.phone_number_verified = False
        self.user.save(update_fields=["phone_number_verified"])
        self.profile.refresh_from_db()
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )

        self.service.handle_forgot_password_method_text(
            self.profile,
            self.service.button(self.profile, "forgot_by_phone"),
        )

        self.account_logic.send_forget_password_code_by_sms.assert_not_called()
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )
        self.assertIn("no verified phone", self.client.send_message.call_args.args[1])

    def test_unlinked_user_is_prompted_for_selected_email(self):
        self.profile.user = None
        self.profile.is_verified = False
        self.profile.save(update_fields=["user", "is_verified"])
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_FORGOT_PASSWORD_METHOD,
        )

        self.service.handle_forgot_password_method_text(
            self.profile,
            self.service.button(self.profile, "forgot_by_email"),
        )

        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_FORGOT_PASSWORD_EMAIL,
        )
        self.assertIn("Send your account email", self.client.send_message.call_args.args[1])

    def test_unlinked_user_phone_input_is_normalized_before_logic(self):
        self.profile.user = None
        self.profile.is_verified = False
        self.profile.save(update_fields=["user", "is_verified"])
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_FORGOT_PASSWORD_PHONE,
        )

        self.service.handle_forgot_password_phone_text(
            self.profile,
            "+989121234567",
        )

        dto = self.account_logic.send_forget_password_code_by_sms.call_args.args[0]
        self.assertEqual(dto.phone_number, "09121234567")
        self.assertIsNone(self.service.get_action(self.profile.chat_id))
