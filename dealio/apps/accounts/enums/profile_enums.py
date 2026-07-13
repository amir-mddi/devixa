from enum import StrEnum


class AccountProfileErrorCodeEnum(StrEnum):
    USER_NOT_FOUND = "user_not_found"
    INACTIVE_ACCOUNT = "inactive_account"
    USERNAME_ALREADY_IN_USE = "username_already_in_use"
    EMAIL_ALREADY_IN_USE = "email_already_in_use"
    PHONE_NUMBER_ALREADY_IN_USE = "phone_number_already_in_use"
