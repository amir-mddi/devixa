from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO


@dataclass(frozen=True, slots=True)
class LoginUserDTO:
    identifier: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterUserDTO:
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class PasswordValidationUserDTO:
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    email: str = ""


@dataclass(frozen=True, slots=True)
class AuthResultDTO:
    is_success: bool
    error_code: AccountAuthErrorCodeVO | None = None
    user: Any | None = None

    @classmethod
    def success(cls, *, user: Any | None = None) -> "AuthResultDTO":
        return cls(is_success=True, user=user)

    @classmethod
    def failed(cls, *, error_code: AccountAuthErrorCodeVO) -> "AuthResultDTO":
        return cls(is_success=False, error_code=error_code)
