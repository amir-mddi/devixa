from __future__ import annotations

import logging
import os

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from dealio.apps.telegram_bot.bale_services import BaleBotClient, BaleBotService
from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.rubika_services import RubikaBotClient, RubikaBotService, RubikaUpdateNormalizer
from dealio.apps.telegram_bot.services import TelegramBotService
from dealio.apps.telegram_bot.application_services.webhook_service import BotWebhookService

logger = logging.getLogger("dealio")


class BaseBotWebhookAPIView(APIView):
    """Thin webhook controller.

    The view validates transport concerns, then delegates update processing to
    application services/logic/repositories/adapters.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    provider: str = ""
    secret_env_name: str = ""
    secret_headers: tuple[str, ...] = ()
    not_configured_message: str = "Bot is not configured"
    ready_message: str = "Webhook endpoint is ready"

    def get_client(self):
        raise NotImplementedError

    def make_service(self, client):
        raise NotImplementedError

    def get_update_id(self, update: dict):
        return update.get("update_id")

    def get_secret(self, request) -> str:
        for header_name in self.secret_headers:
            value = request.headers.get(header_name, "")
            if value:
                return value
        return ""

    def post(self, request):
        expected_secret = os.environ.get(self.secret_env_name) or ""
        webhook_service = BotWebhookService(
            provider=self.provider,
            service_factory=lambda: self.make_service(self.get_client()),
            update_id_getter=self.get_update_id,
        )

        if not webhook_service.validate_secret(
            expected_secret=expected_secret,
            provided_secret=self.get_secret(request),
        ):
            return JsonResponse({"ok": False, "detail": "Forbidden"}, status=403)

        update = request.data if isinstance(request.data, dict) else {}
        client = self.get_client()
        if not client.is_configured:
            return JsonResponse({"ok": False, "detail": self.not_configured_message}, status=503)

        try:
            processed = BotWebhookService(
                provider=self.provider,
                service_factory=lambda: self.make_service(client),
                update_id_getter=self.get_update_id,
            ).process(update)
        except Exception:
            logger.exception("Failed to process %s update", self.provider)
            return JsonResponse({"ok": False, "detail": "Update received but processing failed"})

        return JsonResponse({"ok": True, "processed": processed})

    def get(self, request):
        return JsonResponse({"ok": True, "detail": self.ready_message})


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookAPIView(BaseBotWebhookAPIView):
    provider = TelegramBotService.MESSENGER_PROVIDER
    secret_env_name = "TELEGRAM_WEBHOOK_SECRET"
    secret_headers = ("X-Telegram-Bot-Api-Secret-Token",)
    not_configured_message = "Telegram bot token is not configured"
    ready_message = "Telegram webhook endpoint is ready"

    def get_client(self):
        return TelegramBotClient()

    def make_service(self, client):
        return TelegramBotService(client=client)


@method_decorator(csrf_exempt, name="dispatch")
class BaleWebhookAPIView(BaseBotWebhookAPIView):
    provider = BaleBotService.MESSENGER_PROVIDER
    secret_env_name = "BALE_WEBHOOK_SECRET"
    secret_headers = ("X-Bale-Bot-Api-Secret-Token", "X-Telegram-Bot-Api-Secret-Token")
    not_configured_message = "Bale bot token/base URL is not configured"
    ready_message = "Bale webhook endpoint is ready"

    def get_client(self):
        return BaleBotClient()

    def make_service(self, client):
        return BaleBotService(client=client)


@method_decorator(csrf_exempt, name="dispatch")
class RubikaWebhookAPIView(BaseBotWebhookAPIView):
    provider = RubikaBotService.MESSENGER_PROVIDER
    secret_env_name = "RUBIKA_WEBHOOK_SECRET"
    secret_headers = ("X-Rubika-Bot-Api-Secret-Token", "X-Bot-Api-Secret-Token")
    not_configured_message = "Rubika bot token/base URL is not configured"
    ready_message = "Rubika webhook endpoint is ready"

    def get_client(self):
        return RubikaBotClient()

    def make_service(self, client):
        return RubikaBotService(client=client)

    def get_update_id(self, update: dict):
        return RubikaUpdateNormalizer.update_log_id(update)
