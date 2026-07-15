from __future__ import annotations

from backend.apps.telegram_bot.dtos.bot_support_dtos import (
    BotSupportCloseDTO,
    BotSupportReplyDTO,
    BotSupportTicketCreateDTO,
)
from backend.apps.telegram_bot.enums.support_enums import BotSupportProviderEnum
from backend.apps.telegram_bot.repositories.adapters.bot_support_adapter import (
    BotSupportDjangoAdapter,
)


class BotSupportLogicRepository:
    def __init__(self, adapter: BotSupportDjangoAdapter | None = None):
        self.adapter = adapter or BotSupportDjangoAdapter()

    def list_user_tickets(self, *, provider: str, profile, limit: int = 10):
        return self.adapter.list_user_tickets(
            provider=provider, profile=profile, limit=limit
        )

    def list_account_tickets(self, *, user, limit: int = 50):
        return self.adapter.list_account_tickets(user=user, limit=limit)

    def list_admin_tickets(
        self, *, provider: str, status: str | None = None, limit: int = 10
    ):
        return self.adapter.list_admin_tickets(
            provider=provider, status=status, limit=limit
        )

    def get_ticket(self, *, provider: str, ticket_id):
        return self.adapter.get_ticket(provider=provider, ticket_id=ticket_id)

    def get_account_ticket(self, *, ticket_id, user):
        return self.adapter.get_account_ticket(ticket_id=ticket_id, user=user)

    def list_frequently_asked_tickets(self, *, limit: int = 6):
        return self.adapter.list_frequently_asked_tickets(limit=limit)

    def create_ticket(self, *, provider: str, profile, message: str, subject: str = ""):
        return self.adapter.create_ticket(
            BotSupportTicketCreateDTO(
                provider=provider,
                profile_id=profile.id,
                user_id=profile.user_id,
                message=message,
                subject=subject,
            )
        )

    def create_account_ticket(self, *, user, message: str, subject: str = ""):
        return self.adapter.create_ticket(
            BotSupportTicketCreateDTO(
                provider=BotSupportProviderEnum.WEB.value,
                profile_id=None,
                user_id=user.id,
                message=message,
                subject=subject,
            )
        )

    def add_user_message(self, *, provider: str, ticket_id, profile, message: str):
        return self.adapter.add_user_message(
            provider=provider,
            ticket_id=ticket_id,
            profile=profile,
            message=message,
        )

    def add_account_user_message(self, *, ticket_id, user, message: str):
        return self.adapter.add_account_user_message(
            ticket_id=ticket_id,
            user=user,
            message=message,
        )

    def reply(self, *, ticket_id, admin_user, message: str):
        return self.adapter.reply(
            BotSupportReplyDTO(
                ticket_id=ticket_id,
                admin_user_id=admin_user.id,
                message=message,
            )
        )

    def close(self, *, ticket_id, admin_user):
        return self.adapter.close(
            BotSupportCloseDTO(
                ticket_id=ticket_id,
                admin_user_id=admin_user.id,
            )
        )
