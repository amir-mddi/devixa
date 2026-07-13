from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AdminUserCreateDTO:
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str | None
    password: str
    role_id: UUID
    is_active: bool = True
    is_staff: bool = False


@dataclass(frozen=True, slots=True)
class AdminUserUpdateDTO:
    user_id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str | None
    role_id: UUID
    is_active: bool
    is_staff: bool
    email_verified: bool
    phone_number_verified: bool
    new_password: str = ""


@dataclass(frozen=True, slots=True)
class AdminNotificationDTO:
    provider: str
    message: str
    scheduled_at: object | None = None
