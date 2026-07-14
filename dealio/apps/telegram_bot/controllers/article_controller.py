from __future__ import annotations

from typing import Any, Callable

from dealio.apps.telegram_bot.logic.article_bot_logic import ArticleBotLogic
from dealio.apps.telegram_bot.vo.article_bot_vo import ArticleBotCallbackVO


class ArticleBotController:
    def __init__(
        self,
        *,
        logic: ArticleBotLogic,
        send_chain_message: Callable[..., None],
        is_admin_profile: Callable[[Any], bool],
        language_resolver: Callable[[Any], str],
    ):
        self.logic = logic
        self.send_chain_message = send_chain_message
        self.is_admin_profile = is_admin_profile
        self.language_resolver = language_resolver

    def clear_state(self, chat_id: int) -> None:
        self.logic.clear_state(chat_id)

    def show_menu(self, profile, *, message_id: int | None = None) -> None:
        screen = self.logic.menu_screen(
            language=self.language_resolver(profile),
            is_admin=self.is_admin_profile(profile),
        )
        self._deliver(profile, screen, message_id=message_id)

    def show_admin_list(self, profile, *, message_id: int | None = None) -> None:
        if not self.is_admin_profile(profile):
            self.show_menu(profile, message_id=message_id)
            return
        screen = self.logic.admin_list_screen(
            language=self.language_resolver(profile),
            page=1,
        )
        self._deliver(profile, screen, message_id=message_id)

    def handle_callback(self, profile, data: str, *, message_id: int | None = None) -> bool:
        result = self.logic.handle_callback(
            chat_id=profile.chat_id,
            language=self.language_resolver(profile),
            data=data,
            admin_user=self._admin_user(profile),
        )
        if not result.handled:
            return False
        if result.screen:
            self._deliver(profile, result.screen, message_id=message_id)
        return True

    def handle_text(self, profile, text: str) -> bool:
        result = self.logic.handle_text(
            chat_id=profile.chat_id,
            language=self.language_resolver(profile),
            text=text,
            admin_user=self._admin_user(profile),
        )
        if not result.handled:
            return False
        if result.screen:
            self._deliver(profile, result.screen)
        return True

    def _admin_user(self, profile):
        if self.is_admin_profile(profile) and profile.user_id:
            return profile.user
        return None

    def _deliver(self, profile, screen, *, message_id: int | None = None) -> None:
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": button.text, "callback_data": button.callback_data}
                    for button in row
                ]
                for row in screen.rows
            ]
        }
        self.send_chain_message(
            profile,
            screen.text,
            reply_markup=reply_markup,
            message_id=message_id,
        )
