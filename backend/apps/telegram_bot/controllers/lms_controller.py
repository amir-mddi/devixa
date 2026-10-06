from __future__ import annotations

from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

from backend.apps.telegram_bot.logic.lms_bot_logic import LMSBotLogic
from backend.apps.telegram_bot.vo.lms_bot_vo import LMSBotCallbackVO, LMSBotTextVO


class LMSBotController:
    def __init__(self, *, logic=None, send_chain_message, language_resolver, linked_user_resolver, app_url_resolver):
        self.logic = logic or LMSBotLogic()
        self.send_chain_message = send_chain_message
        self.language_resolver = language_resolver
        self.linked_user_resolver = linked_user_resolver
        self.app_url_resolver = app_url_resolver

    @staticmethod
    def _keyboard(rows):
        return {"inline_keyboard": [list(row) for row in rows]}

    def show(self, profile, course_id, *, section=LMSBotCallbackVO.SECTION_CLASSROOM, message_id=None) -> bool:
        language = self.language_resolver(profile)
        user = self.linked_user_resolver(profile)
        if not user:
            self.send_chain_message(profile, LMSBotTextVO.get(language, "login_required"), message_id=message_id)
            return True
        methods = {
            LMSBotCallbackVO.SECTION_CLASSROOM: self.logic.classroom_screen,
            LMSBotCallbackVO.SECTION_LESSONS: self.logic.lessons_screen,
            LMSBotCallbackVO.SECTION_ASSIGNMENTS: self.logic.assignments_screen,
            LMSBotCallbackVO.SECTION_GRADES: self.logic.grades_screen,
            LMSBotCallbackVO.SECTION_QUESTIONS: self.logic.questions_screen,
        }
        try:
            screen = methods[section](user=user, course_id=course_id, language=language, app_url=self.app_url_resolver())
        except (PermissionDenied, NotFound):
            self.send_chain_message(profile, LMSBotTextVO.get(language, "access_denied"), message_id=message_id)
            return True
        self.send_chain_message(profile, screen.text, reply_markup=self._keyboard(screen.keyboard), message_id=message_id)
        return True

    def handle_callback(self, profile, data: str, *, message_id=None) -> bool:
        parsed = LMSBotCallbackVO.parse(data)
        if parsed is None:
            return False
        section, course_id = parsed
        return self.show(profile, course_id, section=section, message_id=message_id)
