from __future__ import annotations

from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware


class BlockedTokenMiddleware(AsyncCompatibleMiddleware):
    """Validate bearer-token shape without forcing ASGI requests into sync mode."""

    @staticmethod
    def _invalid_token_response(request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            UntypedToken(token)
        except TokenError:
            return JsonResponse({"detail": "Invalid or expired token."}, status=401)
        return None

    def process_sync(self, request):
        return self._invalid_token_response(request) or self.get_response(request)

    async def process_async(self, request):
        response = self._invalid_token_response(request)
        if response is not None:
            return response
        return await self.get_response(request)
