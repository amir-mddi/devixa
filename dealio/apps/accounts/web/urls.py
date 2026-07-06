from __future__ import annotations

from django.urls import path

from dealio.apps.accounts.web.value_objects import (
    AccountWebAppNameVO,
    AccountWebPathVO,
    AccountWebRouteNameVO,
)
from dealio.apps.accounts.web.views import (
    ForgotPasswordPageView,
    LoginPageView,
    LogoutPageView,
    RecoverPasswordPageView,
    RegisterPageView,
)

app_name = AccountWebAppNameVO.NAMESPACE.value

urlpatterns = [
    path(
        AccountWebPathVO.LOGIN.value,
        LoginPageView.as_view(),
        name=AccountWebRouteNameVO.LOGIN.value,
    ),
    path(
        AccountWebPathVO.REGISTER.value,
        RegisterPageView.as_view(),
        name=AccountWebRouteNameVO.REGISTER.value,
    ),
    path(
        AccountWebPathVO.FORGOT_PASSWORD.value,
        ForgotPasswordPageView.as_view(),
        name=AccountWebRouteNameVO.FORGOT_PASSWORD.value,
    ),
    path(
        AccountWebPathVO.RECOVER_PASSWORD.value,
        RecoverPasswordPageView.as_view(),
        name=AccountWebRouteNameVO.RECOVER_PASSWORD.value,
    ),
    path(
        AccountWebPathVO.LOGOUT.value,
        LogoutPageView.as_view(),
        name=AccountWebRouteNameVO.LOGOUT.value,
    ),
]
