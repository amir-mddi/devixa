from django.core.management.base import BaseCommand

from dealio.apps.telegram_bot.services import TelegramBotClient
from dealio.apps.telegram_bot.vo.commerce_bot_vo import TelegramBotLanguageVO, TelegramBotProfileVO


class Command(BaseCommand):
    help = "Set Telegram bot description, short description, and command menu for better UX."

    def handle(self, *args, **options):
        client = TelegramBotClient()

        # Default is Persian because your current UX/screens are Persian-first.
        client.set_my_description(TelegramBotProfileVO.DESCRIPTION[TelegramBotLanguageVO.FA])
        client.set_my_short_description(TelegramBotProfileVO.SHORT_DESCRIPTION[TelegramBotLanguageVO.FA])
        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.FA])

        # English localization for users whose Telegram language is English.
        client.set_my_description(TelegramBotProfileVO.DESCRIPTION[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)
        client.set_my_short_description(TelegramBotProfileVO.SHORT_DESCRIPTION[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)
        client.set_my_commands(TelegramBotProfileVO.COMMANDS[TelegramBotLanguageVO.EN], language_code=TelegramBotLanguageVO.EN)

        self.stdout.write(self.style.SUCCESS(TelegramBotProfileVO.SETUP_SUCCESS_MESSAGE))
