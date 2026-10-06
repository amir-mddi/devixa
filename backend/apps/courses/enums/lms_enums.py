from backend.apps.core_models.enum.base import BaseEnum


class CourseResourceTypeEnum(BaseEnum):
    FILE = "file"
    LINK = "link"
    NOTE = "note"


class AssignmentTypeEnum(BaseEnum):
    EXERCISE = "exercise"
    PROJECT = "project"
    QUIZ = "quiz"
    OTHER = "other"


class AssignmentSubmissionTypeEnum(BaseEnum):
    FILE = "file"
    TEXT = "text"
    LINK = "link"
    MIXED = "mixed"


class AssignmentStatusEnum(BaseEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatusEnum(BaseEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    RETURNED = "returned"


class GradeCategoryEnum(BaseEnum):
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    QUIZ = "quiz"
    EXAM = "exam"
    PARTICIPATION = "participation"
    MANUAL = "manual"


class QuestionStatusEnum(BaseEnum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"


class LessonProgressStatusEnum(BaseEnum):
    NOT_STARTED = "not_started"
    COMPLETED = "completed"
