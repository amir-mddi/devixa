from __future__ import annotations

from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO
from dealio.apps.accounts.vo.password_recovery_vo import AccountPasswordRecoveryErrorCodeVO
from dealio.apps.accounts.web.value_objects import (
    AccountWebFieldNameVO,
    AccountWebValidationMessageVO,
)


class AccountWebAuthErrorPresenter:
    _MESSAGES_BY_ERROR_CODE = {
        AccountAuthErrorCodeVO.INVALID_CREDENTIALS: AccountWebValidationMessageVO.INVALID_CREDENTIALS.value,
        AccountAuthErrorCodeVO.INACTIVE_ACCOUNT: AccountWebValidationMessageVO.INACTIVE_ACCOUNT.value,
        AccountAuthErrorCodeVO.USERNAME_EXISTS: AccountWebValidationMessageVO.USERNAME_EXISTS.value,
        AccountAuthErrorCodeVO.EMAIL_EXISTS: AccountWebValidationMessageVO.EMAIL_EXISTS.value,
    }
    _FIELDS_BY_ERROR_CODE = {
        AccountAuthErrorCodeVO.USERNAME_EXISTS: AccountWebFieldNameVO.USERNAME.value,
        AccountAuthErrorCodeVO.EMAIL_EXISTS: AccountWebFieldNameVO.EMAIL.value,
    }

    @classmethod
    def message_for(cls, error_code: AccountAuthErrorCodeVO | None) -> str:
        if not error_code:
            return AccountWebValidationMessageVO.PASSWORD_INVALID.value
        return cls._MESSAGES_BY_ERROR_CODE.get(
            error_code,
            AccountWebValidationMessageVO.PASSWORD_INVALID.value,
        )

    @classmethod
    def field_for(cls, error_code: AccountAuthErrorCodeVO | None) -> str | None:
        if not error_code:
            return None
        return cls._FIELDS_BY_ERROR_CODE.get(error_code)


class AccountWebPasswordRecoveryErrorPresenter:
    _MESSAGES_BY_ERROR_CODE = {
        AccountPasswordRecoveryErrorCodeVO.INVALID_OR_EXPIRED_CODE: AccountWebValidationMessageVO.INVALID_OR_EXPIRED_RECOVERY_CODE.value,
        AccountPasswordRecoveryErrorCodeVO.INACTIVE_ACCOUNT: AccountWebValidationMessageVO.INACTIVE_ACCOUNT.value,
        AccountPasswordRecoveryErrorCodeVO.USER_NOT_FOUND: AccountWebValidationMessageVO.INVALID_OR_EXPIRED_RECOVERY_CODE.value,
    }

    @classmethod
    def message_for(cls, error_code: AccountPasswordRecoveryErrorCodeVO | None) -> str:
        if not error_code:
            return AccountWebValidationMessageVO.INVALID_OR_EXPIRED_RECOVERY_CODE.value
        return cls._MESSAGES_BY_ERROR_CODE.get(
            error_code,
            AccountWebValidationMessageVO.INVALID_OR_EXPIRED_RECOVERY_CODE.value,
        )
