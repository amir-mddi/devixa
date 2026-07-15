from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from backend.apps.telegram_bot.models import TelegramProfile
from backend.apps.telegram_bot.vo.account_link_vo import BotAccountLinkMethodVO

User = get_user_model()


class BotAccountLinkPostgresAdapter:
    @staticmethod
    def find_active_user_by_email(email: str):
        return User.objects.filter(
            email__iexact=email,
            is_active=True,
            is_deleted=False,
        ).first()

    @staticmethod
    def find_active_user_by_phone(phone_number: str):
        return User.objects.filter(
            phone_number=phone_number,
            is_active=True,
            is_deleted=False,
        ).first()

    @staticmethod
    @transaction.atomic
    def link_profile(
        *,
        provider: str,
        chat_id: str,
        profile_id: int,
        user_id: str,
        verification_method: str,
    ) -> bool:
        profile = (
            TelegramProfile.objects.select_for_update()
            .filter(
                id=profile_id,
                messenger_provider=provider,
                chat_id=str(chat_id),
            )
            .first()
        )
        user = User.objects.select_for_update().filter(
            id=user_id,
            is_active=True,
            is_deleted=False,
        ).first()

        if not profile or not user:
            return False

        profile.user = user
        profile.is_verified = True
        profile.is_active = True
        profile.save(
            update_fields=[
                "user",
                "is_verified",
                "is_active",
                "updated_at",
            ]
        )

        if (
            verification_method == BotAccountLinkMethodVO.PHONE
            and not user.phone_number_verified
        ):
            user.phone_number_verified = True
            user.save(update_fields=["phone_number_verified", "updated_at"])

        return True
