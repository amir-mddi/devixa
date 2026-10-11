from __future__ import annotations

from django.contrib.auth import get_user_model

from backend.apps.accounts.dtos.session_auth_dto import PasswordValidationUserDTO


class PasswordValidationUserAdapter:
    """Provide Django password validators with an unsaved, model-compatible user."""

    @staticmethod
    def to_django_user(user):
        if not isinstance(user, PasswordValidationUserDTO):
            return user

        user_model = get_user_model()
        return user_model(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
        )
