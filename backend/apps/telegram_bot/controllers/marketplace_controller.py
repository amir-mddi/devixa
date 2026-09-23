"""Thin controller mapping Telegram commands/callbacks to isolated use cases."""
from backend.apps.telegram_bot.logic.marketplace_bot_logic import MarketplaceBotLogic
from backend.apps.telegram_bot.vo.marketplace_vo import MarketplaceBotCallbackVO as C, MarketplaceBotSection


class MarketplaceBotController:
    def __init__(self, *, send_chain_message, language_resolver, linked_user_resolver, app_url_resolver, logic=None):
        self.send_chain_message = send_chain_message
        self.language_resolver = language_resolver
        self.linked_user_resolver = linked_user_resolver
        self.app_url_resolver = app_url_resolver
        self.logic = logic or MarketplaceBotLogic()

    def show(self, profile, section, message_id=None):
        language = self.language_resolver(profile)
        if section == MarketplaceBotSection.MENTORS:
            screen = self.logic.mentors(language)
        elif section == MarketplaceBotSection.COLLABORATIONS:
            screen = self.logic.collaborations(language, self.app_url_resolver())
        elif section == MarketplaceBotSection.WORKSPACE:
            screen = self.logic.workspace(language, self.linked_user_resolver(profile), self.app_url_resolver())
        else:
            screen = self.logic.menu(language)
        self.send_chain_message(profile, screen.text, reply_markup=screen.keyboard, message_id=message_id)

    def handle_callback(self, profile, callback, *, message_id=None):
        language = self.language_resolver(profile)
        if callback == C.MENU:
            screen = self.logic.menu(language)
        elif callback == C.MENTORS:
            screen = self.logic.mentors(language)
        elif callback == C.COLLABORATIONS:
            screen = self.logic.collaborations(language, self.app_url_resolver())
        elif callback == C.WORKSPACE:
            screen = self.logic.workspace(language, self.linked_user_resolver(profile), self.app_url_resolver())
        elif callback.startswith(C.PROJECT) and callback[len(C.PROJECT):].isdigit() and len(callback) - len(C.PROJECT) <= 18:
            screen = self.logic.collaboration_detail(language, int(callback[len(C.PROJECT):]), self.app_url_resolver())
        elif callback.startswith(C.OFFER) and callback[len(C.OFFER):].isdigit():
            screen = self.logic.offer(language, int(callback[len(C.OFFER):]))
        elif callback.startswith(C.BOOK) and callback[len(C.BOOK):].isdigit():
            screen = self.logic.book(language, int(callback[len(C.BOOK):]), self.linked_user_resolver(profile))
        else:
            return False
        self.send_chain_message(profile, screen.text, reply_markup=screen.keyboard, message_id=message_id)
        return True
