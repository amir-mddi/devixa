from unittest.mock import MagicMock, patch

from django.test import TestCase

from dealio.apps.core_models.vo.common_vo import KavenegarVo
from dealio.apps.telegram_bot.dtos.account_link_dtos import (
    ConfirmBotAccountLinkCodeDTO,
    SendBotAccountLinkCodeDTO,
)
from dealio.apps.telegram_bot.repositories.logic.account_link_logic import (
    BotAccountLinkLogicRepository,
)
from dealio.apps.telegram_bot.services import TelegramBotService, TelegramCommand
from dealio.apps.telegram_bot.vo.account_link_vo import BotAccountLinkVO
from dealio.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO
from dealio.tests.factories import TelegramProfileFactory, UserFactory
from dealio.tests.mixins import IsolatedServiceTestMixin


class BotAccountLinkServiceTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.profile = TelegramProfileFactory.create(
            user=None,
            is_verified=False,
            bot_language=TelegramBotLanguageVO.EN,
        )
        self.client = MagicMock()
        self.account_link_logic = MagicMock()
        self.service = TelegramBotService(
            client=self.client,
            account_link_logic=self.account_link_logic,
            account_logic=MagicMock(),
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

    def test_link_flow_shows_email_and_phone_methods(self):
        self.service.start_link_flow(self.profile)

        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_LINK_METHOD,
        )
        reply_markup = self.client.send_message.call_args.kwargs["reply_markup"]
        button_texts = {
            button["text"]
            for row in reply_markup["keyboard"]
            for button in row
        }
        self.assertIn(
            self.service.button(self.profile, "link_by_email"),
            button_texts,
        )
        self.assertIn(
            self.service.button(self.profile, "link_by_phone"),
            button_texts,
        )

    def test_phone_method_opens_phone_input_step(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_LINK_METHOD,
        )

        self.service.handle_link_method_text(
            self.profile,
            self.service.button(self.profile, "link_by_phone"),
        )

        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_LINK_PHONE,
        )
        self.assertIn(
            "Iranian mobile number",
            self.client.send_message.call_args.args[1],
        )

    def test_phone_input_is_normalized_and_delegated_to_link_logic(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_LINK_PHONE,
        )

        self.service.handle_link_phone_text(
            self.profile,
            "+989121234567",
        )

        dto = self.account_link_logic.send_code_by_phone.call_args.args[0]
        self.assertEqual(dto.provider, "telegram")
        self.assertEqual(dto.chat_id, str(self.profile.chat_id))
        self.assertEqual(dto.identifier, "09121234567")
        self.assertEqual(dto.language, TelegramBotLanguageVO.EN)
        self.assertEqual(
            self.service.get_action(self.profile.chat_id),
            self.service.STATE_LINK_CODE,
        )
        self.assertIn(
            "SMS connection code",
            self.client.send_message.call_args.args[1],
        )

    def test_link_command_accepts_phone_number(self):
        self.service.handle_link(
            self.profile,
            TelegramCommand(
                name="/link",
                args=["989121234567"],
                raw_text="/link 989121234567",
            ),
        )

        dto = self.account_link_logic.send_code_by_phone.call_args.args[0]
        self.assertEqual(dto.identifier, "09121234567")

    def test_successful_link_code_delegates_confirmation_and_closes_flow(self):
        self.service.set_action(
            self.profile.chat_id,
            self.service.STATE_LINK_CODE,
        )
        self.account_link_logic.confirm_code.return_value = True

        self.service.handle_link_code_text(self.profile, "123456")

        dto = self.account_link_logic.confirm_code.call_args.args[0]
        self.assertEqual(dto.provider, "telegram")
        self.assertEqual(dto.chat_id, str(self.profile.chat_id))
        self.assertEqual(dto.profile_id, self.profile.id)
        self.assertEqual(dto.code, "123456")
        self.assertIsNone(self.service.get_action(self.profile.chat_id))
        self.assertIn("linked successfully", self.client.send_message.call_args.args[1])

    def test_help_text_describes_current_account_and_recovery_flows(self):
        help_text = self.service.help_text(self.profile)

        self.assertIn("connect by registered email", help_text)
        self.assertIn("securely share your own contact", help_text)
        self.assertIn("request recovery by email or verified phone", help_text)
        self.assertIn("Contact support", help_text)


class BotAccountLinkLogicTests(IsolatedServiceTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            email="link-user@gmail.com",
            phone_number="09121234567",
            phone_number_verified=False,
        )
        self.profile = TelegramProfileFactory.create(
            user=None,
            is_verified=False,
            messenger_provider="telegram",
            bot_language=TelegramBotLanguageVO.EN,
        )
        self.email_adapter = MagicMock()
        self.shared_logic = MagicMock()
        self.logic = BotAccountLinkLogicRepository(
            email_adapter=self.email_adapter,
            shared_logic=self.shared_logic,
        )

    def test_phone_link_uses_connect_account_template(self):
        result = self.logic.send_code_by_phone(
            SendBotAccountLinkCodeDTO(
                provider="telegram",
                chat_id=str(self.profile.chat_id),
                identifier=self.user.phone_number,
                language=TelegramBotLanguageVO.EN,
            )
        )

        self.assertTrue(result.account_found)
        self.assertTrue(result.code_issued)
        sms_dto = self.shared_logic.send_sms.call_args.args[0]
        self.assertEqual(sms_dto.recipient_phone_number, self.user.phone_number)
        self.assertEqual(sms_dto.template_name, KavenegarVo.CONNECT_ACCOUNT)
        self.assertTrue(sms_dto.token.isdigit())
        self.assertEqual(len(sms_dto.token), BotAccountLinkVO.CODE_LENGTH)
        self.assertEqual(
            sms_dto.token2,
            str(BotAccountLinkVO.CODE_EXPIRATION_MINUTES),
        )

    def test_active_phone_link_code_is_not_replaced_or_sent_again(self):
        dto = SendBotAccountLinkCodeDTO(
            provider="telegram",
            chat_id=str(self.profile.chat_id),
            identifier=self.user.phone_number,
            language=TelegramBotLanguageVO.EN,
        )

        first_result = self.logic.send_code_by_phone(dto)
        second_result = self.logic.send_code_by_phone(dto)

        self.assertTrue(first_result.code_issued)
        self.assertFalse(second_result.code_issued)
        self.shared_logic.send_sms.assert_called_once()

    def test_active_email_link_code_is_not_replaced_or_sent_again(self):
        dto = SendBotAccountLinkCodeDTO(
            provider="telegram",
            chat_id=str(self.profile.chat_id),
            identifier=self.user.email,
            language=TelegramBotLanguageVO.EN,
        )

        first_result = self.logic.send_code_by_email(dto)
        second_result = self.logic.send_code_by_email(dto)

        self.assertTrue(first_result.code_issued)
        self.assertFalse(second_result.code_issued)
        self.email_adapter.send_code.assert_called_once()

    def test_phone_link_confirmation_links_profile_and_verifies_phone(self):
        self.logic.send_code_by_phone(
            SendBotAccountLinkCodeDTO(
                provider="telegram",
                chat_id=str(self.profile.chat_id),
                identifier=self.user.phone_number,
                language=TelegramBotLanguageVO.EN,
            )
        )
        code = self.shared_logic.send_sms.call_args.args[0].token

        confirmed = self.logic.confirm_code(
            ConfirmBotAccountLinkCodeDTO(
                provider="telegram",
                chat_id=str(self.profile.chat_id),
                profile_id=self.profile.id,
                code=code,
            )
        )

        self.assertTrue(confirmed)
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.profile.user_id, self.user.id)
        self.assertTrue(self.profile.is_verified)
        self.assertTrue(self.user.phone_number_verified)

    def test_missing_phone_account_does_not_send_sms(self):
        result = self.logic.send_code_by_phone(
            SendBotAccountLinkCodeDTO(
                provider="telegram",
                chat_id=str(self.profile.chat_id),
                identifier="09129999999",
                language=TelegramBotLanguageVO.EN,
            )
        )

        self.assertFalse(result.account_found)
        self.assertFalse(result.code_issued)
        self.shared_logic.send_sms.assert_not_called()
