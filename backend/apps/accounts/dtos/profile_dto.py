from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.apps.accounts.enums.profile_enums import AccountProfileErrorCodeEnum


@dataclass(frozen=True, slots=True)
class UpdateAccountProfileDTO:
    user_id: str
    first_name: str
    last_name: str
    username: str
    profile_photo: Any | None = None
    remove_profile_photo: bool = False


@dataclass(frozen=True, slots=True)
class UpdateAccountContactDTO:
    user_id: str
    email: str
    phone_number: str | None


@dataclass(frozen=True, slots=True)
class AccountProfileUpdateResultDTO:
    is_success: bool
    user: Any | None = None
    error_code: AccountProfileErrorCodeEnum | None = None
    email_changed: bool = False
    phone_number_changed: bool = False

    @classmethod
    def success(
        cls,
        *,
        user: Any,
        email_changed: bool = False,
        phone_number_changed: bool = False,
    ) -> "AccountProfileUpdateResultDTO":
        return cls(
            is_success=True,
            user=user,
            email_changed=email_changed,
            phone_number_changed=phone_number_changed,
        )

    @classmethod
    def failed(
        cls,
        *,
        error_code: AccountProfileErrorCodeEnum,
    ) -> "AccountProfileUpdateResultDTO":
        return cls(is_success=False, error_code=error_code)


@dataclass(frozen=True, slots=True)
class AccountProfileDashboardDTO:
    profile: Any
    enrollments: tuple[Any, ...]
    orders: tuple[Any, ...]
    payments: tuple[Any, ...]
    tickets: tuple[Any, ...]
    messenger_profiles: tuple[Any, ...]
    reviews_by_course_id: dict[str, Any]
    receipt_upload_payment_ids: frozenset[Any]
