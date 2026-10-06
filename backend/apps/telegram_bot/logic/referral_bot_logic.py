from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError

from backend.apps.referrals.logic import ChannelReferralLogic, ReferralLogic
from backend.apps.telegram_bot.dtos.lms_bot_dtos import ReferralBotScreenDTO
from backend.apps.telegram_bot.vo.referral_bot_vo import (
    ReferralBotCallbackVO,
    ReferralBotTextVO,
    ReferralBotWebPathVO,
)


class ReferralBotLogic:
    def __init__(
        self,
        referral_logic: ReferralLogic | None = None,
        channel_referral_logic: ChannelReferralLogic | None = None,
    ):
        self.referrals = referral_logic or ReferralLogic()
        self.channel_referrals = channel_referral_logic or ChannelReferralLogic()

    @staticmethod
    def _button(text: str, *, url: str | None = None, callback_data: str | None = None) -> dict:
        result = {"text": text}
        if url:
            result["url"] = url
        else:
            result["callback_data"] = callback_data or ReferralBotCallbackVO.MAIN_MENU
        return result

    @staticmethod
    def _url(base_url: str, path: str) -> str:
        try:
            parts = urlsplit((base_url or "").strip())
            if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password:
                origin = urlunsplit(("https", parts.netloc, "", "", ""))
                return f"{origin}/{path.lstrip('/')}"
        except ValueError:
            pass
        return ""

    def screen(self, *, user, language: str, app_url: str = "") -> ReferralBotScreenDTO:
        channel_link = self.channel_referrals.get_link(user)
        summary = self.referrals.public_summary(
            user,
            channel_username=self.channel_referrals.display_channel(),
            channel_invite_link=channel_link.invite_link if channel_link else "",
        )
        t = lambda key, **kwargs: ReferralBotTextVO.get(language, key, **kwargs)
        lines = [t("title"), "", t("body", code=summary.code)]
        if summary.channel_invite_link:
            lines.append(t("channel_ready", channel=summary.channel_username))
        else:
            lines.append(t("channel_missing", channel=summary.channel_username))
        lines.extend(["", t("private_stats")])

        rows = []
        register_url = self._url(app_url, ReferralBotWebPathVO.REGISTER.format(code=summary.code))
        profile_url = self._url(app_url, ReferralBotWebPathVO.PROFILE)
        if register_url:
            rows.append((self._button(t("button_register"), url=register_url),))
        if summary.channel_invite_link:
            rows.append((self._button(t("button_open_channel"), url=summary.channel_invite_link),))
        else:
            rows.append((self._button(t("button_create_channel"), callback_data=ReferralBotCallbackVO.CREATE_CHANNEL_LINK),))
        if profile_url:
            rows.append((self._button(t("button_profile"), url=profile_url),))
        rows.append((self._button(t("button_back"), callback_data=ReferralBotCallbackVO.MAIN_MENU),))
        return ReferralBotScreenDTO(text="\n".join(lines), keyboard=tuple(rows))

    def create_channel_link(self, *, user) -> bool:
        try:
            self.channel_referrals.get_or_create_link(user)
            return True
        except (ValidationError, RuntimeError):
            return False

    def handle_chat_member_update(self, update: dict) -> bool:
        return self.channel_referrals.process_chat_member_update(update)
