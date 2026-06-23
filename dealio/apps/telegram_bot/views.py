import hmac
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from dealio.apps.telegram_bot.models import TelegramUpdateLog
from dealio.apps.telegram_bot.services import TelegramBotClient, TelegramBotService

logger = logging.getLogger("dealio")


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        expected_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "")
        if expected_secret:
            provided_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not hmac.compare_digest(provided_secret, expected_secret):
                return JsonResponse({"ok": False, "detail": "Forbidden"}, status=403)

        update = request.data if isinstance(request.data, dict) else {}
        update_id = update.get("update_id")
        update_log = None

        if update_id is not None:
            update_log, created = TelegramUpdateLog.objects.get_or_create(
                update_id=update_id,
                defaults={"payload": update},
            )
            if not created and update_log.processed:
                return JsonResponse({"ok": True, "detail": "Duplicate update ignored"})

        client = TelegramBotClient()
        if not client.is_configured:
            return JsonResponse({"ok": False, "detail": "Telegram bot token is not configured"}, status=503)

        try:
            TelegramBotService(client=client).handle_update(update)
        except Exception as exc:
            logger.exception("Failed to process Telegram update")
            if update_log:
                update_log.error_text = str(exc)
                update_log.save(update_fields=["error_text"])
            # Return 200 so Telegram does not keep retrying a broken update forever.
            return JsonResponse({"ok": False, "detail": "Update received but processing failed"})

        if update_log:
            update_log.processed = True
            update_log.save(update_fields=["processed"])

        return JsonResponse({"ok": True})

    def get(self, request):
        return JsonResponse({"ok": True, "detail": "Telegram webhook endpoint is ready"})
