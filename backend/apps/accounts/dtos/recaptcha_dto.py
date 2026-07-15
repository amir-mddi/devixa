from __future__ import annotations

from dataclasses import dataclass

from backend.apps.accounts.enums.recaptcha_enums import RecaptchaActionEnum


@dataclass(frozen=True, slots=True)
class RecaptchaVerificationDTO:
    token: str
    expected_action: RecaptchaActionEnum
    remote_ip: str | None = None
