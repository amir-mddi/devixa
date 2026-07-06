from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from dealio.apps.telegram_bot.dtos.channel_member_sync_dtos import ChannelMemberCandidateDTO
from dealio.apps.telegram_bot.enums.channel_sync_enums import MessengerProviderEnum
from dealio.apps.telegram_bot.models import TelegramProfile


class ChannelMemberSyncRepository:
    """Reads known bot profiles from PostgreSQL.

    Bots cannot list every member in Telegram/Bale channels. Therefore this
    repository works with known users only: users who have interacted with the
    bot and have a TelegramProfile row. Cross-provider matching is based on the
    linked application user id.
    """

    def known_candidates(self) -> Iterable[ChannelMemberCandidateDTO]:
        profiles = (
            TelegramProfile.objects.filter(
                messenger_provider__in=[MessengerProviderEnum.TELEGRAM.value, MessengerProviderEnum.BALE.value],
                is_active=True,
                user_id__isnull=False,
            )
            .only("id", "user_id", "messenger_provider", "chat_id", "telegram_user_id")
            .order_by("user_id")
        )

        grouped: dict[int, dict[str, TelegramProfile]] = defaultdict(dict)
        for profile in profiles:
            grouped[int(profile.user_id)][profile.messenger_provider] = profile

        for user_id, provider_profiles in grouped.items():
            telegram_profile = provider_profiles.get(MessengerProviderEnum.TELEGRAM.value)
            bale_profile = provider_profiles.get(MessengerProviderEnum.BALE.value)

            yield ChannelMemberCandidateDTO(
                user_id=user_id,
                telegram_profile_id=telegram_profile.id if telegram_profile else None,
                telegram_chat_id=str(telegram_profile.chat_id) if telegram_profile else "",
                telegram_user_id=str(telegram_profile.telegram_user_id) if telegram_profile else "",
                bale_profile_id=bale_profile.id if bale_profile else None,
                bale_chat_id=str(bale_profile.chat_id) if bale_profile else "",
                bale_user_id=str(bale_profile.telegram_user_id) if bale_profile else "",
            )
