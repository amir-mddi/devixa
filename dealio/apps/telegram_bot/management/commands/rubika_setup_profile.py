from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.rubika_services import RubikaBotClient
from dealio.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO, TelegramBotProfileVO


class Command(BaseCommand):
    help = "Set Rubika bot command menu."

    def handle(self, *args, **options):
        client = RubikaBotClient()
        if not client.is_configured:
            raise CommandError("RUBIKA_BOT_TOKEN and RUBIKA_BOT_BASE_URL are required.")

        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.FA])
        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.EN])

        self.stdout.write(self.style.SUCCESS("Rubika bot commands configured successfully."))
