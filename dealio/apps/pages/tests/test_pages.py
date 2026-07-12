from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from dealio.apps.pages.dtos.contact_dto import ContactMessageDTO
from dealio.apps.pages.dtos.home_content_dto import ChannelLinkDTO
from dealio.apps.pages.repositories.logic import PageLogicRepository
from dealio.apps.pages.vo.page_vo import PageErrorCodeVO
from dealio.apps.pages.web.forms import ContactMessageTemplateForm
from dealio.tests.mixins import IsolatedServiceTestMixin


class PageDTOAndFormTests(SimpleTestCase):
    def test_channel_link_availability(self):
        self.assertTrue(ChannelLinkDTO("T", "D", "https://example.com", "icon", "badge").is_available)
        self.assertFalse(ChannelLinkDTO("T", "D", "#", "icon", "badge").is_available)

    def test_contact_form_normalizes_values_and_builds_dto(self):
        form = ContactMessageTemplateForm(
            data={
                "full_name": "  Ali Reza  ",
                "email": " USER@EXAMPLE.COM ",
                "topic": "  Support  ",
                "message": "  This message is long enough for validation.  ",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        dto = form.to_dto()
        self.assertEqual(dto.email, "user@example.com")
        self.assertEqual(dto.topic, "Support")


class PageLogicRepositoryTests(IsolatedServiceTestMixin, TestCase):
    @patch("dealio.apps.pages.repositories.logic.PageLogicRepository._contact_recipient_email", return_value="")
    def test_contact_message_fails_when_recipient_is_not_configured(self, _recipient_mock):
        result = PageLogicRepository().send_contact_message(
            ContactMessageDTO("Ali", "ali@example.com", "Topic", "Message")
        )

        self.assertFalse(result.is_success)
        self.assertEqual(result.error_code, PageErrorCodeVO.EMAIL_NOT_CONFIGURED)

    @patch("dealio.apps.pages.repositories.logic.send_html_email_async")
    @patch("dealio.apps.pages.repositories.logic.get_project_public_config")
    @patch("dealio.apps.pages.repositories.logic.PageLogicRepository._contact_recipient_email", return_value="contact@example.com")
    def test_contact_message_is_queued_with_configured_recipient(self, _recipient_mock, config_mock, send_mock):
        config_mock.return_value = MagicMock(display_name="Dealio")

        result = PageLogicRepository().send_contact_message(
            ContactMessageDTO("Ali", "ali@example.com", "Topic", "Message")
        )

        self.assertTrue(result.is_success)
        send_mock.assert_called_once()

    def test_default_faq_is_used_when_no_public_bot_faq_exists(self):
        repository = PageLogicRepository()
        repository.bot_support_logic = MagicMock()
        repository.bot_support_logic.list_frequently_asked_tickets.return_value = ()

        items = repository.list_home_frequently_asked_questions(limit=2)

        self.assertEqual(len(items), 2)
