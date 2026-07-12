from __future__ import annotations

from dataclasses import dataclass

from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationErrorCodeVO,
)


@dataclass(frozen=True, slots=True)
class SendPhoneVerificationCodeDTO:
    user_id: str


@dataclass(frozen=True, slots=True)
class VerifyPhoneNumberDTO:
    user_id: str
    code: str


@dataclass(frozen=True, slots=True)
class VerifyPhoneNumberByTelegramDTO:
    user_id: str
    phone_number: str


@dataclass(frozen=True, slots=True)
class PhoneVerificationResultDTO:
    is_success: bool
    error_code: AccountPhoneVerificationErrorCodeVO | None = None
    code_issued: bool | None = None

    @classmethod
    def success(
        cls,
        *,
        code_issued: bool | None = None,
    ) -> "PhoneVerificationResultDTO":
        return cls(is_success=True, code_issued=code_issued)

    @classmethod
    def failed(
        cls,
        *,
        error_code: AccountPhoneVerificationErrorCodeVO,
    ) -> "PhoneVerificationResultDTO":
        return cls(is_success=False, error_code=error_code)
