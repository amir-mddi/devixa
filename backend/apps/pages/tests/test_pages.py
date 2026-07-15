from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from backend.apps.pages.dtos.contact_dto import ContactMessageDTO
from backend.apps.pages.dtos.home_content_dto import ChannelLinkDTO
from backend.apps.pages.repositories.logic import PageLogicRepository
from backend.apps.pages.vo.page_vo import PageAndroidAppVO, PageErrorCodeVO
from backend.apps.pages.web.forms import ContactMessageTemplateForm
from backend.tests.mixins import IsolatedServiceTestMixin


class PageDTOAndFormTests(SimpleTestCase):
    def test_channel_link_availability(self):
        self.assertTrue(
            ChannelLinkDTO(
                "T", "D", "https://example.com", "icon", "badge"
            ).is_available
        )
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
    @patch(
        "backend.apps.pages.repositories.logic.PageLogicRepository._contact_recipient_email",
        return_value="",
    )
    def test_contact_message_fails_when_recipient_is_not_configured(
        self, _recipient_mock
    ):
        result = PageLogicRepository().send_contact_message(
            ContactMessageDTO("Ali", "ali@example.com", "Topic", "Message")
        )

        self.assertFalse(result.is_success)
        self.assertEqual(result.error_code, PageErrorCodeVO.EMAIL_NOT_CONFIGURED)

    @patch("backend.apps.pages.repositories.logic.send_html_email_async")
    @patch("backend.apps.pages.repositories.logic.get_project_public_config")
    @patch(
        "backend.apps.pages.repositories.logic.PageLogicRepository._contact_recipient_email",
        return_value="contact@example.com",
    )
    def test_contact_message_is_queued_with_configured_recipient(
        self, _recipient_mock, config_mock, send_mock
    ):
        config_mock.return_value = MagicMock(display_name="Devixa")

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


class ChannelLinkTests(SimpleTestCase):
    @patch("backend.apps.pages.repositories.logic.get_project_public_config")
    def test_channels_include_configured_rubika_bot(self, config_mock):
        config_mock.return_value = MagicMock(
            telegram_bot_url="https://t.me/devixa_bot",
            telegram_url="https://t.me/devixa",
            bale_bot_url="https://ble.ir/devixa_bot",
            rubika_bot_url="https://rubika.ir/devixa_bot",
        )

        links = PageLogicRepository().list_channel_links()

        self.assertEqual(len(links), 3)
        rubika = next(link for link in links if link.badge == "Rubika")
        self.assertEqual(rubika.url, "https://rubika.ir/devixa_bot")
        self.assertTrue(rubika.is_available)


class AndroidAppDownloadTests(SimpleTestCase):
    def test_stable_download_route_redirects_to_versioned_apk(self):
        response = self.client.get(reverse("pages_web:download_android_app"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"/static/{PageAndroidAppVO.APK_STATIC_PATH.value}",
        )

    def test_footer_uses_stable_download_route(self):
        response = self.client.get(reverse("pages_web:home"))

        self.assertContains(response, reverse("pages_web:download_android_app"))
        self.assertContains(response, "دانلود اپلیکیشن اندروید")

