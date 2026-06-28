from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from dealio.apps.accounts.views import ChangePasswordView, UserViewSet, UsersApiView, SendEmailVerificationCodeAPIView, \
    VerifyEmailCodeAPIView, SendForgotPasswordCodeAPIView, VerifyForgotPasswordCodeAPIView, \
    GoogleOAuthLoginAPIView, GitHubOAuthLoginAPIView
from dealio.apps.common.helpers.jwt.custom_jwt import CustomTokenObtainPairView

router = routers.DefaultRouter()

router.register("change_password", ChangePasswordView, basename='change-password')
router.register("users", UserViewSet, basename='users')
urlpatterns = [
    path(
        "users/",
        UsersApiView.as_view(
            http_method_names=["get", "post", "head", "options"]
        ),
        name="users-list-create",
    ),
    path(
        "users/<uuid:pk>/",
        UsersApiView.as_view(
            http_method_names=["get", "put", "delete"]
        ),
        name="users-detail",
    ),
    path(
        "email-verification/send/",
        SendEmailVerificationCodeAPIView.as_view(
            http_method_names=["post"]
        ),
        name="send-email-verification-code",
    ),
    path(
        "email-verification/verify/",
        VerifyEmailCodeAPIView.as_view(
            http_method_names=["post"]
        ),
        name="verify-email-code",
    ),
    path(
        "forgot-password/send/",
        SendForgotPasswordCodeAPIView.as_view(
            http_method_names=["post"]
        ),
        name="send-forgot-password-code",
    ),
    path(
        "forgot-password/verify/",
        VerifyForgotPasswordCodeAPIView.as_view(
            http_method_names=["post"]
        ),
        name="verify-forgot-password-code",
    ),
    path('signin/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('oauth/google/', GoogleOAuthLoginAPIView.as_view(http_method_names=["post"]), name='google-oauth-login'),
    path('oauth/github/', GitHubOAuthLoginAPIView.as_view(http_method_names=["post"]), name='github-oauth-login'),
    path('', include(router.urls)),
]
