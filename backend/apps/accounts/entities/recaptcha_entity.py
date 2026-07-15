from __future__ import annotations

from dataclasses import dataclass

from backend.apps.accounts.enums.recaptcha_enums import RecaptchaFailureReasonEnum


@dataclass(frozen=True, slots=True)
class RecaptchaProviderResponseEntity:
    success: bool
    score: float
    action: str
    hostname: str
    challenge_timestamp: str
    error_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecaptchaVerificationResultEntity:
    is_allowed: bool
    reason: RecaptchaFailureReasonEnum
    score: float | None = None
    hostname: str = ""
