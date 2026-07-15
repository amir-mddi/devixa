from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from backend.apps.telegram_bot.models import (
    BotRuntimeSetting,
    BotScheduledNotification,
    BotSupportMessage,
    BotSupportTicket,
    ChannelSyncMessage,
    TelegramUpdateLog,
)
from backend.tests.factories import BotSupportTicketFactory, TelegramProfileFactory


class TelegramBotModelTests(TestCase):
    def test_profile_is_unique_per_provider_and_chat(self):
        TelegramProfileFactory.create(messenger_provider="telegram", chat_id="100")

        with self.assertRaises(IntegrityError), transaction.atomic():
            TelegramProfileFactory.create(messenger_provider="telegram", chat_id="100")

    def test_same_chat_id_can_exist_for_different_providers(self):
        telegram = TelegramProfileFactory.create(messenger_provider="telegram", chat_id="100")
        bale = TelegramProfileFactory.create(messenger_provider="bale", chat_id="100")

        self.assertNotEqual(telegram.pk, bale.pk)

    def test_update_log_is_idempotent_per_provider_and_update(self):
        TelegramUpdateLog.objects.create(messenger_provider="telegram", update_id=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            TelegramUpdateLog.objects.create(messenger_provider="telegram", update_id=1)

    def test_runtime_setting_is_unique_per_provider_and_key(self):
        BotRuntimeSetting.objects.create(provider="telegram", key="bot_token", value="one")

        with self.assertRaises(IntegrityError), transaction.atomic():
            BotRuntimeSetting.objects.create(provider="telegram", key="bot_token", value="two")

    def test_channel_sync_mapping_is_unique_per_source_and_target(self):
        values = {
            "source_provider": "telegram",
            "source_chat_id": "source",
            "source_message_id": "1",
            "target_provider": "bale",
            "target_chat_id": "target",
        }
        ChannelSyncMessage.objects.create(**values)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ChannelSyncMessage.objects.create(**values)

    def test_support_message_uses_ticket_ordering_and_readable_string(self):
        ticket = BotSupportTicketFactory.create()
        first = BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_USER,
            message="First",
        )
        second = BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_ADMIN,
            message="Second",
        )

        self.assertQuerySetEqual(ticket.messages.all(), [first, second])
        self.assertIn(BotSupportMessage.SENDER_USER, str(first))

    def test_scheduled_notification_defaults_to_pending(self):
        notification = BotScheduledNotification.objects.create(
            provider="telegram",
            message="Hello",
            scheduled_at=timezone.now(),
        )

        self.assertEqual(notification.status, BotScheduledNotification.STATUS_PENDING)
