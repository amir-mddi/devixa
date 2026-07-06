from __future__ import annotations

from dealio.apps.pages.vo.page_vo import PageErrorCodeVO, PageWebValidationMessageVO


class PageWebErrorPresenter:
    _messages = {
        PageErrorCodeVO.EMAIL_NOT_CONFIGURED: PageWebValidationMessageVO.CONTACT_EMAIL_NOT_CONFIGURED.value,
        PageErrorCodeVO.MESSAGE_FAILED: PageWebValidationMessageVO.CONTACT_MESSAGE_FAILED.value,
    }

    @classmethod
    def message_for(cls, error_code: PageErrorCodeVO | None) -> str:
        return cls._messages.get(error_code, PageWebValidationMessageVO.CONTACT_MESSAGE_FAILED.value)
