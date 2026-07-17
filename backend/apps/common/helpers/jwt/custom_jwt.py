from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from backend.apps.accounts.serializers import CustomTokenObtainPairSerializer
from backend.apps.common.utils.async_api import AsyncAPIView
from backend.apps.common.utils.async_drf import call_sync, validate_serializer


@extend_schema(tags=["Account"])
class CustomTokenObtainPairView(AsyncAPIView):
    """Issue JWT credentials without blocking the ASGI event loop."""

    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get_serializer_context(self) -> dict:
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return self.serializer_class(*args, **kwargs)

    @extend_schema(
        request=CustomTokenObtainPairSerializer,
        responses={status.HTTP_200_OK: dict},
    )
    async def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        await validate_serializer(serializer)
        token_data = await call_sync(lambda: dict(serializer.validated_data))

        access_token = token_data["access"]
        refresh_token = token_data["refresh"]
        access = AccessToken(access_token)

        return Response(
            {
                "token": access_token,
                "refreshToken": refresh_token,
                "expirationTime": int(access["exp"]) * 1000,
            },
            status=status.HTTP_200_OK,
        )
