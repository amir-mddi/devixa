from dataclasses import dataclass
from decimal import Decimal
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
    discount_code: str = ""


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
class TelegramCourseUpdateFieldDTO:
    course_id: UUID
    field: str
    value: object


@dataclass(frozen=True)
class TelegramCourseDeleteDTO:
    course_id: UUID


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


@dataclass(frozen=True)
class TelegramPaymentReceiptDTO:
    payment_id: UUID
    tracking_code: str = ""
    receipt_file: object | None = None
    receipt_file_url: str = ""
    note: str = ""


@dataclass(frozen=True)
class BotDownloadedFileDTO:
    content: bytes
    filename: str
    content_type: str


@dataclass(frozen=True)
class TelegramPaymentReceiptReviewDTO:
    receipt_id: UUID
    approve: bool
    admin_note: str = ""


@dataclass(frozen=True)
class TelegramDiscountCreateDTO:
    code: str
    discount_type: str
    value: Decimal
    title: str = ""
    course_id: UUID | None = None
    usage_limit: int | None = None


@dataclass(frozen=True)
class TelegramDiscountDeleteDTO:
    discount_id: UUID
