from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccountProfileEntity:
    user_id: str
    username: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    email_verified: bool
    phone_number_verified: bool
    profile_photo_url: str
    date_joined: datetime | None
    last_login: datetime | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def initials(self) -> str:
        parts = [part for part in (self.first_name, self.last_name) if part]
        if parts:
            return "".join(part[0] for part in parts[:2]).upper()
        return (self.username[:2] or "U").upper()

    @classmethod
    def from_user(cls, user) -> "AccountProfileEntity":
        photo_url = ""
        profile_photo = getattr(user, "profile_photo", None)
        if profile_photo:
            try:
                photo_url = profile_photo.url
            except (ValueError, AttributeError):
                photo_url = ""

        return cls(
            user_id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number or "",
            email_verified=bool(user.email_verified),
            phone_number_verified=bool(user.phone_number_verified),
            profile_photo_url=photo_url,
            date_joined=getattr(user, "date_joined", None),
            last_login=getattr(user, "last_login", None),
        )
