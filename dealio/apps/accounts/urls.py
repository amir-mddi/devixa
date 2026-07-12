from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from dealio.apps.accounts.views import (
    ChangePasswordView,
    GitHubOAuthLoginAPIView,
    GoogleOAuthLoginAPIView,
    SendEmailVerificationCodeAPIView,
    SendForgotPasswordCodeAPIView,
    SendForgotPasswordSmsCodeAPIView,
    SendPhoneVerificationCodeAPIView,
    UserViewSet,
    VerifyEmailCodeAPIView,
    VerifyForgotPasswordCodeAPIView,
    VerifyForgotPasswordSmsCodeAPIView,
    VerifyPhoneCodeAPIView,
)
from dealio.apps.common.helpers.jwt.custom_jwt import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

router = routers.DefaultRouter()
router.register("change_password", ChangePasswordView, basename="change-password")
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path(
        "email-verification/send/",
        SendEmailVerificationCodeAPIView.as_view(http_method_names=["post"]),
        name="send-email-verification-code",
    ),
    path(
        "email-verification/verify/",
        VerifyEmailCodeAPIView.as_view(http_method_names=["post"]),
        name="verify-email-code",
    ),
    path(
        "phone-verification/send/",
        SendPhoneVerificationCodeAPIView.as_view(http_method_names=["post"]),
        name="send-phone-verification-code",
    ),
    path(
        "phone-verification/verify/",
        VerifyPhoneCodeAPIView.as_view(http_method_names=["post"]),
        name="verify-phone-code",
    ),
    path(
        "forgot-password/send/",
        SendForgotPasswordCodeAPIView.as_view(http_method_names=["post"]),
        name="send-forgot-password-code",
    ),
    path(
        "forgot-password/verify/",
        VerifyForgotPasswordCodeAPIView.as_view(http_method_names=["post"]),
        name="verify-forgot-password-code",
    ),
    path(
        "forgot-password/sms/send/",
        SendForgotPasswordSmsCodeAPIView.as_view(http_method_names=["post"]),
        name="send-forgot-password-sms-code",
    ),
    path(
        "forgot-password/sms/verify/",
        VerifyForgotPasswordSmsCodeAPIView.as_view(http_method_names=["post"]),
        name="verify-forgot-password-sms-code",
    ),
    path("signin/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("oauth/google/", GoogleOAuthLoginAPIView.as_view(http_method_names=["post"]), name="google-oauth-login"),
    path("oauth/github/", GitHubOAuthLoginAPIView.as_view(http_method_names=["post"]), name="github-oauth-login"),
    path("", include(router.urls)),
]
