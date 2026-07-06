from __future__ import annotations

from dealio.apps.common.utils.common_utils import CommonUtils

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from dealio.apps.common.project_config import get_project_public_config
from dealio.apps.common.email_service import send_html_email_async
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.pages.dtos.contact_dto import ContactMessageDTO, PageActionResultDTO
from dealio.apps.pages.dtos.home_content_dto import ChannelLinkDTO, HomeFaqDTO, HomeTestimonialDTO
from dealio.apps.telegram_bot.repositories.logic.bot_support_logic import BotSupportLogicRepository
from dealio.apps.pages.vo.page_vo import (
    PageEmailContextKeyVO,
    PageEmailSubjectVO,
    PageEmailTemplateVO,
    PageErrorCodeVO,
    PageSettingNameVO,
)

logger = CommonUtils.get_project_logger(__name__)


class PageLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.bot_support_logic = BotSupportLogicRepository()

    def list_home_testimonials(self) -> tuple[HomeTestimonialDTO, ...]:
        project_name = get_project_public_config().display_name
        return (
            HomeTestimonialDTO(
                comment=f"با دوره‌های {project_name} توانستم اولین پروژه واقعی خودم را کامل کنم و برای مصاحبه فنی آماده شوم.",
                student_name="علی محمدی",
                student_role="Backend Developer",
            ),
            HomeTestimonialDTO(
                comment="مسیر پروژه‌محور باعث شد به جای حفظ کردن، واقعا تجربه ساخت محصول داشته باشم.",
                student_name="سارا احمدی",
                student_role="Frontend Developer",
            ),
            HomeTestimonialDTO(
                comment="پشتیبانی و بازخورد روی تمرین‌ها کمک کرد سریع‌تر اشکال‌های کدم را پیدا کنم.",
                student_name="رضا کریمی",
                student_role="Fullstack Developer",
            ),
            HomeTestimonialDTO(
                comment="بعد از دوره، نمونه‌کار قابل ارائه داشتم و راحت‌تر برای پروژه‌های فریلنسری مذاکره کردم.",
                student_name="مریم رضایی",
                student_role="Freelance Developer",
            ),
        )

    def list_home_frequently_asked_questions(self, limit: int = 6) -> tuple[HomeFaqDTO, ...]:
        try:
            tickets = self.bot_support_logic.list_frequently_asked_tickets(limit=limit)
        except (OperationalError, ProgrammingError):
            tickets = ()

        faq_items = tuple(self._faq_from_ticket(ticket) for ticket in tickets if self._ticket_has_public_faq(ticket))
        return faq_items or self._default_faq_items()[:limit]

    def list_channel_links(self) -> tuple[ChannelLinkDTO, ...]:
        project_config = get_project_public_config()
        return (
            ChannelLinkDTO(
                title="ربات تلگرام",
                description="ثبت‌نام، خرید دوره و پیگیری سفارش از طریق تلگرام",
                url=project_config.telegram_bot_url or project_config.telegram_url,
                icon_class="fa-brands fa-telegram",
                badge="Telegram",
            ),
            ChannelLinkDTO(
                title="ربات بله",
                description="ثبت‌نام و خرید دوره برای کاربرانی که از بله استفاده می‌کنند",
                url=project_config.bale_bot_url,
                icon_class="fa-solid fa-comments",
                badge="Bale",
            ),
        )

    @staticmethod
    def _ticket_has_public_faq(ticket) -> bool:
        return bool((ticket.faq_question or ticket.subject or "").strip() and (ticket.faq_answer or "").strip())

    @staticmethod
    def _faq_from_ticket(ticket) -> HomeFaqDTO:
        return HomeFaqDTO(
            question=(ticket.faq_question or ticket.subject or "").strip(),
            answer=(ticket.faq_answer or "").strip(),
        )

    @staticmethod
    def _default_faq_items() -> tuple[HomeFaqDTO, ...]:
        return (
            HomeFaqDTO("آیا دوره‌ها پیش‌نیاز دارند؟", "بیشتر دوره‌های مقدماتی بدون نیاز به پیش‌نیاز طراحی شده‌اند. اگر دوره‌ای پیش‌نیاز داشته باشد، در صفحه همان دوره کامل نوشته می‌شود."),
            HomeFaqDTO("آیا در طول دوره پروژه عملی انجام می‌دهیم؟", "بله، تمرکز اصلی دوره‌ها روی پروژه واقعی است تا در پایان مسیر نمونه‌کار قابل ارائه داشته باشید."),
            HomeFaqDTO("پشتیبانی دوره‌ها چگونه است؟", "سوالات از طریق کانال‌های پشتیبانی، ربات‌ها و تیکت‌ها بررسی می‌شود تا در مسیر یادگیری تنها نمانید."),
            HomeFaqDTO("آیا گواهی پایان دوره دریافت می‌کنیم؟", "پس از تکمیل دوره و انجام تمرین‌های اصلی، گواهی پایان دوره برای شما قابل صدور است."),
            HomeFaqDTO("آیا بوت‌کمپ برای افراد مبتدی مناسب است؟", "بله، مسیر از مباحث پایه شروع می‌شود و مرحله به مرحله تا سطح پروژه واقعی و ورود به بازار کار جلو می‌رود."),
            HomeFaqDTO("بعد از پایان دوره چه مسیری پیشنهاد می‌کنید؟", "تکمیل نمونه‌کار، انجام پروژه واقعی، فعالیت فریلنسری و ادامه مسیر از طریق نقشه‌راه‌های تخصصی پیشنهاد می‌شود."),
        )

    def send_contact_message(self, dto: ContactMessageDTO) -> PageActionResultDTO:
        recipient_email = self._contact_recipient_email()
        if not recipient_email:
            return PageActionResultDTO.failed(error_code=PageErrorCodeVO.EMAIL_NOT_CONFIGURED)

        try:
            send_html_email_async(
                subject=PageEmailSubjectVO.CONTACT_MESSAGE.value,
                template_name=PageEmailTemplateVO.CONTACT_MESSAGE.value,
                context={
                    PageEmailContextKeyVO.APP_NAME.value: get_project_public_config().display_name,
                    PageEmailContextKeyVO.FULL_NAME.value: dto.full_name,
                    PageEmailContextKeyVO.EMAIL.value: dto.email,
                    PageEmailContextKeyVO.TOPIC.value: dto.topic,
                    PageEmailContextKeyVO.MESSAGE.value: dto.message,
                },
                recipient_list=[recipient_email],
            )
        except Exception as exc:
            logger.exception("Failed to queue contact message email: %s", exc)
            return PageActionResultDTO.failed(error_code=PageErrorCodeVO.MESSAGE_FAILED)

        return PageActionResultDTO.success()

    @staticmethod
    def _contact_recipient_email() -> str:
        project_config = get_project_public_config()
        return project_config.contact_email or getattr(settings, PageSettingNameVO.DEFAULT_FROM_EMAIL.value, "")
