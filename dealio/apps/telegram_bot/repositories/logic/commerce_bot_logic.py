from __future__ import annotations

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.telegram_bot.enums.bot_setting_enums import BotSettingProviderEnum
from dealio.apps.telegram_bot.repositories.logic.bot_setting_logic import BotRuntimeConfigProvider
from dealio.apps.telegram_bot.dtos.commerce_bot_dtos import (
    TelegramCheckoutDTO,
    TelegramCourseCreateDTO,
    TelegramCourseDeleteDTO,
    TelegramCourseLessonCreateDTO,
    TelegramCourseReviewDTO,
    TelegramCourseStatusDTO,
    TelegramCourseUpdateFieldDTO,
    TelegramDiscountCreateDTO,
    TelegramDiscountDeleteDTO,
    TelegramPaginationDTO,
    TelegramPaymentReceiptDTO,
    TelegramPaymentReceiptReviewDTO,
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

    def update_course_field(self, admin_user, *, course_id, field: str, value):
        return self.adapter.update_course_field(
            admin_user=admin_user,
            dto=TelegramCourseUpdateFieldDTO(course_id=course_id, field=field, value=value),
        )

    def delete_course(self, admin_user, *, course_id):
        return self.adapter.delete_course(
            admin_user=admin_user,
            dto=TelegramCourseDeleteDTO(course_id=course_id),
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

    def checkout_course(self, user, *, course_id, discount_code: str = ""):
        return self.adapter.create_checkout_and_payment(
            user=user,
            dto=TelegramCheckoutDTO(course_id=course_id, provider=self.default_payment_provider(), discount_code=discount_code),
        )

    def list_orders(self, user, limit: int = 10):
        return self.adapter.list_user_orders(user, limit=limit)

    def upload_payment_receipt(self, user, *, payment_id, tracking_code: str = "", receipt_file_url: str = "", note: str = ""):
        return self.adapter.upload_payment_receipt(
            user=user,
            dto=TelegramPaymentReceiptDTO(
                payment_id=payment_id,
                tracking_code=tracking_code,
                receipt_file_url=receipt_file_url,
                note=note,
            ),
        )

    def list_pending_payment_receipts(self, page: int = 1, page_size: int = 10):
        return self.adapter.list_pending_payment_receipts(TelegramPaginationDTO(page=page, page_size=page_size))

    def review_payment_receipt(self, admin_user, *, receipt_id, approve: bool, admin_note: str = ""):
        return self.adapter.review_payment_receipt(
            admin_user=admin_user,
            dto=TelegramPaymentReceiptReviewDTO(receipt_id=receipt_id, approve=approve, admin_note=admin_note),
        )

    def list_pending_reviews(self, page: int = 1, page_size: int = 10):
        return self.adapter.list_pending_reviews(TelegramPaginationDTO(page=page, page_size=page_size))

    def moderate_review(self, admin_user, *, review_id, status: str, admin_note: str = ""):
        return self.adapter.moderate_review(
            admin_user=admin_user,
            dto=TelegramReviewModerationDTO(review_id=review_id, status=status, admin_note=admin_note),
        )


    def list_discount_codes(self, page: int = 1, page_size: int = 10):
        return self.adapter.list_discount_codes(page=page, page_size=page_size)

    def create_discount_code(self, admin_user, *, code: str, discount_type: str, value, title: str = "", course_id=None, usage_limit: int | None = None):
        return self.adapter.create_discount_code(
            admin_user=admin_user,
            dto=TelegramDiscountCreateDTO(
                code=code,
                discount_type=discount_type,
                value=value,
                title=title,
                course_id=course_id,
                usage_limit=usage_limit,
            ),
        )

    def delete_discount_code(self, admin_user, *, discount_id):
        return self.adapter.delete_discount_code(
            admin_user=admin_user,
            dto=TelegramDiscountDeleteDTO(discount_id=discount_id),
        )

    @staticmethod
    def default_payment_provider() -> str:
        provider = BotRuntimeConfigProvider.get(BotSettingProviderEnum.TELEGRAM.value, "payment_provider")
        if not provider:
            raise RuntimeError("TELEGRAM_PAYMENT_PROVIDER is required.")
        return provider
