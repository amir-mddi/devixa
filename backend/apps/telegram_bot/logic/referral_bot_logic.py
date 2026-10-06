from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from backend.apps.referrals.logic import ReferralLogic
from backend.apps.telegram_bot.dtos.lms_bot_dtos import ReferralBotScreenDTO
from backend.apps.telegram_bot.vo.referral_bot_vo import (
    ReferralBotCallbackVO, ReferralBotTextVO, ReferralBotWebPathVO,
)


class ReferralBotLogic:
    def __init__(self, referral_logic: ReferralLogic | None = None):
        self.referrals = referral_logic or ReferralLogic()

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
        summary = self.referrals.summary(user)
        t = lambda key, **kwargs: ReferralBotTextVO.get(language, key, **kwargs)
        lines = [t("title"), "", t("body", code=summary.code, count=summary.invited_count)]
        rows = []
        register_url = self._url(app_url, ReferralBotWebPathVO.REGISTER.format(code=summary.code))
        profile_url = self._url(app_url, ReferralBotWebPathVO.PROFILE)
        if register_url:
            lines.extend(["", t("share_hint")])
            rows.append((self._button(t("button_open"), url=register_url),))
        if profile_url:
            rows.append((self._button(t("button_profile"), url=profile_url),))
        rows.append((self._button(t("button_back"), callback_data=ReferralBotCallbackVO.MAIN_MENU),))
        return ReferralBotScreenDTO(text="\n".join(lines), keyboard=tuple(rows))
