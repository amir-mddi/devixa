from __future__ import annotations
import json
from typing import Any
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from backend.apps.common.utils.async_api import AsyncAPIView as APIView
from backend.apps.common.utils.async_drf import validate_serializer
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.telegram_bot.application_services.async_bot_service import AsyncBotService
from backend.apps.telegram_bot.application_services.webhook_service import BotWebhookService
from backend.apps.telegram_bot.bale_services import BaleBotClient, BaleBotService
from backend.apps.telegram_bot.factories.service_factory import TelegramBotServiceFactory
from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import TelegramBotClient
from backend.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider, BotSettingLogicRepository
from backend.apps.telegram_bot.rubika_services import RubikaBotClient, RubikaBotService, RubikaUpdateNormalizer
from backend.apps.telegram_bot.serializers import BotSettingsUpdateSerializer
from backend.apps.telegram_bot.services import TelegramBotService
from backend.apps.telegram_bot.vo.webhook_vo import (
    BotWebhookEnvironmentVO,
    BotWebhookHeaderVO,
    BotWebhookMessageVO,
    BotWebhookResponseKeyVO,
)
logger = CommonUtils.get_project_logger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class BaseBotWebhookAPIView(View):
    """Native async webhook controller.

    Transport validation stays in the controller. Update processing is delegated
    to async application logic and repositories, preserving the clean layering:
    request -> controller -> logic -> repository -> adapter.
    """
    http_method_names = ['get', 'post', 'options']
    provider: str = ''
    secret_env_name: str = ''
    secret_headers: tuple[str, ...] = ()
    not_configured_message: str = BotWebhookMessageVO.BOT_NOT_CONFIGURED.value
    ready_message: str = BotWebhookMessageVO.WEBHOOK_READY.value

    def get_client(self):
        raise NotImplementedError

    def make_service(self, client):
        raise NotImplementedError

    def get_update_id(self, update: dict[str, Any]):
        return update.get('update_id')

    def get_secret(self, request) -> str:
        for header_name in self.secret_headers:
            value = request.headers.get(header_name, '')
            if value:
                return value
        return ''

    @staticmethod
    def _json_response(payload: dict[str, Any], *, status_code: int=200) -> JsonResponse:
        response = JsonResponse(payload, status=status_code)
        response['Cache-Control'] = 'no-store'
        response['Pragma'] = 'no-cache'
        return response

    async def _expected_secret(self) -> str:
        return await sync_to_async(BotRuntimeConfigProvider.get_env, thread_sensitive=True)(self.secret_env_name)

    async def post(self, request, *args, **kwargs):
        expected_secret = await self._expected_secret()
        if not BotWebhookService.validate_secret(expected_secret=expected_secret, provided_secret=self.get_secret(request)):
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.FORBIDDEN.value}, status_code=403)
        update = self._parse_json_body(request)
        if not update or not self._is_safe_update(update):
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.INVALID_UPDATE.value}, status_code=400)
        update_id = self.get_update_id(update)
        if update_id is None:
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.INVALID_UPDATE.value}, status_code=400)
        try:
            normalized_update_id = int(update_id)
        except (TypeError, ValueError):
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.INVALID_UPDATE.value}, status_code=400)
        if normalized_update_id < 0 or normalized_update_id > 9223372036854775807:
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.INVALID_UPDATE.value}, status_code=400)
        client = self.get_client()
        is_configured = await sync_to_async(lambda: client.is_configured, thread_sensitive=True)()
        if not is_configured:
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: self.not_configured_message}, status_code=503)
        webhook_service = BotWebhookService(provider=self.provider, service_factory=lambda: self.make_service(client), update_id_getter=self.get_update_id)
        try:
            processed = await webhook_service.process(update)
        except Exception:
            logger.exception('Failed to process %s update', self.provider)
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.UPDATE_PROCESSING_FAILED.value}, status_code=503)
        return self._json_response({BotWebhookResponseKeyVO.OK.value: True, BotWebhookResponseKeyVO.PROCESSED.value: processed})

    async def get(self, request, *args, **kwargs):
        expected_secret = await self._expected_secret()
        if not BotWebhookService.validate_secret(expected_secret=expected_secret, provided_secret=self.get_secret(request)):
            return self._json_response({BotWebhookResponseKeyVO.OK.value: False, BotWebhookResponseKeyVO.DETAIL.value: BotWebhookMessageVO.NOT_FOUND.value}, status_code=404)
        return self._json_response({BotWebhookResponseKeyVO.OK.value: True, BotWebhookResponseKeyVO.DETAIL.value: self.ready_message})

    @staticmethod
    def _parse_json_body(request) -> dict[str, Any] | None:
        try:
            payload = json.loads(request.body.decode(request.encoding or 'utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _is_safe_update(update: dict[str, Any]) -> bool:
        max_nodes = 2000
        max_string_length = 100000
        nodes = 0
        stack: list[Any] = [update]
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

class TelegramWebhookAPIView(BaseBotWebhookAPIView):
    provider = TelegramBotService.MESSENGER_PROVIDER
    secret_env_name = BotWebhookEnvironmentVO.TELEGRAM_SECRET.value
    secret_headers = (BotWebhookHeaderVO.TELEGRAM_SECRET.value,)
    not_configured_message = BotWebhookMessageVO.TELEGRAM_NOT_CONFIGURED.value
    ready_message = BotWebhookMessageVO.TELEGRAM_READY.value

    def get_client(self):
        return TelegramBotClient()

    def make_service(self, client):
        return TelegramBotServiceFactory.create_async(client=client)

class BaleWebhookAPIView(BaseBotWebhookAPIView):
    provider = BaleBotService.MESSENGER_PROVIDER
    secret_env_name = BotWebhookEnvironmentVO.BALE_SECRET.value
    secret_headers = (
        BotWebhookHeaderVO.BALE_SECRET.value,
        BotWebhookHeaderVO.TELEGRAM_SECRET.value,
    )
    not_configured_message = BotWebhookMessageVO.BALE_NOT_CONFIGURED.value
    ready_message = BotWebhookMessageVO.BALE_READY.value

    def get_client(self):
        return BaleBotClient()

    def make_service(self, client):
        return AsyncBotService(BaleBotService(client=client))

class RubikaWebhookAPIView(BaseBotWebhookAPIView):
    provider = RubikaBotService.MESSENGER_PROVIDER
    secret_env_name = BotWebhookEnvironmentVO.RUBIKA_SECRET.value
    secret_headers = (
        BotWebhookHeaderVO.RUBIKA_SECRET.value,
        BotWebhookHeaderVO.GENERIC_SECRET.value,
    )
    not_configured_message = BotWebhookMessageVO.RUBIKA_NOT_CONFIGURED.value
    ready_message = BotWebhookMessageVO.RUBIKA_READY.value

    def get_client(self):
        return RubikaBotClient()

    def make_service(self, client):
        return AsyncBotService(RubikaBotService(client=client))

    def get_update_id(self, update: dict[str, Any]):
        return RubikaUpdateNormalizer.update_log_id(update)

class BotSettingsAPIView(APIView):
    """Admin-only endpoint used by the panel bot settings button."""
    permission_classes = [IsAdminUser]

    async def get(self, request):
        items = await BotSettingLogicRepository().list_all_async()
        return Response({"items": items}, status=status.HTTP_200_OK)


class BotProviderSettingsAPIView(APIView):
    """Read or update runtime settings for one provider group."""
    permission_classes = [IsAdminUser]

    async def get(self, request, provider: str):
        try:
            data = await BotSettingLogicRepository().provider_settings_async(provider)
        except ValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(data, status=status.HTTP_200_OK)

    async def patch(self, request, provider: str):
        serializer = BotSettingsUpdateSerializer(data=request.data)
        await validate_serializer(serializer)
        try:
            data = await BotSettingLogicRepository().update_provider_settings_async(
                provider=provider,
                raw_settings=serializer.validated_data["settings"],
                user=request.user,
                write_to_database=True,
                write_to_env=False,
            )
        except ValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(data, status=status.HTTP_200_OK)
