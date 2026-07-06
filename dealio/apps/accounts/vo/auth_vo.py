from __future__ import annotations

from enum import StrEnum


class AccountAuthErrorCodeVO(StrEnum):
    INVALID_CREDENTIALS = "invalid_credentials"
    INACTIVE_ACCOUNT = "inactive_account"
    USERNAME_EXISTS = "username_exists"
    EMAIL_EXISTS = "email_exists"


class AccountUserQueryLookupVO(StrEnum):
    EMAIL_IEXACT = "email__iexact"
    USERNAME_IEXACT = "username__iexact"


class AccountUserFieldVO(StrEnum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    USERNAME = "username"
    EMAIL = "email"
    PASSWORD = "password"
    ROLE = "role"


class AccountRoleFieldVO(StrEnum):
    NAME = "name"


class AccountUserLookupVO(StrEnum):
    EMAIL_SEPARATOR = "@"


class AccountDefaultRoleVO(StrEnum):
    NAME = "کاربر سیستم"


class AccountSmsFallbackVO(StrEnum):
    VERIFICATION_CODE_USERNAME = "Verification_code"
