from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from backend.apps.core_models.dtos.base_dto import BaseDTO


class CourseInstructorUpdateDTO(BaseDTO):
    course_id: UUID
    title: str
    short_description: str = ""
    description: str = ""
    level: str = "all_levels"
    duration_minutes: int = 0


class CourseSectionCreateDTO(BaseDTO):
    course_id: UUID
    title: str
    description: str = ""
    position: int | None = None
    release_at: datetime | None = None


class CourseLessonManageDTO(BaseDTO):
    course_id: UUID
    lesson_id: UUID | None = None
    section_id: UUID | None = None
    title: str
    description: str = ""
    content: str = ""
    video_url: str = ""
    duration_minutes: int = 0
    position: int | None = None
    is_preview: bool = False
    release_at: datetime | None = None
    require_completion: bool = False


class CourseResourceCreateDTO(BaseDTO):
    course_id: UUID
    lesson_id: UUID | None = None
    title: str
    description: str = ""
    resource_type: str = "file"
    file: object | None = None
    external_url: str = ""
    text_content: str = ""
    position: int | None = None
    release_at: datetime | None = None


class CourseAssignmentCreateDTO(BaseDTO):
    course_id: UUID
    lesson_id: UUID | None = None
    title: str
    assignment_type: str = "exercise"
    submission_type: str = "mixed"
    instructions: str = ""
    attachment: object | None = None
    starts_at: datetime | None = None
    due_at: datetime | None = None
    allow_late_submission: bool = False
    max_score: Decimal = Decimal("100.00")
    position: int | None = None
    status: str = "published"


class CourseSubmissionDTO(BaseDTO):
    assignment_id: UUID
    text_answer: str = ""
    file: object | None = None
    link_url: str = ""


class CourseSubmissionGradeDTO(BaseDTO):
    submission_id: UUID
    score: Decimal
    feedback: str = ""


class CourseGradeItemDTO(BaseDTO):
    course_id: UUID
    student_id: UUID
    title: str
    category: str = "manual"
    score: Decimal
    max_score: Decimal = Decimal("100.00")
    note: str = ""
    is_published_to_student: bool = True


class CourseQuestionCreateDTO(BaseDTO):
    course_id: UUID
    subject: str
    body: str
    attachment: object | None = None


class CourseQuestionReplyDTO(BaseDTO):
    question_id: UUID
    body: str
    attachment: object | None = None


class CourseAnnouncementCreateDTO(BaseDTO):
    course_id: UUID
    title: str
    message: str
    expires_at: datetime | None = None
    is_pinned: bool = False


class CourseProgressToggleDTO(BaseDTO):
    lesson_id: UUID
    completed: bool = True
