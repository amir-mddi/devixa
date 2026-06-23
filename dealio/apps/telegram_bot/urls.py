from django.urls import path

from dealio.apps.telegram_bot.views import TelegramWebhookAPIView

urlpatterns = [
    path("webhook/", TelegramWebhookAPIView.as_view(), name="telegram-webhook"),
]
