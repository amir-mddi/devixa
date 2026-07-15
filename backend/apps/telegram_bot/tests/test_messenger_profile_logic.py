from django.test import TestCase

from backend.apps.telegram_bot.dtos.profile_dtos import DisconnectMessengerProfileDTO
from backend.apps.telegram_bot.enums.profile_enums import (
    MessengerProfileDisconnectErrorEnum,
)
from backend.apps.telegram_bot.logic.profile_logic import MessengerProfileLogic
from backend.tests.factories import TelegramProfileFactory, UserFactory


class MessengerProfileLogicTests(TestCase):
    def setUp(self):
        self.logic = MessengerProfileLogic()
        self.user = UserFactory.create()

    def test_user_can_disconnect_owned_messenger_profile(self):
        profile = TelegramProfileFactory.create(
            user=self.user,
            is_verified=True,
            is_active=True,
        )

        result = self.logic.disconnect(
            DisconnectMessengerProfileDTO(
                profile_id=profile.id,
                user_id=self.user.id,
            )
        )

        profile.refresh_from_db()
        self.assertTrue(result.is_success)
        self.assertIsNone(profile.user_id)
        self.assertFalse(profile.is_verified)
        self.assertTrue(profile.is_active)

    def test_user_cannot_disconnect_another_users_profile(self):
        profile = TelegramProfileFactory.create(
            user=UserFactory.create(),
            is_verified=True,
        )

        result = self.logic.disconnect(
            DisconnectMessengerProfileDTO(
                profile_id=profile.id,
                user_id=self.user.id,
            )
        )

        profile.refresh_from_db()
        self.assertFalse(result.is_success)
        self.assertEqual(
            result.error_code,
            MessengerProfileDisconnectErrorEnum.PROFILE_NOT_FOUND,
        )
        self.assertIsNotNone(profile.user_id)
