from __future__ import annotations

from django.conf import settings

from backend.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from backend.apps.accounts.enums.recaptcha_enums import RecaptchaActionEnum
from backend.apps.accounts.logic.recaptcha_logic import RecaptchaVerificationLogic
from backend.apps.accounts.web.value_objects import (
    AccountWebFieldNameVO,
    AccountWebValidationMessageVO,
)
from backend.apps.common.utils.common_utils import CommonUtils


class RecaptchaProtectedFormViewMixin:
    recaptcha_action: RecaptchaActionEnum
    recaptcha_logic_class = RecaptchaVerificationLogic

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "recaptcha_enabled": settings.RECAPTCHA_ENABLED,
                "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
                "recaptcha_action": self.recaptcha_action.value,
                "recaptcha_client_error_message": (
                    AccountWebValidationMessageVO.RECAPTCHA_UNAVAILABLE.value
                ),
            }
        )
        return context

    def form_valid(self, form):
        result = self.recaptcha_logic_class().verify(
            RecaptchaVerificationDTO(
                token=str(
                    form.cleaned_data.get(
                        AccountWebFieldNameVO.RECAPTCHA_TOKEN.value,
                        "",
                    )
                    or ""
                ),
                expected_action=self.recaptcha_action,
                remote_ip=CommonUtils.get_client_ip(self.request),
            )
        )
        if not result.is_allowed:
            form.add_error(
                None,
                AccountWebValidationMessageVO.RECAPTCHA_FAILED.value,
            )
            return self.form_invalid(form)
        return self.recaptcha_form_valid(form)

    def recaptcha_form_valid(self, form):
        return super().form_valid(form)
