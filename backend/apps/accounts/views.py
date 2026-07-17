from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from backend.apps.accounts.dtos.password_recovery_dto import (
    ResetPasswordBySmsDTO,
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
    SendSmsPasswordRecoveryCodeDTO,
)
from backend.apps.accounts.dtos.phone_verification_dto import (
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberDTO,
)
from backend.apps.accounts.enums.oauth_enums import OAuthProviderEnum
from backend.apps.accounts.repositories.account_logic import AccountLogicRepository
from backend.apps.accounts.repositories.oauth_service import OAuthProviderError, SocialOAuthService
from backend.apps.accounts.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSendCodeSerializer,
    ForgotPasswordSmsSendCodeSerializer,
    ForgotPasswordSmsVerifyCodeSerializer,
    ForgotPasswordVerifyCodeSerializer,
    PhoneVerificationCodeSerializer,
    SocialOAuthLoginSerializer,
    UserSerializer,
    VerifyCodeSerializer,
)
from backend.apps.accounts.vo.oauth_vo import OAuthLogMessageVO, OAuthResponseKeyVO
from backend.apps.accounts.vo.password_recovery_vo import (
    AccountPasswordRecoveryApiMessageVO,
    AccountPasswordRecoveryErrorCodeVO,
    AccountPasswordRecoveryResponseKeyVO,
)
from backend.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationApiMessageVO,
    AccountPhoneVerificationErrorCodeVO,
)
from backend.apps.common.helpers.decorators.rate_limit import rate_limit
from backend.apps.common.response_utils import ResponseUtil
from backend.apps.common.utils.async_drf import validate_serializer
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.constants.common_vo import ResponseVO
from backend.apps.shared.views import BaseAPIView, BaseViewSet

User = get_user_model()
account_logic = AccountLogicRepository()
logger = CommonUtils.get_project_logger(__name__)


class ChangePasswordView(BaseViewSet):
    model_clz = User
    http_method_names = ["post"]
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    tag_name = "Account"

    async def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        await validate_serializer(serializer)
        await account_logic.async_change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )
        return ResponseUtil(
            custom_fields={"success": True, "message": "successfully changed"},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=2, period=60, anonymous_limit=0), name="post")
class UsersApiView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    model_class = User

    async def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        await validate_serializer(serializer)
        return ResponseUtil(data={"ok": True}, status_code=ResponseVO.http_200)


class UserViewSet(BaseViewSet):
    model_clz = User
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]
    tag_name = "Users"
    serializer_class = UserSerializer

    async def list(self, request):
        if not request.user.is_staff:
            return ResponseUtil(
                data={"detail": "Administrator access is required."},
                status_code=ResponseVO.http_403,
            )
        return await super().list(request)

    async def retrieve(self, request, pk=None):
        if not request.user.is_staff and str(request.user.pk) != str(pk):
            return ResponseUtil(
                data={"detail": "User was not found."},
                status_code=ResponseVO.http_404,
            )
        return await super().retrieve(request, pk=pk)


@method_decorator(rate_limit(authenticated_limit=20, period=60, anonymous_limit=0), name="post")
class SendEmailVerificationCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"

    async def post(self, request):
        user = request.user
        if user.email_verified:
            return ResponseUtil(
                data={"detail": "Email is already verified."},
                status_code=ResponseVO.http_400,
            )

        code_issued = await account_logic.async_send_verification_email_code(user)
        detail = (
            "Verification code sent successfully."
            if code_issued
            else "The previous verification code is still active."
        )
        return ResponseUtil(data={"detail": detail}, status_code=ResponseVO.http_200)


@method_decorator(rate_limit(authenticated_limit=20, period=60, anonymous_limit=0), name="post")
class VerifyEmailCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"
    serializer_class = VerifyCodeSerializer

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        is_valid = await account_logic.async_check_email_validation_code(
            user=request.user,
            code=serializer.validated_data["code"],
        )
        if not is_valid:
            return ResponseUtil(
                data={"detail": "Invalid or expired verification code."},
                status_code=ResponseVO.http_400,
            )
        return ResponseUtil(
            data={"detail": "Email verified successfully."},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=5, period=300, anonymous_limit=0), name="post")
class SendPhoneVerificationCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"

    async def post(self, request):
        result = await account_logic.async_send_phone_verification_code(
            dto=SendPhoneVerificationCodeDTO(user_id=str(request.user.id)),
        )
        if not result.is_success:
            return ResponseUtil(
                data={"detail": _phone_verification_error_message(result.error_code)},
                status_code=ResponseVO.http_400,
            )
        message = (
            AccountPhoneVerificationApiMessageVO.CODE_SENT.value
            if result.code_issued
            else AccountPhoneVerificationApiMessageVO.CODE_STILL_ACTIVE.value
        )
        return ResponseUtil(data={"detail": message}, status_code=ResponseVO.http_200)


@method_decorator(rate_limit(authenticated_limit=10, period=300, anonymous_limit=0), name="post")
class VerifyPhoneCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"
    serializer_class = PhoneVerificationCodeSerializer

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        result = await account_logic.async_verify_phone_number(
            dto=VerifyPhoneNumberDTO(
                user_id=str(request.user.id),
                code=serializer.validated_data["code"],
            ),
        )
        if not result.is_success:
            return ResponseUtil(
                data={"detail": _phone_verification_error_message(result.error_code)},
                status_code=ResponseVO.http_400,
            )
        return ResponseUtil(
            data={"detail": AccountPhoneVerificationApiMessageVO.VERIFIED.value},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=2, period=300), name="post")
class SendForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSendCodeSerializer
    tag_name = "Manage-Account"

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        await account_logic.async_send_forget_password_code_by_email(
            dto=SendPasswordRecoveryCodeDTO(email=serializer.validated_data["email"]),
        )
        return ResponseUtil(
            data={
                AccountPasswordRecoveryResponseKeyVO.DETAIL.value:
                    AccountPasswordRecoveryApiMessageVO.CODE_SENT.value,
            },
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="post")
class VerifyForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordVerifyCodeSerializer
    tag_name = "Manage-Account"

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        result = await account_logic.async_reset_forget_password_by_email(
            dto=ResetPasswordDTO(
                email=serializer.validated_data["email"],
                code=serializer.validated_data["code"],
                new_password=serializer.validated_data["new_password"],
            ),
        )
        return _password_reset_response(result)


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=2, period=300), name="post")
class SendForgotPasswordSmsCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSmsSendCodeSerializer
    tag_name = "Manage-Account"

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        await account_logic.async_send_forget_password_code_by_sms(
            dto=SendSmsPasswordRecoveryCodeDTO(
                phone_number=serializer.validated_data["phone_number"],
            ),
        )
        return ResponseUtil(
            data={
                AccountPasswordRecoveryResponseKeyVO.DETAIL.value:
                    AccountPasswordRecoveryApiMessageVO.SMS_CODE_SENT.value,
            },
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="post")
class VerifyForgotPasswordSmsCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSmsVerifyCodeSerializer
    tag_name = "Manage-Account"

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        result = await account_logic.async_reset_forget_password_by_sms(
            dto=ResetPasswordBySmsDTO(
                phone_number=serializer.validated_data["phone_number"],
                code=serializer.validated_data["code"],
                new_password=serializer.validated_data["new_password"],
            ),
        )
        return _password_reset_response(result)


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="post")
class BaseSocialOAuthLoginAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = SocialOAuthLoginSerializer
    tag_name = "Account"
    provider = None

    async def post(self, request):
        serializer = self.serializer_class(data=request.data)
        await validate_serializer(serializer)
        service = SocialOAuthService()
        try:
            token_data = await service.login(
                provider=self.provider,
                code=serializer.validated_data["code"],
                redirect_uri=serializer.validated_data["redirect_uri"],
            )
        except OAuthProviderError as exc:
            logger.warning(OAuthLogMessageVO.LOGIN_FAILED.value.format(error=exc.log_message))
            response_status = (
                ResponseVO.http_500
                if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
                else ResponseVO.http_400
            )
            return ResponseUtil(
                data={OAuthResponseKeyVO.DETAIL.value: exc.public_message},
                status_code=response_status,
            )
        return ResponseUtil(custom_fields=token_data, status_code=ResponseVO.http_200)


class GoogleOAuthLoginAPIView(BaseSocialOAuthLoginAPIView):
    provider = OAuthProviderEnum.GOOGLE.value


class GitHubOAuthLoginAPIView(BaseSocialOAuthLoginAPIView):
    provider = OAuthProviderEnum.GITHUB.value


def _password_reset_response(result):
    if not result.is_success:
        detail = (
            AccountPasswordRecoveryApiMessageVO.INVALID_PASSWORD.value
            if result.error_code == AccountPasswordRecoveryErrorCodeVO.INVALID_PASSWORD
            else AccountPasswordRecoveryApiMessageVO.INVALID_OR_EXPIRED_CODE.value
        )
        return ResponseUtil(
            data={AccountPasswordRecoveryResponseKeyVO.DETAIL.value: detail},
            status_code=ResponseVO.http_400,
        )
    return ResponseUtil(
        data={
            AccountPasswordRecoveryResponseKeyVO.DETAIL.value:
                AccountPasswordRecoveryApiMessageVO.PASSWORD_RESET_SUCCESS.value,
        },
        status_code=ResponseVO.http_200,
    )


def _phone_verification_error_message(error_code):
    messages = {
        AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND:
            AccountPhoneVerificationApiMessageVO.USER_NOT_FOUND.value,
        AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT:
            AccountPhoneVerificationApiMessageVO.INACTIVE_ACCOUNT.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED:
            AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_REQUIRED.value,
        AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED:
            AccountPhoneVerificationApiMessageVO.ALREADY_VERIFIED.value,
        AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE:
            AccountPhoneVerificationApiMessageVO.INVALID_OR_EXPIRED_CODE.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE:
            AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_ALREADY_IN_USE.value,
    }
    return messages.get(
        error_code,
        AccountPhoneVerificationApiMessageVO.INVALID_OR_EXPIRED_CODE.value,
    )
