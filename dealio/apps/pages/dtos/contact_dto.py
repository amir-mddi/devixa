from __future__ import annotations

from dataclasses import dataclass

from dealio.apps.pages.vo.page_vo import PageErrorCodeVO


@dataclass(frozen=True, slots=True)
class ContactMessageDTO:
    full_name: str
    email: str
    topic: str
    message: str


@dataclass(frozen=True, slots=True)
class PageActionResultDTO:
    is_success: bool
    error_code: PageErrorCodeVO | None = None

    @classmethod
    def success(cls) -> "PageActionResultDTO":
        return cls(is_success=True)

    @classmethod
    def failed(cls, *, error_code: PageErrorCodeVO) -> "PageActionResultDTO":
        return cls(is_success=False, error_code=error_code)
