from django.core.management.base import BaseCommand, CommandError

from dealio.apps.telegram_bot.bale_services import BaleBotClient
from dealio.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO, TelegramBotProfileVO


class Command(BaseCommand):
    help = "Set Bale bot description, short description, and command menu."

    def handle(self, *args, **options):
        client = BaleBotClient()
        if not client.is_configured:
            raise CommandError("BALE_BOT_TOKEN and BALE_BOT_BASE_URL are required.")

        client.set_my_description(TelegramBotProfileVO.DESCRIPTION[TelegramBotLanguageVO.FA])
        client.set_my_short_description(TelegramBotProfileVO.SHORT_DESCRIPTION[TelegramBotLanguageVO.FA])
        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.FA])

        client.set_my_description(TelegramBotProfileVO.DESCRIPTION[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)
        client.set_my_short_description(TelegramBotProfileVO.SHORT_DESCRIPTION[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)
        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)

        self.stdout.write(self.style.SUCCESS("Bale bot profile configured successfully."))
