from __future__ import annotations

import os
from uuid import UUID

from django.db.models import QuerySet

from dealio.apps.billing.dtos import (
    CheckoutDTO,
    PaymentConfirmDTO,
    PaymentReceiptReviewDTO,
    PaymentReceiptUploadDTO,
    PaymentStartDTO,
)
from dealio.apps.billing.enums import (
    OrderStatusEnum,
    PaymentProviderEnum,
    PaymentReceiptSourceEnum,
    PaymentReceiptStatusEnum,
    PaymentStatusEnum,
)
from dealio.apps.billing.models import Order, Payment, PaymentReceipt
from dealio.apps.billing.repositories.logic import BillingLogicRepository
from dealio.apps.courses.dtos import (
    CourseCreateDTO,
    CourseLessonCreateDTO,
    CourseStatusUpdateDTO,
    ReviewCreateDTO,
    ReviewModerationDTO,
)
from dealio.apps.courses.enums import ReviewStatusEnum
from dealio.apps.courses.models import Course, CourseReview
from dealio.apps.courses.repositories.logic import CourseLogicRepository
from dealio.apps.telegram_bot.dtos.commerce_bot_dtos import (
    TelegramCheckoutDTO,
    TelegramCourseCreateDTO,
    TelegramCourseLessonCreateDTO,
    TelegramCourseReviewDTO,
    TelegramCourseStatusDTO,
    TelegramPaginationDTO,
    TelegramPaymentReceiptDTO,
    TelegramPaymentReceiptReviewDTO,
    TelegramReviewModerationDTO,
)


class TelegramCommerceBotDjangoAdapter:
    """Django adapter for Telegram commerce actions.

    The Telegram service should not know query details. This adapter coordinates
    with the courses and billing domain logic while keeping bot controllers thin.
    """

    def __init__(self):
        self.course_logic = CourseLogicRepository()
        self.billing_logic = BillingLogicRepository()


    def list_admin_courses(self, dto: TelegramPaginationDTO):
        queryset = self.course_logic.list_courses_for_admin(filters={})
        courses = list(queryset[dto.offset:dto.offset + dto.page_size + 1])
        return courses[:dto.page_size], len(courses) > dto.page_size

    def get_admin_course(self, course_id_or_slug) -> Course:
        return self.course_logic.get_course_for_admin(course_id_or_slug)

    def create_course(self, admin_user, dto: TelegramCourseCreateDTO) -> Course:
        return self.course_logic.create_course(
            admin_user=admin_user,
            dto=CourseCreateDTO(
                title=dto.title,
                short_description=dto.short_description,
                description=dto.description,
                price=dto.price,
                currency=dto.currency,
                level=dto.level,
                duration_minutes=dto.duration_minutes,
                status=dto.status,
            ),
        )

    def update_course_status(self, admin_user, dto: TelegramCourseStatusDTO) -> Course:
        return self.course_logic.update_course_status(
            admin_user=admin_user,
            dto=CourseStatusUpdateDTO(course_id=dto.course_id, status=dto.status),
        )

    def create_lesson(self, admin_user, dto: TelegramCourseLessonCreateDTO):
        return self.course_logic.create_lesson(
            admin_user=admin_user,
            dto=CourseLessonCreateDTO(
                course_id=dto.course_id,
                title=dto.title,
                description=dto.description,
                content=dto.content,
                video_url=dto.video_url,
                duration_minutes=dto.duration_minutes,
                position=dto.position,
                is_preview=dto.is_preview,
            ),
        )

    @staticmethod
    def paginate_queryset(queryset: QuerySet, dto: TelegramPaginationDTO):
        items = list(queryset[dto.offset:dto.offset + dto.page_size + 1])
        total_count = queryset.count()
        return items[:dto.page_size], len(items) > dto.page_size, total_count

    def list_published_courses(self, dto: TelegramPaginationDTO) -> tuple[list[Course], bool]:
        queryset = self.course_logic.list_published_courses(filters={})
        courses = list(queryset[dto.offset:dto.offset + dto.page_size + 1])
        return courses[:dto.page_size], len(courses) > dto.page_size

    def get_published_course(self, course_id_or_slug) -> Course:
        return self.course_logic.get_published_course(course_id_or_slug)

    def list_course_reviews(self, course_id_or_slug, limit: int = 5) -> list[CourseReview]:
        queryset = self.course_logic.list_approved_reviews(course_id_or_slug)
        return list(queryset[:limit])

    def list_user_enrollments(self, user, limit: int = 10):
        queryset = self.course_logic.list_user_enrollments(user)
        return list(queryset[:limit])

    def submit_course_review(self, user, dto: TelegramCourseReviewDTO) -> CourseReview:
        return self.course_logic.submit_review(
            user=user,
            dto=ReviewCreateDTO(
                course_id=dto.course_id,
                rating=dto.rating,
                title=dto.title,
                comment=dto.comment,
            ),
        )

    def create_checkout_and_payment(self, user, dto: TelegramCheckoutDTO) -> tuple[Order, Payment | None, bool]:
        order, _ = self.billing_logic.create_checkout_order(user=user, dto=CheckoutDTO(course_id=dto.course_id))
        order.refresh_from_db()
        if order.status == OrderStatusEnum.PAID.value:
            return order, None, True

        provider = self.normalize_provider(dto.provider)
        payment = self.billing_logic.start_payment(
            user=user,
            dto=PaymentStartDTO(order_id=order.id, provider=provider),
        )

        if provider == PaymentProviderEnum.SANDBOX and self.sandbox_enabled():
            payment = self.billing_logic.confirm_payment(
                actor=user,
                dto=PaymentConfirmDTO(
                    payment_id=payment.id,
                    authority=payment.authority,
                    status=PaymentStatusEnum.SUCCEEDED.value,
                ),
            )
            order.refresh_from_db()
            return order, payment, True

        return order, payment, False

    def list_user_orders(self, user, limit: int = 10):
        queryset = self.billing_logic.list_user_orders(user)
        return list(queryset[:limit])

    def upload_payment_receipt(self, user, dto: TelegramPaymentReceiptDTO):
        return self.billing_logic.upload_receipt(
            user=user,
            dto=PaymentReceiptUploadDTO(
                payment_id=dto.payment_id,
                tracking_code=(dto.tracking_code or "").strip(),
                receipt_file_url=(dto.receipt_file_url or "").strip(),
                note=dto.note,
                source=PaymentReceiptSourceEnum.TELEGRAM,
            ),
        )

    def list_pending_payment_receipts(self, dto: TelegramPaginationDTO):
        queryset = self.billing_logic.list_receipts_for_admin(status=PaymentReceiptStatusEnum.PENDING.value)
        return self.paginate_queryset(queryset, dto)

    def review_payment_receipt(self, admin_user, dto: TelegramPaymentReceiptReviewDTO):
        return self.billing_logic.review_receipt(
            actor=admin_user,
            dto=PaymentReceiptReviewDTO(
                receipt_id=dto.receipt_id,
                approve=dto.approve,
                admin_note=dto.admin_note,
            ),
        )

    def list_pending_reviews(self, dto: TelegramPaginationDTO):
        queryset = self.course_logic.list_reviews_for_admin(status=ReviewStatusEnum.PENDING.value)
        return self.paginate_queryset(queryset, dto)

    def moderate_review(self, admin_user, dto: TelegramReviewModerationDTO) -> CourseReview:
        return self.course_logic.moderate_review(
            admin_user=admin_user,
            dto=ReviewModerationDTO(
                review_id=dto.review_id,
                status=ReviewStatusEnum(dto.status),
                admin_note=dto.admin_note,
            ),
        )

    @staticmethod
    def normalize_provider(provider: str):
        value = (provider or "").strip().lower()
        if value == PaymentProviderEnum.SANDBOX.value:
            return PaymentProviderEnum.SANDBOX
        if value == PaymentProviderEnum.PARDAKHTYAR.value:
            return PaymentProviderEnum.PARDAKHTYAR
        if value in {PaymentProviderEnum.CARD_TO_CARD.value, PaymentProviderEnum.MANUAL.value}:
            return PaymentProviderEnum.CARD_TO_CARD
        return PaymentProviderEnum.CARD_TO_CARD

    @staticmethod
    def sandbox_enabled() -> bool:
        value = os.environ.get("PAYMENT_SANDBOX_ENABLED")
        if value is None:
            raise RuntimeError("PAYMENT_SANDBOX_ENABLED is required.")
        return value.strip().lower() in {"1", "true", "yes"}
