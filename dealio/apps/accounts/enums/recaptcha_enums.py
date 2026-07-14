from __future__ import annotations

from enum import StrEnum


class RecaptchaActionEnum(StrEnum):
    LOGIN = "login"
    REGISTER = "register"
    FORGOT_PASSWORD = "forgot_password"


class RecaptchaFailureReasonEnum(StrEnum):
    DISABLED = "disabled"
    MISSING_TOKEN = "missing_token"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_REJECTED = "provider_rejected"
    ACTION_MISMATCH = "action_mismatch"
    SCORE_TOO_LOW = "score_too_low"
    HOSTNAME_MISMATCH = "hostname_mismatch"
    VERIFIED = "verified"
