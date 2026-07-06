from __future__ import annotations

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic.edit import FormView

from dealio.apps.accounts.repositories.account_logic import AccountLogicRepository
from dealio.apps.accounts.web.forms import (
    ForgotPasswordTemplateForm,
    LoginTemplateForm,
    RecoverPasswordTemplateForm,
    RegisterTemplateForm,
)
from dealio.apps.accounts.web.presenters import (
    AccountWebAuthErrorPresenter,
    AccountWebPasswordRecoveryErrorPresenter,
)
from dealio.apps.pages.vo.page_vo import PageWebReverseNameVO
from dealio.apps.accounts.web.value_objects import (
    AccountWebFieldNameVO,
    AccountWebRequestKeyVO,
    AccountWebReverseNameVO,
    AccountWebTemplateVO,
    AccountWebUrlSeparatorVO,
    AccountWebValidationMessageVO,
)


class SafeNextUrlMixin:
    fallback_success_url = reverse_lazy(PageWebReverseNameVO.HOME.value)

    def get_success_url(self):
        next_url = self.request.POST.get(AccountWebRequestKeyVO.NEXT.value) or self.request.GET.get(
            AccountWebRequestKeyVO.NEXT.value
        )
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return self.fallback_success_url


class LoginPageView(SafeNextUrlMixin, FormView):
    template_name = AccountWebTemplateVO.LOGIN.value
    form_class = LoginTemplateForm
    fallback_success_url = reverse_lazy(PageWebReverseNameVO.HOME.value)
    account_logic_repository_class = AccountLogicRepository
    error_presenter_class = AccountWebAuthErrorPresenter

    def form_valid(self, form):
        result = self.account_logic_repository_class().authenticate_user_by_identifier(
            request=self.request,
            dto=form.to_dto(),
        )

        if not result.is_success:
            form.add_error(None, self.error_presenter_class.message_for(result.error_code))
            return self.form_invalid(form)

        django_login(self.request, result.user)
        messages.success(self.request, AccountWebValidationMessageVO.LOGIN_SUCCESS.value)
        return redirect(self.get_success_url())


class RegisterPageView(FormView):
    template_name = AccountWebTemplateVO.REGISTER.value
    form_class = RegisterTemplateForm
    success_url = reverse_lazy(AccountWebReverseNameVO.LOGIN.value)
    account_logic_repository_class = AccountLogicRepository
    error_presenter_class = AccountWebAuthErrorPresenter

    def form_valid(self, form):
        result = self.account_logic_repository_class().register_user_account(dto=form.to_dto())

        if not result.is_success:
            form.add_error(
                self.error_presenter_class.field_for(result.error_code),
                self.error_presenter_class.message_for(result.error_code),
            )
            return self.form_invalid(form)

        messages.success(self.request, AccountWebValidationMessageVO.REGISTER_SUCCESS.value)
        return redirect(self.get_success_url())


class ForgotPasswordPageView(FormView):
    template_name = AccountWebTemplateVO.FORGOT_PASSWORD.value
    form_class = ForgotPasswordTemplateForm
    success_url = reverse_lazy(AccountWebReverseNameVO.RECOVER_PASSWORD.value)
    account_logic_repository_class = AccountLogicRepository

    def form_valid(self, form):
        dto = form.to_dto()
        self.account_logic_repository_class().send_forget_password_code_by_email(dto=dto)
        messages.success(self.request, AccountWebValidationMessageVO.RECOVERY_CODE_SENT.value)
        return redirect(self._build_recover_password_url(email=dto.email))

    @staticmethod
    def _build_recover_password_url(*, email: str) -> str:
        query = urlencode({AccountWebFieldNameVO.EMAIL.value: email})
        return (
            reverse(AccountWebReverseNameVO.RECOVER_PASSWORD.value)
            + AccountWebUrlSeparatorVO.QUERY.value
            + query
        )


class RecoverPasswordPageView(FormView):
    template_name = AccountWebTemplateVO.RECOVER_PASSWORD.value
    form_class = RecoverPasswordTemplateForm
    success_url = reverse_lazy(AccountWebReverseNameVO.LOGIN.value)
    account_logic_repository_class = AccountLogicRepository
    error_presenter_class = AccountWebPasswordRecoveryErrorPresenter

    def get_initial(self):
        initial = super().get_initial()
        email = self.request.GET.get(AccountWebFieldNameVO.EMAIL.value)
        if email:
            initial[AccountWebFieldNameVO.EMAIL.value] = email
        return initial

    def form_valid(self, form):
        result = self.account_logic_repository_class().reset_forget_password_by_email(dto=form.to_dto())

        if not result.is_success:
            form.add_error(None, self.error_presenter_class.message_for(result.error_code))
            return self.form_invalid(form)

        messages.success(self.request, AccountWebValidationMessageVO.PASSWORD_RESET_SUCCESS.value)
        return redirect(self.get_success_url())


class LogoutPageView(View):
    def post(self, request, *args, **kwargs):
        django_logout(request)
        messages.success(request, AccountWebValidationMessageVO.LOGOUT_SUCCESS.value)
        return redirect(PageWebReverseNameVO.HOME.value)
