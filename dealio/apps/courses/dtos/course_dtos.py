from uuid import UUID

from dealio.apps.core_models.dtos.base_dto import BaseDTO
from dealio.apps.courses.enums import ReviewStatusEnum


class ReviewCreateDTO(BaseDTO):
    course_id: UUID
    rating: int
    title: str = ""
    comment: str


class ReviewModerationDTO(BaseDTO):
    review_id: UUID
    status: ReviewStatusEnum
    admin_note: str = ""


class CourseCreateDTO(BaseDTO):
    title: str
    short_description: str = ""
    description: str = ""
    price: float = 0
    currency: str = "irr"
    level: str = "all_levels"
    duration_minutes: int = 0
    category_id: UUID | None = None
    status: str = "draft"
    is_featured: bool = False


class CourseUpdateDTO(BaseDTO):
    course_id: UUID
    title: str | None = None
    short_description: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    level: str | None = None
    duration_minutes: int | None = None
    category_id: UUID | None = None
    is_featured: bool | None = None


class CourseStatusUpdateDTO(BaseDTO):
    course_id: UUID
    status: str


class CourseLessonCreateDTO(BaseDTO):
    course_id: UUID
    title: str
    description: str = ""
    content: str = ""
    video_url: str = ""
    duration_minutes: int = 0
    position: int | None = None
    is_preview: bool = False
