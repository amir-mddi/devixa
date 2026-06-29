from __future__ import annotations

import os

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.telegram_bot.dtos.commerce_bot_dtos import (
    TelegramCheckoutDTO,
    TelegramCourseCreateDTO,
    TelegramCourseLessonCreateDTO,
    TelegramCourseReviewDTO,
    TelegramCourseStatusDTO,
    TelegramPaginationDTO,
    TelegramReviewModerationDTO,
)
from dealio.apps.telegram_bot.repositories.adapters.commerce_bot_adapter import TelegramCommerceBotDjangoAdapter


class TelegramCommerceBotLogicRepository(metaclass=Singleton):
    """Application logic for course commerce inside Telegram."""

    def __init__(self):
        self.adapter = TelegramCommerceBotDjangoAdapter()


    def list_admin_courses(self, page: int = 1, page_size: int = 5):
        return self.adapter.list_admin_courses(TelegramPaginationDTO(page=page, page_size=page_size))

    def get_admin_course(self, course_id_or_slug):
        return self.adapter.get_admin_course(course_id_or_slug)

    def create_course(self, admin_user, *, title: str, short_description: str, description: str, price: float, currency: str, level: str, duration_minutes: int, status: str = "draft"):
        return self.adapter.create_course(
            admin_user=admin_user,
            dto=TelegramCourseCreateDTO(
                title=title,
                short_description=short_description,
                description=description,
                price=price,
                currency=currency,
                level=level,
                duration_minutes=duration_minutes,
                status=status,
            ),
        )

    def update_course_status(self, admin_user, *, course_id, status: str):
        return self.adapter.update_course_status(
            admin_user=admin_user,
            dto=TelegramCourseStatusDTO(course_id=course_id, status=status),
        )

    def create_lesson(self, admin_user, *, course_id, title: str, description: str, content: str, video_url: str, duration_minutes: int, position: int | None, is_preview: bool):
        return self.adapter.create_lesson(
            admin_user=admin_user,
            dto=TelegramCourseLessonCreateDTO(
                course_id=course_id,
                title=title,
                description=description,
                content=content,
                video_url=video_url,
                duration_minutes=duration_minutes,
                position=position,
                is_preview=is_preview,
            ),
        )

    def list_courses(self, page: int = 1, page_size: int = 5):
        return self.adapter.list_published_courses(TelegramPaginationDTO(page=page, page_size=page_size))

    def get_course(self, course_id_or_slug):
        return self.adapter.get_published_course(course_id_or_slug)

    def list_reviews(self, course_id_or_slug, limit: int = 5):
        return self.adapter.list_course_reviews(course_id_or_slug, limit=limit)

    def list_enrollments(self, user, limit: int = 10):
        return self.adapter.list_user_enrollments(user, limit=limit)

    def submit_review(self, user, *, course_id, rating: int, title: str, comment: str):
        return self.adapter.submit_course_review(
            user=user,
            dto=TelegramCourseReviewDTO(
                course_id=course_id,
                rating=rating,
                title=title,
                comment=comment,
            ),
        )

    def checkout_course(self, user, *, course_id):
        return self.adapter.create_checkout_and_payment(
            user=user,
            dto=TelegramCheckoutDTO(course_id=course_id, provider=self.default_payment_provider()),
        )

    def list_orders(self, user, limit: int = 10):
        return self.adapter.list_user_orders(user, limit=limit)

    def list_pending_reviews(self, limit: int = 10):
        return self.adapter.list_pending_reviews(limit=limit)

    def moderate_review(self, admin_user, *, review_id, status: str, admin_note: str = ""):
        return self.adapter.moderate_review(
            admin_user=admin_user,
            dto=TelegramReviewModerationDTO(review_id=review_id, status=status, admin_note=admin_note),
        )

    @staticmethod
    def default_payment_provider() -> str:
        return os.environ.get("TELEGRAM_PAYMENT_PROVIDER", os.environ.get("PAYMENT_DEFAULT_PROVIDER", "manual"))
