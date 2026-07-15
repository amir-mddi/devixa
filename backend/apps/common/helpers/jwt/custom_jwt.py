from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from backend.apps.accounts.serializers import CustomTokenObtainPairSerializer


@extend_schema(tags=["Account"])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        access_token = response.data.get("access")
        refresh_token = response.data.get("refresh")
        access = AccessToken(access_token)
        return Response(
            {
                "token": access_token,
                "refreshToken": refresh_token,
                "expirationTime": int(access["exp"]) * 1000,
            },
            status=status.HTTP_200_OK,
        )
