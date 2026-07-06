from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import NotFound, ValidationError

from dealio.apps.telegram_bot.dtos.bot_support_dtos import (
    BotSupportCloseDTO,
    BotSupportReplyDTO,
    BotSupportTicketCreateDTO,
)
from dealio.apps.telegram_bot.models import BotSupportMessage, BotSupportTicket, TelegramProfile

User = get_user_model()


class BotSupportDjangoAdapter:
    def list_user_tickets(self, *, provider: str, profile: TelegramProfile, limit: int = 10):
        return list(
            BotSupportTicket.objects.filter(provider=provider, profile=profile)
            .prefetch_related("messages")
            .order_by("-last_message_at")[:limit]
        )

    def list_admin_tickets(self, *, provider: str, status: str | None = None, limit: int = 10):
        queryset = (
            BotSupportTicket.objects.select_related("profile", "user")
            .prefetch_related("messages")
            .filter(provider=provider)
        )
        if status:
            queryset = queryset.filter(status=status)
        return list(queryset.order_by("-last_message_at")[:limit])

    def get_ticket(self, *, provider: str, ticket_id):
        ticket = (
            BotSupportTicket.objects.select_related("profile", "user")
            .prefetch_related("messages", "messages__sender_user")
            .filter(id=ticket_id, provider=provider)
            .first()
        )
        if not ticket:
            raise NotFound("Support ticket not found.")
        return ticket

    @staticmethod
    def list_frequently_asked_tickets(*, limit: int = 6):
        return (
            BotSupportTicket.objects.filter(is_frequently_asked=True)
            .prefetch_related("messages")
            .order_by("faq_display_order", "-last_message_at")[:limit]
        )

    def create_ticket(self, dto: BotSupportTicketCreateDTO):
        profile = TelegramProfile.objects.filter(id=dto.profile_id, messenger_provider=dto.provider).first()
        if not profile:
            raise NotFound("Bot profile not found.")
        text = (dto.message or "").strip()
        if not text:
            raise ValidationError("Support message cannot be empty.")
        ticket = BotSupportTicket.objects.create(
            provider=dto.provider,
            profile=profile,
            user_id=dto.user_id,
            subject=(dto.subject or text[:80]).strip(),
            status=BotSupportTicket.STATUS_OPEN,
            last_message_at=now(),
        )
        BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_USER,
            sender_user_id=dto.user_id,
            message=text,
        )
        return ticket

    @transaction.atomic
    def add_user_message(self, *, provider: str, ticket_id, profile: TelegramProfile, message: str):
        ticket = self.get_ticket(provider=provider, ticket_id=ticket_id)
        if ticket.profile_id != profile.id:
            raise NotFound("Support ticket not found.")
        if ticket.status == BotSupportTicket.STATUS_CLOSED:
            raise ValidationError("This ticket is already closed.")
        text = (message or "").strip()
        if not text:
            raise ValidationError("Support message cannot be empty.")
        msg = BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_USER,
            sender_user=profile.user,
            message=text,
        )
        ticket.status = BotSupportTicket.STATUS_OPEN
        ticket.last_message_at = now()
        ticket.save(update_fields=["status", "last_message_at", "updated_at"])
        return ticket, msg

    @transaction.atomic
    def reply(self, dto: BotSupportReplyDTO):
        ticket = self.get_ticket(provider="telegram", ticket_id=dto.ticket_id)
        if ticket.status == BotSupportTicket.STATUS_CLOSED:
            raise ValidationError("This ticket is already closed.")
        admin_user = User.objects.filter(id=dto.admin_user_id).first()
        text = (dto.message or "").strip()
        if not text:
            raise ValidationError("Reply cannot be empty.")
        msg = BotSupportMessage.objects.create(
            ticket=ticket,
            sender_type=BotSupportMessage.SENDER_ADMIN,
            sender_user=admin_user,
            message=text,
        )
        ticket.status = BotSupportTicket.STATUS_ANSWERED
        ticket.last_message_at = now()
        ticket.save(update_fields=["status", "last_message_at", "updated_at"])
        return ticket, msg

    @transaction.atomic
    def close(self, dto: BotSupportCloseDTO):
        ticket = self.get_ticket(provider="telegram", ticket_id=dto.ticket_id)
        ticket.status = BotSupportTicket.STATUS_CLOSED
        ticket.closed_by_id = dto.admin_user_id
        ticket.closed_at = now()
        ticket.last_message_at = now()
        ticket.save(update_fields=["status", "closed_by", "closed_at", "last_message_at", "updated_at"])
        return ticket
