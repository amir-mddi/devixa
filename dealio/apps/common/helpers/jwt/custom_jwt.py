from dealio.apps.common.utils.common_utils import CommonUtils
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.core.cache import cache
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from dealio.apps.accounts.serializers import CustomTokenObtainPairSerializer
from dealio.apps.common.response_utils import ResponseUtil
from dealio.project.settings import ACCESS_TOKEN_LIFE_TIME_HOUR, SIMPLE_JWT

User = get_user_model()
import jwt

logger = CommonUtils.get_project_logger(__name__)


@extend_schema(tags=["Account"])
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code != 200:
            return JsonResponse(
                {"error": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        username = request.data.get("username", "")

        try:
            user = User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "User not found or inactive"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = response.data.get("access")

        if not token:
            return JsonResponse(
                {"error": "Access token was not generated"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        access = AccessToken(token)

        cache.set(
            f"mock_service_user_access_token_with_id:{user.id}",
            str(token),
            timeout=int(SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        )

        login(request, user)

        return ResponseUtil(
            custom_fields={
                "token": str(token),
                "expirationTime": int(access["exp"]) * 1000,
            }
        )
