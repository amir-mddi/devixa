from __future__ import annotations

from dealio.apps.accounts.enums.profile_enums import AccountProfileErrorCodeEnum
from dealio.apps.accounts.vo.auth_vo import AccountAuthErrorCodeVO
from dealio.apps.accounts.vo.password_recovery_vo import (
    AccountPasswordRecoveryErrorCodeVO,
)
from dealio.apps.accounts.vo.phone_verification_vo import (
    AccountPhoneVerificationApiMessageVO,
    AccountPhoneVerificationErrorCodeVO,
)
from dealio.apps.accounts.vo.profile_vo import AccountProfileMessageVO
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


class AccountWebProfileErrorPresenter:
    _MESSAGES_BY_ERROR_CODE = {
        AccountProfileErrorCodeEnum.USER_NOT_FOUND: AccountProfileMessageVO.PROFILE_NOT_FOUND.value,
        AccountProfileErrorCodeEnum.INACTIVE_ACCOUNT: AccountProfileMessageVO.INACTIVE_ACCOUNT.value,
        AccountProfileErrorCodeEnum.USERNAME_ALREADY_IN_USE: AccountProfileMessageVO.USERNAME_ALREADY_IN_USE.value,
        AccountProfileErrorCodeEnum.EMAIL_ALREADY_IN_USE: AccountProfileMessageVO.EMAIL_ALREADY_IN_USE.value,
        AccountProfileErrorCodeEnum.PHONE_NUMBER_ALREADY_IN_USE: AccountProfileMessageVO.PHONE_ALREADY_IN_USE.value,
    }
    _FIELDS_BY_ERROR_CODE = {
        AccountProfileErrorCodeEnum.USERNAME_ALREADY_IN_USE: AccountWebFieldNameVO.USERNAME.value,
        AccountProfileErrorCodeEnum.EMAIL_ALREADY_IN_USE: AccountWebFieldNameVO.EMAIL.value,
        AccountProfileErrorCodeEnum.PHONE_NUMBER_ALREADY_IN_USE: AccountWebFieldNameVO.PHONE_NUMBER.value,
    }
    _PHONE_MESSAGES_BY_ERROR_CODE = {
        AccountPhoneVerificationErrorCodeVO.USER_NOT_FOUND: AccountPhoneVerificationApiMessageVO.USER_NOT_FOUND.value,
        AccountPhoneVerificationErrorCodeVO.INACTIVE_ACCOUNT: AccountPhoneVerificationApiMessageVO.INACTIVE_ACCOUNT.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_REQUIRED: AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_REQUIRED.value,
        AccountPhoneVerificationErrorCodeVO.ALREADY_VERIFIED: AccountPhoneVerificationApiMessageVO.ALREADY_VERIFIED.value,
        AccountPhoneVerificationErrorCodeVO.PHONE_NUMBER_ALREADY_IN_USE: AccountPhoneVerificationApiMessageVO.PHONE_NUMBER_ALREADY_IN_USE.value,
    }

    @classmethod
    def message_for(cls, error_code) -> str:
        return cls._MESSAGES_BY_ERROR_CODE.get(
            error_code,
            AccountProfileMessageVO.PROFILE_NOT_FOUND.value,
        )

    @classmethod
    def field_for(cls, error_code) -> str | None:
        return cls._FIELDS_BY_ERROR_CODE.get(error_code)

    @classmethod
    def phone_verification_message_for(cls, error_code) -> str:
        return cls._PHONE_MESSAGES_BY_ERROR_CODE.get(
            error_code,
            AccountProfileMessageVO.PHONE_SEND_FAILED.value,
        )
