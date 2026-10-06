from __future__ import annotations

from backend.apps.telegram_bot.logic.referral_bot_logic import ReferralBotLogic
from backend.apps.telegram_bot.vo.referral_bot_vo import ReferralBotCallbackVO, ReferralBotTextVO


class ReferralBotController:
    def __init__(self, *, logic=None, send_chain_message, language_resolver, linked_user_resolver, app_url_resolver):
        self.logic = logic or ReferralBotLogic()
        self.send_chain_message = send_chain_message
        self.language_resolver = language_resolver
        self.linked_user_resolver = linked_user_resolver
        self.app_url_resolver = app_url_resolver

    @staticmethod
    def _keyboard(rows):
        return {"inline_keyboard": [list(row) for row in rows]}

    def show(self, profile, *, message_id=None) -> bool:
        language = self.language_resolver(profile)
        user = self.linked_user_resolver(profile)
        if not user:
            self.send_chain_message(profile, ReferralBotTextVO.get(language, "login_required"), message_id=message_id)
            return True
        screen = self.logic.screen(user=user, language=language, app_url=self.app_url_resolver())
        self.send_chain_message(profile, screen.text, reply_markup=self._keyboard(screen.keyboard), message_id=message_id)
        return True

    def handle_callback(self, profile, data: str, *, message_id=None) -> bool:
        if not str(data or "").startswith(ReferralBotCallbackVO.PREFIX):
            return False
        language = self.language_resolver(profile)
        user = self.linked_user_resolver(profile)
        if not user:
            self.send_chain_message(profile, ReferralBotTextVO.get(language, "login_required"), message_id=message_id)
            return True
        if data == ReferralBotCallbackVO.CREATE_CHANNEL_LINK:
            created = self.logic.create_channel_link(user=user)
            if not created:
                self.send_chain_message(profile, ReferralBotTextVO.get(language, "channel_create_failed"), message_id=message_id)
                return True
            screen = self.logic.screen(user=user, language=language, app_url=self.app_url_resolver())
            text = f"{ReferralBotTextVO.get(language, 'channel_created')}\n\n{screen.text}"
            self.send_chain_message(profile, text, reply_markup=self._keyboard(screen.keyboard), message_id=message_id)
            return True
        return self.show(profile, message_id=message_id)

    def handle_chat_member_update(self, update: dict) -> bool:
        return self.logic.handle_chat_member_update(update)
