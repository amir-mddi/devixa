import time
from audioop import alaw2lin

from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction

from dealio.apps.accounts.serializers import ChangePasswordSerializer, UserSerializer, VerifyCodeSerializer, \
    ForgotPasswordSendCodeSerializer, ForgotPasswordVerifyCodeSerializer
from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.shared.views import BaseViewSet, BaseAPIView
from .models import Role
from ..common.helpers.decorators.rate_limit import rate_limit
from ..core_models.constants.common_vo import ResponseVO
from ..shared.repositories.logic import SharedApplicationLogic
from ..shared.serializers import ListResponseSerializer, BaseResponseSerializer

User = get_user_model()
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository

shared_logic = SharedApplicationLogic()
account_logic = AccountLogicRepository()
import logging

logger = logging.getLogger("dealio")


class ChangePasswordView(BaseViewSet):
    model_clz = User
    http_method_names = ['post']
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    tag_name = "Account"

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = request.user
            if user.check_password(request.data.get('currentPassword')):
                password = request.data.get('newPassword')
                user.set_password(password)
                user.save()
                account_logic.send_change_password_in_separate_thread(user.phone_number, password, user.username)
                return ResponseUtil(custom_fields={'success': True, 'message': 'successfully changed'},
                                    status_code=ResponseVO.http_200)
            else:
                return ResponseUtil(custom_fields={"success": False, "message": "incorrect password provide"},
                                    status_code=ResponseVO.http_400)
        else:
            return ResponseUtil(custom_fields={"success": False, "message": str(serializer.errors)},
                                status_code=ResponseVO.http_400)


@method_decorator(rate_limit(authenticated_limit=2, period=60, anonymous_limit=0), name="dispatch")
class UsersApiView(BaseAPIView):
    serializer_class = UserSerializer
    model_class = User

    def post(self, request):
        data = request.data

        serializer = self.serializer_class(
            data=data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        # account_logic.send_verification_forget_password_code(user=instance)
        # response_data = self.serializer_class(instance).data

        return ResponseUtil(
            data={"ok": True},
            status_code=ResponseVO.http_200,
        )


class UserViewSet(BaseViewSet):
    model_clz = User
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    tag_name = "Users"
    serializer_class = UserSerializer


@method_decorator(rate_limit(authenticated_limit=20, period=60, anonymous_limit=0), name="dispatch")
class SendEmailVerificationCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"

    def post(self, request):
        user = request.user

        if user.email_verified:
            return ResponseUtil(
                data={"detail": "Email is already verified."},
                status_code=ResponseVO.http_400,
            )

        AccountLogicRepository().send_verification_email_code(user)

        return ResponseUtil(
            {"detail": "Verification code sent successfully."},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=20, period=60, anonymous_limit=0), name="dispatch")
class VerifyEmailCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"
    serializer_class = VerifyCodeSerializer

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_valid = AccountLogicRepository().check_email_validation_code(
            user=request.user,
            code=serializer.validated_data["code"],
        )

        if not is_valid:
            return ResponseUtil(
                data={"detail": "Invalid or expired verification code."},
                status_code=ResponseVO.http_400,
            )

        return ResponseUtil(
            {"detail": "Email verified successfully."},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=2, period=300), name="dispatch")
class SendForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSendCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = ForgotPasswordSendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        if user:
            AccountLogicRepository().send_verification_forget_password_code(user)

        return ResponseUtil(
            data={"detail": "If this email exists, a password recovery code has been sent."},
            status_code=ResponseVO.http_400,
        )


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="dispatch")
class VerifyForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordVerifyCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = ForgotPasswordVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["newPassword"]
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return ResponseUtil(
                data={"detail": "Invalid or expired verification code."},
                status_code=ResponseVO.http_400,
            )

        is_valid = AccountLogicRepository().check_forget_password_code(
            user=user,
            code=code,
        )

        if not is_valid:
            return ResponseUtil(
                data={"detail": "Invalid or expired verification code."},
                status_code=ResponseVO.http_400,
            )

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password"])

        return ResponseUtil(
            data={"detail": "Password has been reset successfully."},
            status_code=ResponseVO.http_200,
        )
