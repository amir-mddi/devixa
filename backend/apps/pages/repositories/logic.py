from __future__ import annotations

from backend.apps.common.utils.common_utils import CommonUtils

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from backend.apps.common.project_config import get_project_public_config
from backend.apps.common.email_service import send_html_email_async
from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.pages.dtos.contact_dto import ContactMessageDTO, PageActionResultDTO
from backend.apps.pages.dtos.home_content_dto import (
    ChannelLinkDTO,
    HomeFaqDTO,
    HomeTestimonialDTO,
)
from backend.apps.telegram_bot.repositories.logic.bot_support_logic import (
    BotSupportLogicRepository,
)
from backend.apps.pages.vo.page_vo import (
    PageEmailContextKeyVO,
    PageEmailSubjectVO,
    PageEmailTemplateVO,
    PageErrorCodeVO,
    PageSettingNameVO,
    PageHomeTestimonialVO,
    PageHomeFaqVO,
    PageChannelLinkVO,
)

logger = CommonUtils.get_project_logger(__name__)


class PageLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.bot_support_logic = BotSupportLogicRepository()

    def list_home_testimonials(self) -> tuple[HomeTestimonialDTO, ...]:
        project_name = get_project_public_config().display_name
        return (
            HomeTestimonialDTO(
                comment=PageHomeTestimonialVO.BACKEND_COMMENT.format(project_name=project_name),
                student_name=PageHomeTestimonialVO.BACKEND_NAME,
                student_role=PageHomeTestimonialVO.BACKEND_ROLE,
            ),
            HomeTestimonialDTO(
                comment=PageHomeTestimonialVO.FRONTEND_COMMENT,
                student_name=PageHomeTestimonialVO.FRONTEND_NAME,
                student_role=PageHomeTestimonialVO.FRONTEND_ROLE,
            ),
            HomeTestimonialDTO(
                comment=PageHomeTestimonialVO.FULLSTACK_COMMENT,
                student_name=PageHomeTestimonialVO.FULLSTACK_NAME,
                student_role=PageHomeTestimonialVO.FULLSTACK_ROLE,
            ),
            HomeTestimonialDTO(
                comment=PageHomeTestimonialVO.FREELANCE_COMMENT,
                student_name=PageHomeTestimonialVO.FREELANCE_NAME,
                student_role=PageHomeTestimonialVO.FREELANCE_ROLE,
            ),
        )

    def list_home_frequently_asked_questions(
        self, limit: int = 6
    ) -> tuple[HomeFaqDTO, ...]:
        try:
            tickets = self.bot_support_logic.list_frequently_asked_tickets(limit=limit)
        except (OperationalError, ProgrammingError):
            tickets = ()

        faq_items = tuple(
            self._faq_from_ticket(ticket)
            for ticket in tickets
            if self._ticket_has_public_faq(ticket)
        )
        return faq_items or self._default_faq_items()[:limit]

    def list_channel_links(self) -> tuple[ChannelLinkDTO, ...]:
        project_config = get_project_public_config()
        return (
            ChannelLinkDTO(
                title=PageChannelLinkVO.TELEGRAM_TITLE,
                description=PageChannelLinkVO.TELEGRAM_DESCRIPTION,
                url=project_config.telegram_bot_url or project_config.telegram_url,
                icon_class=PageChannelLinkVO.TELEGRAM_ICON,
                badge=PageChannelLinkVO.TELEGRAM_BADGE,
            ),
            ChannelLinkDTO(
                title=PageChannelLinkVO.BALE_TITLE,
                description=PageChannelLinkVO.BALE_DESCRIPTION,
                url=project_config.bale_bot_url,
                icon_class=PageChannelLinkVO.BALE_ICON,
                badge=PageChannelLinkVO.BALE_BADGE,
            ),
            ChannelLinkDTO(
                title=PageChannelLinkVO.RUBIKA_TITLE,
                description=PageChannelLinkVO.RUBIKA_DESCRIPTION,
                url=project_config.rubika_bot_url,
                icon_class=PageChannelLinkVO.RUBIKA_ICON,
                badge=PageChannelLinkVO.RUBIKA_BADGE,
            ),
        )

    @staticmethod
    def _ticket_has_public_faq(ticket) -> bool:
        return bool(
            (ticket.faq_question or ticket.subject or "").strip()
            and (ticket.faq_answer or "").strip()
        )

    @staticmethod
    def _faq_from_ticket(ticket) -> HomeFaqDTO:
        return HomeFaqDTO(
            question=(ticket.faq_question or ticket.subject or "").strip(),
            answer=(ticket.faq_answer or "").strip(),
        )

    @staticmethod
    def _default_faq_items() -> tuple[HomeFaqDTO, ...]:
        return tuple(
            HomeFaqDTO(question=question, answer=answer)
            for question, answer in PageHomeFaqVO.DEFAULT_ITEMS
        )

    def send_contact_message(self, dto: ContactMessageDTO) -> PageActionResultDTO:
        recipient_email = self._contact_recipient_email()
        if not recipient_email:
            return PageActionResultDTO.failed(
                error_code=PageErrorCodeVO.EMAIL_NOT_CONFIGURED
            )

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
        return project_config.business_email or getattr(
            settings, PageSettingNameVO.DEFAULT_FROM_EMAIL.value, ""
        )
