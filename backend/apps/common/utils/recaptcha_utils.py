from __future__ import annotations

from backend.apps.common.utils.common_utils import CommonUtils


class ValidateReCaptcha:
    """Backward-compatible facade for legacy API callers.

    New account web flows use `RecaptchaVerificationLogic` directly. This
    facade remains so older imports do not call the removed duplicate provider
    implementation.
    """

    def validate(self, request, *, action="login") -> bool:
        from backend.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
        from backend.apps.accounts.enums.recaptcha_enums import RecaptchaActionEnum
        from backend.apps.accounts.logic.recaptcha_logic import RecaptchaVerificationLogic

        try:
            expected_action = RecaptchaActionEnum(action)
        except ValueError:
            return False

        request_data = getattr(request, "data", None) or getattr(request, "POST", {})
        token = request_data.get("recaptcha_token") or request_data.get("recaptcha") or ""
        result = RecaptchaVerificationLogic().verify(
            RecaptchaVerificationDTO(
                token=str(token),
                expected_action=expected_action,
                remote_ip=CommonUtils.get_client_ip(request),
            )
        )
        return result.is_allowed
