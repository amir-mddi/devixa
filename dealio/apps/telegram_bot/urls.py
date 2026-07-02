from django.urls import path

from dealio.apps.telegram_bot.views import (
    BaleWebhookAPIView,
    BotProviderSettingsAPIView,
    BotSettingsAPIView,
    RubikaWebhookAPIView,
    TelegramWebhookAPIView,
)

urlpatterns = [
    path("webhook/", TelegramWebhookAPIView.as_view(), name="telegram-webhook"),
    path("bale/webhook/", BaleWebhookAPIView.as_view(), name="bale-webhook"),
    path("rubika/webhook/", RubikaWebhookAPIView.as_view(), name="rubika-webhook"),
    path("settings/", BotSettingsAPIView.as_view(), name="bot-settings"),
    path("settings/<str:provider>/", BotProviderSettingsAPIView.as_view(), name="bot-provider-settings"),
]
