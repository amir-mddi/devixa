from django.core.management.base import BaseCommand

from dealio.apps.telegram_bot.services import TelegramBotClient


class Command(BaseCommand):
    help = "Set Telegram bot description, short description, and command menu for better UX."

    DESCRIPTION_FA = (
        "سلام! به ربات Devixa خوش آمدید. 👋\n\n"
        "با این ربات می‌توانید حساب کاربری خود را به تلگرام متصل کنید، "
        "ایمیل را تأیید کنید، رمز عبور را بازیابی کنید، اطلاعات حساب را ببینید "
        "و اگر مدیر باشید کاربر جدید بسازید.\n\n"
        "برای شروع، دکمه Start را بزنید."
    )
    DESCRIPTION_EN = (
        "Welcome to Devixa bot. 👋\n\n"
        "Use this bot to link your app account, verify email, recover password, "
        "view account details, and create users if you are an admin.\n\n"
        "Tap Start to begin."
    )
    SHORT_DESCRIPTION_FA = "اتصال حساب، تأیید ایمیل، بازیابی رمز عبور و مدیریت کاربران Devixa"
    SHORT_DESCRIPTION_EN = "Link your account, verify email, recover password, and manage Devixa users."

    COMMANDS_FA = [
        {"command": "start", "description": "شروع و نمایش منو"},
        {"command": "account", "description": "نمایش حساب من"},
        {"command": "verify_email", "description": "تأیید ایمیل"},
        {"command": "forgot_password", "description": "بازیابی رمز عبور"},
        {"command": "language", "description": "تغییر زبان"},
        {"command": "help", "description": "راهنما"},
    ]
    COMMANDS_EN = [
        {"command": "start", "description": "Start and show menu"},
        {"command": "account", "description": "Show my account"},
        {"command": "verify_email", "description": "Verify email"},
        {"command": "forgot_password", "description": "Recover password"},
        {"command": "language", "description": "Change language"},
        {"command": "help", "description": "Help"},
    ]

    def handle(self, *args, **options):
        client = TelegramBotClient()

        # Default is Persian because your current UX/screens are Persian-first.
        client.set_my_description(self.DESCRIPTION_FA)
        client.set_my_short_description(self.SHORT_DESCRIPTION_FA)
        client.set_my_commands(self.COMMANDS_FA)

        # English localization for users whose Telegram language is English.
        client.set_my_description(self.DESCRIPTION_EN, language_code="en")
        client.set_my_short_description(self.SHORT_DESCRIPTION_EN, language_code="en")
        client.set_my_commands(self.COMMANDS_EN, language_code="en")

        self.stdout.write(self.style.SUCCESS("Telegram bot profile UX was updated successfully."))
