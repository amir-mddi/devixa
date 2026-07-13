from __future__ import annotations

import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from dealio.apps.accounts.web.value_objects import (
    AccountWebEmailVO,
    AccountWebPasswordValidationCodeVO,
    AccountWebRegexVO,
    AccountWebValidationMessageVO,
)
from dealio.apps.common.helpers.validators.account_validators import (
    validate_iranian_phone_number,
)


class AccountWebInputValidator:
    @classmethod
    def validate_persian_text(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValidationError(AccountWebValidationMessageVO.REQUIRED.value)

        if not re.fullmatch(AccountWebRegexVO.PERSIAN_TEXT.value, normalized_value):
            raise ValidationError(
                AccountWebValidationMessageVO.INVALID_PERSIAN_TEXT.value
            )

        return normalized_value

    @classmethod
    def validate_english_username(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValidationError(AccountWebValidationMessageVO.REQUIRED.value)

        if not re.fullmatch(AccountWebRegexVO.ENGLISH_USERNAME.value, normalized_value):
            raise ValidationError(AccountWebValidationMessageVO.INVALID_USERNAME.value)

        return normalized_value

    @classmethod
    def validate_gmail_email(cls, value: str) -> str:
        normalized_value = value.lower().strip()

        if not normalized_value:
            raise ValidationError(AccountWebValidationMessageVO.REQUIRED.value)

        try:
            validate_email(normalized_value)
        except ValidationError as exc:
            raise ValidationError(
                AccountWebValidationMessageVO.INVALID_EMAIL.value
            ) from exc

        if not normalized_value.endswith(AccountWebEmailVO.GMAIL_SUFFIX.value):
            raise ValidationError(AccountWebValidationMessageVO.INVALID_GMAIL.value)

        return normalized_value

    @classmethod
    def validate_phone_number(cls, value: str, *, required: bool = False) -> str:
        normalized_value = (value or "").strip()
        if not normalized_value and not required:
            return ""
        try:
            return validate_iranian_phone_number(normalized_value)
        except serializers.ValidationError as exc:
            raise ValidationError(
                AccountWebValidationMessageVO.INVALID_PHONE_NUMBER.value
            ) from exc

    @classmethod
    def validate_recovery_code(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValidationError(AccountWebValidationMessageVO.REQUIRED.value)

        if not re.fullmatch(AccountWebRegexVO.RECOVERY_CODE.value, normalized_value):
            raise ValidationError(
                AccountWebValidationMessageVO.INVALID_RECOVERY_CODE.value
            )

        return normalized_value

    @classmethod
    def validate_password(cls, password: str, user=None) -> None:
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise ValidationError(cls._translate_password_errors(exc)) from exc

    @classmethod
    def _translate_password_errors(cls, exc: ValidationError) -> list[str]:
        return [cls._translate_password_error(error) for error in exc.error_list]

    @classmethod
    def _translate_password_error(cls, error: ValidationError) -> str:
        error_code = getattr(error, "code", None)
        error_params = getattr(error, "params", None) or {}

        if error_code == AccountWebPasswordValidationCodeVO.PASSWORD_TOO_SHORT.value:
            return AccountWebValidationMessageVO.PASSWORD_TOO_SHORT.value % error_params

        if error_code == AccountWebPasswordValidationCodeVO.PASSWORD_TOO_COMMON.value:
            return AccountWebValidationMessageVO.PASSWORD_TOO_COMMON.value

        if (
            error_code
            == AccountWebPasswordValidationCodeVO.PASSWORD_ENTIRELY_NUMERIC.value
        ):
            return AccountWebValidationMessageVO.PASSWORD_ENTIRELY_NUMERIC.value

        if error_code == AccountWebPasswordValidationCodeVO.PASSWORD_TOO_SIMILAR.value:
            return AccountWebValidationMessageVO.PASSWORD_TOO_SIMILAR.value

        return AccountWebValidationMessageVO.PASSWORD_INVALID.value
