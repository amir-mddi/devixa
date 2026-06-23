from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dealio.apps.telegram_bot"
    verbose_name = "Telegram Bot"
