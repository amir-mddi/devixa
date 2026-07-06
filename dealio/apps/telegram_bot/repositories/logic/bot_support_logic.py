from __future__ import annotations

from dealio.apps.telegram_bot.dtos.bot_support_dtos import (
    BotSupportCloseDTO,
    BotSupportReplyDTO,
    BotSupportTicketCreateDTO,
)
from dealio.apps.telegram_bot.repositories.adapters.bot_support_adapter import BotSupportDjangoAdapter


class BotSupportLogicRepository:
    def __init__(self, adapter: BotSupportDjangoAdapter | None = None):
        self.adapter = adapter or BotSupportDjangoAdapter()

    def list_user_tickets(self, *, provider: str, profile, limit: int = 10):
        return self.adapter.list_user_tickets(provider=provider, profile=profile, limit=limit)

    def list_admin_tickets(self, *, provider: str, status: str | None = None, limit: int = 10):
        return self.adapter.list_admin_tickets(provider=provider, status=status, limit=limit)

    def get_ticket(self, *, provider: str, ticket_id):
        return self.adapter.get_ticket(provider=provider, ticket_id=ticket_id)

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

    def add_user_message(self, *, provider: str, ticket_id, profile, message: str):
        return self.adapter.add_user_message(provider=provider, ticket_id=ticket_id, profile=profile, message=message)

    def reply(self, *, ticket_id, admin_user, message: str):
        return self.adapter.reply(BotSupportReplyDTO(ticket_id=ticket_id, admin_user_id=admin_user.id, message=message))

    def close(self, *, ticket_id, admin_user):
        return self.adapter.close(BotSupportCloseDTO(ticket_id=ticket_id, admin_user_id=admin_user.id))
