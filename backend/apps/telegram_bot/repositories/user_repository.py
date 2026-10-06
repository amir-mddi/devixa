from __future__ import annotations

from django.contrib.auth import get_user_model


User = get_user_model()


class TelegramUserRepository:
    """Persistence operations needed by Telegram/Bale/Rubika account flows."""

    @staticmethod
    def username_exists(username: str) -> bool:
        return User.objects.filter(username__iexact=username).exists()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email__iexact=email).exists()

    @staticmethod
    def phone_number_exists(phone_number: str) -> bool:
        return User.objects.filter(phone_number=phone_number).exists()

    @staticmethod
    def create_unverified_user(
        *,
        username: str,
        email: str,
        phone_number: str,
        first_name: str,
        last_name: str,
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=None,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            email_verified=False,
            phone_number_verified=False,
        )
