from __future__ import annotations

from django.utils.timezone import now

from dealio.apps.admin_panel.adapters import AdminBotClientFactory
from dealio.apps.admin_panel.repositories import AdminPanelRepository
from dealio.apps.billing.dtos import DiscountCreateDTO, PaymentReceiptReviewDTO
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.courses.dtos import ReviewModerationDTO
from dealio.apps.courses.enums import ReviewStatusEnum
from dealio.apps.courses.repositories.logic import CourseLogicRepository
from dealio.apps.telegram_bot.repositories.logic.bot_notification_logic import (
    BotNotificationLogicRepository,
)
from dealio.apps.telegram_bot.repositories.logic.bot_support_logic import (
    BotSupportLogicRepository,
)


class AdminPanelActionLogic:
    def __init__(
        self,
        *,
        repository: AdminPanelRepository | None = None,
        support_logic: BotSupportLogicRepository | None = None,
        billing_logic: BillingLogicRepository | None = None,
        course_logic: CourseLogicRepository | None = None,
        notification_logic: BotNotificationLogicRepository | None = None,
    ):
        self.repository = repository or AdminPanelRepository()
        self.support_logic = support_logic or BotSupportLogicRepository()
        self.billing_logic = billing_logic or BillingLogicRepository()
        self.course_logic = course_logic or CourseLogicRepository()
        self.notification_logic = notification_logic or BotNotificationLogicRepository()

    def list_tickets(self, **filters):
        return self.repository.list_tickets(**filters)

    def get_ticket(self, ticket_id):
        return self.repository.get_ticket(ticket_id)

    def reply_ticket(self, *, actor, ticket_id, message: str):
        return self.support_logic.reply(
            ticket_id=ticket_id,
            admin_user=actor,
            message=message,
        )

    def close_ticket(self, *, actor, ticket_id):
        return self.support_logic.close(ticket_id=ticket_id, admin_user=actor)

    def list_reviews(self, *, status: str = ""):
        return self.course_logic.list_reviews_for_admin(status=status or None)

    def moderate_review(self, *, actor, review_id, status: str, admin_note: str = ""):
        return self.course_logic.moderate_review(
            admin_user=actor,
            dto=ReviewModerationDTO(
                review_id=review_id,
                status=ReviewStatusEnum(status),
                admin_note=admin_note,
            ),
        )

    def list_orders(self, *, status: str = ""):
        return self.billing_logic.list_orders_for_admin(status=status or None)

    def list_payments(self, *, status: str = ""):
        return self.billing_logic.list_payments_for_admin(status=status or None)

    def list_receipts(self, *, status: str = ""):
        return self.billing_logic.list_receipts_for_admin(status=status or None)

    def get_receipt(self, receipt_id):
        return self.repository.get_receipt(receipt_id)

    def review_receipt(
        self,
        *,
        actor,
        receipt_id,
        approve: bool,
        admin_note: str = "",
        transaction_id: str = "",
    ):
        return self.billing_logic.review_receipt(
            actor=actor,
            dto=PaymentReceiptReviewDTO(
                receipt_id=receipt_id,
                approve=approve,
                admin_note=admin_note,
                transaction_id=transaction_id,
            ),
        )

    def list_discounts(self):
        return self.billing_logic.list_discount_codes_for_admin()

    def create_discount(self, *, actor, data: dict):
        return self.billing_logic.create_discount_code(
            actor=actor,
            dto=DiscountCreateDTO(**data),
        )

    def delete_discount(self, *, actor, discount_id):
        return self.billing_logic.delete_discount_code(
            actor=actor,
            discount_id=discount_id,
        )

    def list_notifications(self, *, provider: str = "", status: str = ""):
        return self.repository.list_scheduled_notifications(
            provider=provider,
            status=status,
        )

    def recipient_counts(self):
        return self.repository.messenger_recipient_counts()

    def create_notification(
        self, *, actor, provider: str, message: str, scheduled_at=None
    ):
        if scheduled_at and scheduled_at > now():
            return (
                self.notification_logic.schedule_notification(
                    provider=provider,
                    message=message,
                    scheduled_at=scheduled_at,
                    created_by=actor,
                ),
                False,
            )
        client = AdminBotClientFactory.create(provider)
        result = self.notification_logic.broadcast_to_linked_recipients(
            client=client,
            provider=provider,
            message=message,
        )
        return result, True
