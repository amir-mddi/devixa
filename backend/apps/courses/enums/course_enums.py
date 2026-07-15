from backend.apps.core_models.enum.base import BaseEnum


class CourseStatusEnum(BaseEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseLevelEnum(BaseEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ALL_LEVELS = "all_levels"


class ReviewStatusEnum(BaseEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EnrollmentStatusEnum(BaseEnum):
    ACTIVE = "active"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
