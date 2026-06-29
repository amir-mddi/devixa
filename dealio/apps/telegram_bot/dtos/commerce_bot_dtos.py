from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TelegramPaginationDTO:
    page: int = 1
    page_size: int = 5

    @property
    def offset(self) -> int:
        return max(self.page - 1, 0) * self.page_size


@dataclass(frozen=True)
class TelegramCourseReviewDTO:
    course_id: UUID
    rating: int
    title: str
    comment: str


@dataclass(frozen=True)
class TelegramCheckoutDTO:
    course_id: UUID
    provider: str


@dataclass(frozen=True)
class TelegramReviewModerationDTO:
    review_id: UUID
    status: str
    admin_note: str = ""


@dataclass(frozen=True)
class TelegramCourseCreateDTO:
    title: str
    short_description: str
    description: str
    price: float
    currency: str
    level: str
    duration_minutes: int
    status: str = "draft"


@dataclass(frozen=True)
class TelegramCourseStatusDTO:
    course_id: UUID
    status: str


@dataclass(frozen=True)
class TelegramCourseLessonCreateDTO:
    course_id: UUID
    title: str
    description: str
    content: str
    video_url: str
    duration_minutes: int
    position: int | None
    is_preview: bool
