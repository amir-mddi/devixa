from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()


class AccountProfilePostgresAdapter:
    @staticmethod
    def get_user(user_id):
        return User.objects.filter(id=user_id, is_deleted=False).first()

    @staticmethod
    def username_is_used_by_other_user(*, username: str, user_id: str) -> bool:
        return (
            User.objects.filter(username__iexact=username).exclude(id=user_id).exists()
        )

    @staticmethod
    def email_is_used_by_other_user(*, email: str, user_id: str) -> bool:
        return User.objects.filter(email__iexact=email).exclude(id=user_id).exists()

    @staticmethod
    def phone_number_is_used_by_other_user(*, phone_number: str, user_id: str) -> bool:
        if not phone_number:
            return False
        return (
            User.objects.filter(phone_number=phone_number).exclude(id=user_id).exists()
        )

    @staticmethod
    def update_identity(
        *,
        user,
        first_name: str,
        last_name: str,
        username: str,
        profile_photo=None,
        remove_profile_photo: bool = False,
    ):
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        update_fields = ["first_name", "last_name", "username", "updated_at"]

        if remove_profile_photo:
            user.profile_photo = None
            update_fields.append("profile_photo")
        elif profile_photo is not None:
            user.profile_photo = profile_photo
            update_fields.append("profile_photo")

        user.save(update_fields=update_fields)
        return user

    @staticmethod
    def update_contacts(*, user, email: str, phone_number: str | None):
        user.email = email
        user.phone_number = phone_number or None
        user.save(update_fields=["email", "phone_number", "updated_at"])
        return user
