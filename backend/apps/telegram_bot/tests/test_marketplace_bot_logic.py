from unittest.mock import MagicMock

from django.test import SimpleTestCase

from backend.apps.telegram_bot.controllers.marketplace_controller import MarketplaceBotController
from backend.apps.telegram_bot.logic.marketplace_bot_logic import MarketplaceBotLogic
from backend.apps.telegram_bot.vo.marketplace_vo import MarketplaceBotCallbackVO, MarketplaceBotSection


class MarketplaceBotLogicTests(SimpleTestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.usecases = MagicMock()
        self.logic = MarketplaceBotLogic(repository=self.repo, usecases=self.usecases)

    def test_menu_has_native_callbacks_without_website_url(self):
        screen = self.logic.menu("fa")
        self.assertEqual([row[0]["callback_data"] for row in screen.keyboard["inline_keyboard"]], [
            MarketplaceBotCallbackVO.MENTORS,
            MarketplaceBotCallbackVO.COLLABORATIONS,
            MarketplaceBotCallbackVO.WORKSPACE,
        ])

    def test_unpublished_offer_not_exposed(self):
        self.repo.get_public_offer.return_value = None
        screen = self.logic.offer("fa", 15)
        self.repo.get_public_offer.assert_called_once_with(15)
        self.assertNotIn("mp:book:", str(screen.keyboard))

    def test_guest_cannot_book(self):
        screen = self.logic.book("en", 10, user=None)
        self.assertIn("/link", screen.text)
        self.usecases.book.assert_not_called()

    def test_booking_calls_usecase_when_authenticated(self):
        user = object()
        screen = self.logic.book("en", 42, user=user)
        self.usecases.book.assert_called_once_with(user, 42)
        self.assertIn("awaiting mentor", screen.text)

    def test_project_web_link_requires_https(self):
        project = MagicMock(pk=42, title="Safe & Sound", specialty="Python <backend>")
        self.repo.public_collaborations.return_value = [project]
        screen = self.logic.collaborations("en", "http://local/")
        self.assertTrue(all('url' not in button for row in screen.keyboard['inline_keyboard'] for button in row))
        self.assertEqual(screen.keyboard["inline_keyboard"][0][0]["callback_data"], "mp:project:42")
        self.assertIn("Safe &amp; Sound", screen.text)
        self.repo.get_public_collaboration.return_value = project
        screen = self.logic.collaboration_detail("en", 42, "https://acdevixa.ir/app?token=secret")
        self.assertEqual(screen.keyboard["inline_keyboard"][0][0]["url"], "https://acdevixa.ir/collaborations/42/")


class MarketplaceBotControllerTests(SimpleTestCase):
    def test_valid_callback_edits_existing_screen(self):
        send = MagicMock()
        logic = MagicMock()
        logic.mentors.return_value.text = "Hello"
        logic.mentors.return_value.keyboard = {"inline_keyboard": []}
        controller = MarketplaceBotController(
            send_chain_message=send, language_resolver=lambda p: "fa",
            linked_user_resolver=lambda p: None, app_url_resolver=lambda: "", logic=logic,
        )
        profile = object()
        self.assertTrue(controller.handle_callback(profile, MarketplaceBotCallbackVO.MENTORS, message_id=14))
        send.assert_called_once_with(profile, "Hello", reply_markup={"inline_keyboard": []}, message_id=14)
        self.assertFalse(controller.handle_callback(profile, "mp:unknown", message_id=14))
        send.assert_called_once()
