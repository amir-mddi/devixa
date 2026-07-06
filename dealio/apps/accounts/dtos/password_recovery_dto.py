from __future__ import annotations

from dataclasses import dataclass

from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO


@dataclass(frozen=True, slots=True)
class SendPasswordRecoveryCodeDTO:
    email: str


@dataclass(frozen=True, slots=True)
class ResetPasswordDTO:
    email: str
    code: str
    new_password: str


@dataclass(frozen=True, slots=True)
class PasswordRecoveryResultDTO:
    is_success: bool
    error_code: AccountPasswordRecoveryErrorCodeVO | None = None

    @classmethod
    def success(cls) -> "PasswordRecoveryResultDTO":
        return cls(is_success=True)

    @classmethod
    def failed(
        cls,
        *,
        error_code: AccountPasswordRecoveryErrorCodeVO,
    ) -> "PasswordRecoveryResultDTO":
        return cls(is_success=False, error_code=error_code)
