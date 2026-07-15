from __future__ import annotations

from datetime import datetime

from backend.apps.common.email_service import send_html_email_async
from backend.apps.common.project_config import get_project_name
from backend.apps.telegram_bot.vo.account_link_vo import BotAccountLinkVO
from backend.apps.telegram_bot.vo.commerce_bot_vo import (
    TelegramBotLanguageVO,
    TelegramBotMessageTextVO,
)


class BotAccountLinkEmailAdapter:
    @staticmethod
    def send_code(
        *,
        user,
        code: str,
        provider: str,
        language: str,
        expiration_minutes: int,
    ) -> None:
        normalized_language = (
            language
            if language in TelegramBotLanguageVO.SUPPORTED
            else TelegramBotLanguageVO.EN
        )
        provider_name = BotAccountLinkVO.provider_display_name(provider)
        subject_template = TelegramBotMessageTextVO.LINK_EMAIL_SUBJECT[
            normalized_language
        ]

        send_html_email_async(
            subject=subject_template.format(provider_name=provider_name),
            template_name=(
                "emails/fa_telegram_link_code.html"
                if normalized_language == TelegramBotLanguageVO.FA
                else "emails/telegram_link_code.html"
            ),
            context={
                "subject": subject_template.format(provider_name=provider_name),
                "app_name": get_project_name(),
                "provider_name": provider_name,
                "user_name": (
                    user.first_name
                    or user.username
                    or TelegramBotMessageTextVO.DEFAULT_USER_NAME[
                        normalized_language
                    ]
                ),
                "code": code,
                "expiration_minutes": expiration_minutes,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )
