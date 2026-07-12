from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from dealio.apps.accounts.dtos.password_recovery_dto import (
    ResetPasswordBySmsDTO,
    ResetPasswordDTO,
    SendPasswordRecoveryCodeDTO,
    SendSmsPasswordRecoveryCodeDTO,
)
from dealio.apps.accounts.dtos.phone_verification_dto import (
    SendPhoneVerificationCodeDTO,
    VerifyPhoneNumberDTO,
)
from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.accounts.repositories.oauth_service import OAuthProviderError, SocialOAuthService
from dealio.apps.accounts.serializers import (
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
from dealio.apps.accounts.vo.password_recovery_vo import (
    AccountPasswordRecoveryApiMessageVO,
    AccountPasswordRecoveryResponseKeyVO,
)
from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationApiMessageVO,
    AccountPhoneVerificationErrorCodeVO,
)
from dealio.apps.common.helpers.decorators.rate_limit import rate_limit
from dealio.apps.common.response_utils import ResponseUtil
from dealio.apps.common.utils.common_utils import CommonUtils
from dealio.apps.core_models.constants.common_vo import ResponseVO
from dealio.apps.shared.views import BaseAPIView, BaseViewSet

User = get_user_model()
account_logic = AccountLogicRepository()
logger = CommonUtils.get_project_logger(__name__)


class ChangePasswordView(BaseViewSet):
    model_clz = User
    http_method_names = ["post"]
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    tag_name = "Account"

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data["current_password"]
        if not user.check_password(current_password):
            return ResponseUtil(
                custom_fields={"success": False, "message": "incorrect password provide"},
                status_code=ResponseVO.http_400,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return ResponseUtil(
            custom_fields={"success": True, "message": "successfully changed"},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=2, period=60, anonymous_limit=0), name="dispatch")
class UsersApiView(BaseAPIView):
    serializer_class = UserSerializer
    model_class = User

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        return ResponseUtil(
            data={"ok": True},
            status_code=ResponseVO.http_200,
        )


class UserViewSet(BaseViewSet):
    model_clz = User
    http_method_names = ["get"]
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

        code_issued = account_logic.send_verification_email_code(user)
        detail = (
            "Verification code sent successfully."
            if code_issued
            else "The previous verification code is still active."
        )

        return ResponseUtil(
            data={"detail": detail},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=20, period=60, anonymous_limit=0), name="dispatch")
class VerifyEmailCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"
    serializer_class = VerifyCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_valid = account_logic.check_email_validation_code(
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


@method_decorator(rate_limit(authenticated_limit=5, period=300, anonymous_limit=0), name="dispatch")
class SendPhoneVerificationCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"

    def post(self, request):
        result = account_logic.send_phone_verification_code(
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
        return ResponseUtil(
            data={"detail": message},
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=10, period=300, anonymous_limit=0), name="dispatch")
class VerifyPhoneCodeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    tag_name = "Manage-Account"
    serializer_class = PhoneVerificationCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = account_logic.verify_phone_number(
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


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=2, period=300), name="dispatch")
class SendForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSendCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_logic.send_forget_password_code_by_email(
            dto=SendPasswordRecoveryCodeDTO(
                email=serializer.validated_data["email"],
            ),
        )

        return ResponseUtil(
            data={
                AccountPasswordRecoveryResponseKeyVO.DETAIL.value: AccountPasswordRecoveryApiMessageVO.CODE_SENT.value,
            },
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="dispatch")
class VerifyForgotPasswordCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordVerifyCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = account_logic.reset_forget_password_by_email(
            dto=ResetPasswordDTO(
                email=serializer.validated_data["email"],
                code=serializer.validated_data["code"],
                new_password=serializer.validated_data["new_password"],
            ),
        )

        return _password_reset_response(result)


@method_decorator(rate_limit(authenticated_limit=5, anonymous_limit=2, period=300), name="dispatch")
class SendForgotPasswordSmsCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSmsSendCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        account_logic.send_forget_password_code_by_sms(
            dto=SendSmsPasswordRecoveryCodeDTO(
                phone_number=serializer.validated_data["phone_number"],
            ),
        )

        return ResponseUtil(
            data={
                AccountPasswordRecoveryResponseKeyVO.DETAIL.value: AccountPasswordRecoveryApiMessageVO.SMS_CODE_SENT.value,
            },
            status_code=ResponseVO.http_200,
        )


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="dispatch")
class VerifyForgotPasswordSmsCodeAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ForgotPasswordSmsVerifyCodeSerializer
    tag_name = "Manage-Account"

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = account_logic.reset_forget_password_by_sms(
            dto=ResetPasswordBySmsDTO(
                phone_number=serializer.validated_data["phone_number"],
                code=serializer.validated_data["code"],
                new_password=serializer.validated_data["new_password"],
            ),
        )

        return _password_reset_response(result)


@method_decorator(rate_limit(authenticated_limit=10, anonymous_limit=10, period=300), name="dispatch")
class BaseSocialOAuthLoginAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = SocialOAuthLoginSerializer
    tag_name = "Account"
    provider = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = SocialOAuthService()
        code = serializer.validated_data["code"]
        redirect_uri = serializer.validated_data["redirect_uri"]

        try:
            if self.provider == "google":
                token_data = service.login_with_google(code=code, redirect_uri=redirect_uri)
            elif self.provider == "github":
                token_data = service.login_with_github(code=code, redirect_uri=redirect_uri)
            else:
                return ResponseUtil(
                    data={"detail": "Unsupported OAuth provider."},
                    status_code=ResponseVO.http_400,
                )
        except OAuthProviderError as exc:
            logger.warning("OAuth login failed: %s", exc.log_message)
            response_status = (
                ResponseVO.http_500
                if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
                else ResponseVO.http_400
            )
            return ResponseUtil(
                data={"detail": exc.public_message},
                status_code=response_status,
            )

        return ResponseUtil(custom_fields=token_data, status_code=ResponseVO.http_200)


class GoogleOAuthLoginAPIView(BaseSocialOAuthLoginAPIView):
    provider = "google"


class GitHubOAuthLoginAPIView(BaseSocialOAuthLoginAPIView):
    provider = "github"


def _password_reset_response(result):
    if not result.is_success:
        return ResponseUtil(
            data={
                AccountPasswordRecoveryResponseKeyVO.DETAIL.value: AccountPasswordRecoveryApiMessageVO.INVALID_OR_EXPIRED_CODE.value,
            },
            status_code=ResponseVO.http_400,
        )

    return ResponseUtil(
        data={
            AccountPasswordRecoveryResponseKeyVO.DETAIL.value: AccountPasswordRecoveryApiMessageVO.PASSWORD_RESET_SUCCESS.value,
        },
        status_code=ResponseVO.http_200,
    )


def _phone_verification_error_message(error_code):
    messages = {
        AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND: AccountPhoneVerificationApiMessageVO.USER_NOT_FOUND.value,
        AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT: AccountPhoneVerificationApiMessageVO.INACTIVE_ACCOUNT.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED: AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_REQUIRED.value,
        AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED: AccountPhoneVerificationApiMessageVO.ALREADY_VERIFIED.value,
        AccountPhoneVerificationErrorCodeVO.INVALID_OR_EXPIRED_CODE: AccountPhoneVerificationApiMessageVO.INVALID_OR_EXPIRED_CODE.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE: AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_ALREADY_IN_USE.value,
    }
    return messages.get(
        error_code,
        AccountPhoneVerificationApiMessageVO.INVALID_OR_EXPIRED_CODE.value,
    )
