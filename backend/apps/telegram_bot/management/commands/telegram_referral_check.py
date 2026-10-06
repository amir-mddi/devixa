from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient


class Command(BaseCommand):
    help = "Validate Telegram channel referral bot permissions and channel configuration."

    def handle(self, *args, **options):
        channel = str(getattr(settings, "TELEGRAM_REFERRAL_CHANNEL_USERNAME", "") or "").strip()
        if not channel:
            raise CommandError("TELEGRAM_REFERRAL_CHANNEL_USERNAME is not configured.")

        client = TelegramBotClient()
        if not client.is_configured:
            raise CommandError("TELEGRAM_BOT_TOKEN is not configured.")

        me = (client.get_me().get("result") or {})
        bot_id = me.get("id")
        if not bot_id:
            raise CommandError("Telegram bot identity could not be resolved.")

        chat = (client.get_chat(chat_id=channel).get("result") or {})
        member = (client.get_chat_member(chat_id=channel, user_id=bot_id).get("result") or {})
        status = str(member.get("status") or "")
        can_invite = bool(member.get("can_invite_users"))

        self.stdout.write(f"Channel: {chat.get('title') or channel}")
        self.stdout.write(f"Chat ID: {chat.get('id') or '-'}")
        self.stdout.write(f"Bot: @{me.get('username') or '-'}")
        self.stdout.write(f"Status: {status or '-'}")
        self.stdout.write(f"can_invite_users: {can_invite}")

        if status not in {"administrator", "creator"} or not can_invite:
            raise CommandError(
                "The bot must be a channel administrator with can_invite_users permission."
            )

        self.stdout.write(self.style.SUCCESS("Telegram referral channel permissions are ready."))
