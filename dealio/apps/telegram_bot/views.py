from __future__ import annotations

from dealio.apps.common.utils.common_utils import CommonUtils
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from dealio.apps.telegram_bot.bale_services import BaleBotClient, BaleBotService
from dealio.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from dealio.apps.telegram_bot.rubika_services import RubikaBotClient, RubikaBotService, RubikaUpdateNormalizer
from dealio.apps.telegram_bot.services import TelegramBotService
from dealio.apps.telegram_bot.factories.service_factory import TelegramBotServiceFactory
from dealio.apps.telegram_bot.application_services.webhook_service import BotWebhookService
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider, BotSettingLogicRepository
from dealio.apps.telegram_bot.serializers import BotSettingsUpdateSerializer

logger = CommonUtils.get_project_logger(__name__)


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

    @staticmethod
    def _json_response(payload: dict, *, status_code: int = 200) -> JsonResponse:
        response = JsonResponse(payload, status=status_code)
        response["Cache-Control"] = "no-store"
        response["Pragma"] = "no-cache"
        return response

    def post(self, request):
        expected_secret = BotRuntimeConfigProvider.get_env(self.secret_env_name)
        if not BotWebhookService.validate_secret(
            expected_secret=expected_secret,
            provided_secret=self.get_secret(request),
        ):
            return self._json_response(
                {"ok": False, "detail": "Forbidden"},
                status_code=403,
            )

        update = request.data if isinstance(request.data, dict) else None
        if not update or not self._is_safe_update(update):
            return self._json_response(
                {"ok": False, "detail": "Invalid update"},
                status_code=400,
            )
        update_id = self.get_update_id(update)
        if update_id is None:
            return self._json_response(
                {"ok": False, "detail": "Invalid update"},
                status_code=400,
            )
        try:
            normalized_update_id = int(update_id)
        except (TypeError, ValueError):
            return self._json_response(
                {"ok": False, "detail": "Invalid update"},
                status_code=400,
            )
        if normalized_update_id < 0 or normalized_update_id > 9_223_372_036_854_775_807:
            return self._json_response(
                {"ok": False, "detail": "Invalid update"},
                status_code=400,
            )

        client = self.get_client()
        if not client.is_configured:
            return self._json_response(
                {"ok": False, "detail": self.not_configured_message},
                status_code=503,
            )

        webhook_service = BotWebhookService(
            provider=self.provider,
            service_factory=lambda: self.make_service(client),
            update_id_getter=self.get_update_id,
        )
        try:
            processed = webhook_service.process(update)
        except Exception:
            logger.exception("Failed to process %s update", self.provider)
            # Non-2xx lets the provider retry. Processing is idempotent by update id.
            return self._json_response(
                {"ok": False, "detail": "Update processing failed"},
                status_code=503,
            )

        return self._json_response({"ok": True, "processed": processed})

    @staticmethod
    def _is_safe_update(update: dict) -> bool:
        max_nodes = 2_000
        max_string_length = 100_000
        nodes = 0
        stack = [update]
        while stack:
            current = stack.pop()
            nodes += 1
            if nodes > max_nodes:
                return False
            if isinstance(current, dict):
                if len(current) > 200:
                    return False
                for key, value in current.items():
                    if len(str(key)) > 200:
                        return False
                    stack.append(value)
            elif isinstance(current, list):
                if len(current) > 500:
                    return False
                stack.extend(current)
            elif isinstance(current, str) and len(current) > max_string_length:
                return False
        return True

    def get(self, request):
        expected_secret = BotRuntimeConfigProvider.get_env(self.secret_env_name)
        if not BotWebhookService.validate_secret(
            expected_secret=expected_secret,
            provided_secret=self.get_secret(request),
        ):
            return self._json_response(
                {"ok": False, "detail": "Not found"},
                status_code=404,
            )
        return self._json_response({"ok": True, "detail": self.ready_message})


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
        return TelegramBotServiceFactory.create(client=client)


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



class BotSettingsAPIView(APIView):
    """Admin-only endpoint used by the panel bot settings button."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({"items": BotSettingLogicRepository().list_all()}, status=status.HTTP_200_OK)


class BotProviderSettingsAPIView(APIView):
    """Read/update runtime settings for one provider group.

    Example provider values: telegram, bale, rubika, channel_sync, channel_member_sync.
    """

    permission_classes = [IsAdminUser]

    def get(self, request, provider: str):
        try:
            data = BotSettingLogicRepository().provider_settings(provider)
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request, provider: str):
        serializer = BotSettingsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = BotSettingLogicRepository().update_provider_settings(
                provider=provider,
                raw_settings=serializer.validated_data["settings"],
                user=request.user,
                write_to_database=True,
                write_to_env=False,
            )
        except ValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)
