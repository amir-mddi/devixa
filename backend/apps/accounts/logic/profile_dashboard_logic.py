from __future__ import annotations

from backend.apps.accounts.dtos.profile_dto import AccountProfileDashboardDTO
from backend.apps.accounts.logic.profile_logic import AccountProfileLogic
from backend.apps.billing.repositories.logic import BillingLogicRepository
from backend.apps.courses.repositories.logic import CourseLogicRepository
from backend.apps.telegram_bot.repositories.logic.bot_support_logic import (
    BotSupportLogicRepository,
)
from backend.apps.telegram_bot.repositories.profile_repository import (
    TelegramProfileRepository,
)


class AccountProfileDashboardLogic:
    def __init__(
        self,
        profile_logic: AccountProfileLogic | None = None,
        course_logic: CourseLogicRepository | None = None,
        billing_logic: BillingLogicRepository | None = None,
        support_logic: BotSupportLogicRepository | None = None,
        messenger_profile_repository: TelegramProfileRepository | None = None,
    ):
        self.profile_logic = profile_logic or AccountProfileLogic()
        self.course_logic = course_logic or CourseLogicRepository()
        self.billing_logic = billing_logic or BillingLogicRepository()
        self.support_logic = support_logic or BotSupportLogicRepository()
        self.messenger_profile_repository = messenger_profile_repository or TelegramProfileRepository()

    def build(self, user) -> AccountProfileDashboardDTO:
        reviews = tuple(self.course_logic.list_user_reviews(user))
        payments = tuple(self.billing_logic.list_user_payments(user))
        return AccountProfileDashboardDTO(
            profile=self.profile_logic.get_profile(str(user.id)),
            enrollments=tuple(self.course_logic.list_user_enrollments(user)),
            orders=tuple(self.billing_logic.list_user_orders(user)),
            payments=payments,
            tickets=tuple(self.support_logic.list_account_tickets(user=user)),
            messenger_profiles=tuple(self.messenger_profile_repository.list_profiles_for_user(user)),
            reviews_by_course_id={str(review.course_id): review for review in reviews},
            receipt_upload_payment_ids=frozenset(
                payment.id
                for payment in payments
                if self.billing_logic.can_upload_receipt(payment)
            ),
        )
