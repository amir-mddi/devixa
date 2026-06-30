from django.urls import path

from dealio.apps.telegram_bot.views import BaleWebhookAPIView, RubikaWebhookAPIView, TelegramWebhookAPIView

urlpatterns = [
    path("webhook/", TelegramWebhookAPIView.as_view(), name="telegram-webhook"),
    path("bale/webhook/", BaleWebhookAPIView.as_view(), name="bale-webhook"),
    path("rubika/webhook/", RubikaWebhookAPIView.as_view(), name="rubika-webhook"),
]
