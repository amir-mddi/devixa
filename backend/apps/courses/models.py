from decimal import Decimal
from uuid import uuid4


from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import get_valid_filename, slugify
from django.utils.timezone import now

from backend.apps.billing.enums import CurrencyEnum
from backend.apps.core_models.entities.base.base import BaseModel
from backend.apps.courses.adapters import get_private_course_storage
from backend.apps.courses.enums import (
    CourseLevelEnum,
    CourseStatusEnum,
    EnrollmentStatusEnum,
    ReviewStatusEnum,
    AssignmentStatusEnum,
    AssignmentSubmissionTypeEnum,
    AssignmentTypeEnum,
    CourseResourceTypeEnum,
    GradeCategoryEnum,
    QuestionStatusEnum,
    SubmissionStatusEnum,
)


class CourseCategory(BaseModel):
    title = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "title"]
        verbose_name = "Course category"
        verbose_name_plural = "Course categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Course(BaseModel):
    category = models.ForeignKey(
        CourseCategory,
        related_name="courses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="instructed_courses",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=300, blank=True, default="")
    description = models.TextField(blank=True, default="")
    thumbnail = models.ImageField(upload_to="courses/thumbnails/", null=True, blank=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(
        max_length=10,
        choices=CurrencyEnum.choices(),
        default=CurrencyEnum.IRR.value,
    )
    level = models.CharField(
        max_length=30,
        choices=CourseLevelEnum.choices(),
        default=CourseLevelEnum.ALL_LEVELS.value,
    )
    status = models.CharField(
        max_length=30,
        choices=CourseStatusEnum.choices(),
        default=CourseStatusEnum.DRAFT.value,
        db_index=True,
    )
    duration_minutes = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_active", "is_deleted"], name="course_public_idx"),
            models.Index(fields=["slug"], name="course_slug_idx"),
        ]

    @property
    def is_published(self) -> bool:
        return self.status == CourseStatusEnum.PUBLISHED.value and self.is_active and not self.is_deleted

    @property
    def is_free(self) -> bool:
        return self.price <= Decimal("0.00")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.status == CourseStatusEnum.PUBLISHED.value and not self.published_at:
            self.published_at = now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CourseLesson(BaseModel):
    course = models.ForeignKey(Course, related_name="lessons", on_delete=models.CASCADE)
    section = models.ForeignKey(
        "CourseSection",
        related_name="lessons",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    video_url = models.URLField(blank=True, default="")
    duration_minutes = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)
    release_at = models.DateTimeField(null=True, blank=True)
    require_completion = models.BooleanField(default=False)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["course", "slug"], name="unique_course_lesson_slug"),
            models.UniqueConstraint(fields=["course", "position"], name="unique_course_lesson_position"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseEnrollment(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_enrollments",
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(Course, related_name="enrollments", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=30,
        choices=EnrollmentStatusEnum.choices(),
        default=EnrollmentStatusEnum.ACTIVE.value,
        db_index=True,
    )
    enrolled_at = models.DateTimeField(default=now)
    source_order_number = models.CharField(max_length=60, blank=True, default="")

    class Meta:
        ordering = ["-enrolled_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_user_course_enrollment"),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="enrollment_user_status_idx"),
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.course_id}"


class CourseReview(BaseModel):
    course = models.ForeignKey(Course, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_reviews",
        on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=180, blank=True, default="")
    comment = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=ReviewStatusEnum.choices(),
        default=ReviewStatusEnum.PENDING.value,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="moderated_course_reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["course", "user"], name="unique_user_course_review"),
        ]
        indexes = [
            models.Index(fields=["course", "status"], name="review_course_status_idx"),
        ]

    @property
    def is_public(self) -> bool:
        return self.status == ReviewStatusEnum.APPROVED.value and self.is_active and not self.is_deleted

    def __str__(self):
        return f"{self.course_id} - {self.user_id} - {self.rating}"



def _private_course_file_path(prefix: str, instance, filename: str) -> str:
    safe_name = get_valid_filename(filename or "file")
    extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "bin"
    course_id = getattr(instance, "course_id", None)
    if not course_id and getattr(instance, "lesson_id", None):
        course_id = getattr(getattr(instance, "lesson", None), "course_id", "unknown")
    return f"courses/private/{course_id}/{prefix}/{uuid4().hex}.{extension}"


def course_resource_upload_to(instance, filename: str) -> str:
    return _private_course_file_path("resources", instance, filename)


def course_assignment_upload_to(instance, filename: str) -> str:
    return _private_course_file_path("assignments", instance, filename)


def course_submission_upload_to(instance, filename: str) -> str:
    assignment = getattr(instance, "assignment", None)
    instance.course_id = getattr(assignment, "course_id", "unknown")
    return _private_course_file_path("submissions", instance, filename)


class CourseSection(BaseModel):
    course = models.ForeignKey(Course, related_name="sections", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    release_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["course", "position"], name="unique_course_section_position"),
        ]
        indexes = [
            models.Index(fields=["course", "position"], name="course_section_order_idx"),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseResource(BaseModel):
    course = models.ForeignKey(Course, related_name="resources", on_delete=models.CASCADE)
    lesson = models.ForeignKey(
        CourseLesson,
        related_name="resources",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True, default="")
    resource_type = models.CharField(
        max_length=20,
        choices=CourseResourceTypeEnum.choices(),
        default=CourseResourceTypeEnum.FILE.value,
    )
    file = models.FileField(upload_to=course_resource_upload_to, storage=get_private_course_storage, null=True, blank=True)
    external_url = models.URLField(blank=True, default="")
    text_content = models.TextField(blank=True, default="")
    position = models.PositiveIntegerField(default=0)
    release_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["course", "lesson", "position"], name="course_resource_order_idx"),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseAssignment(BaseModel):
    course = models.ForeignKey(Course, related_name="assignments", on_delete=models.CASCADE)
    lesson = models.ForeignKey(
        CourseLesson,
        related_name="assignments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentTypeEnum.choices(),
        default=AssignmentTypeEnum.EXERCISE.value,
    )
    submission_type = models.CharField(
        max_length=20,
        choices=AssignmentSubmissionTypeEnum.choices(),
        default=AssignmentSubmissionTypeEnum.MIXED.value,
    )
    instructions = models.TextField(blank=True, default="")
    attachment = models.FileField(upload_to=course_assignment_upload_to, storage=get_private_course_storage, null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("100.00"))
    position = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatusEnum.choices(),
        default=AssignmentStatusEnum.DRAFT.value,
        db_index=True,
    )

    class Meta:
        ordering = ["position", "due_at", "created_at"]
        indexes = [
            models.Index(fields=["course", "status", "due_at"], name="course_assignment_due_idx"),
        ]

    @property
    def is_published(self) -> bool:
        return self.status == AssignmentStatusEnum.PUBLISHED.value and self.is_active and not self.is_deleted

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseSubmission(BaseModel):
    assignment = models.ForeignKey(CourseAssignment, related_name="submissions", on_delete=models.CASCADE)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_submissions",
        on_delete=models.CASCADE,
    )
    text_answer = models.TextField(blank=True, default="")
    file = models.FileField(upload_to=course_submission_upload_to, storage=get_private_course_storage, null=True, blank=True)
    link_url = models.URLField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatusEnum.choices(),
        default=SubmissionStatusEnum.SUBMITTED.value,
        db_index=True,
    )
    submitted_at = models.DateTimeField(default=now)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, default="")
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="graded_course_submissions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student"], name="unique_assignment_student_submission"),
        ]
        indexes = [
            models.Index(fields=["student", "status"], name="submission_student_status_idx"),
            models.Index(fields=["assignment", "status"], name="course_subm_asgn_status_idx"),
        ]

    def __str__(self):
        return f"{self.assignment_id} - {self.student_id}"


class CourseGradeItem(BaseModel):
    course = models.ForeignKey(Course, related_name="grade_items", on_delete=models.CASCADE)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_grade_items",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=180)
    category = models.CharField(
        max_length=20,
        choices=GradeCategoryEnum.choices(),
        default=GradeCategoryEnum.MANUAL.value,
    )
    score = models.DecimalField(max_digits=7, decimal_places=2)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("100.00"))
    note = models.TextField(blank=True, default="")
    is_published_to_student = models.BooleanField(default=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["course", "student", "is_published_to_student"], name="course_grade_student_idx"),
        ]

    def __str__(self):
        return f"{self.course_id} - {self.student_id} - {self.title}"


class CourseLessonProgress(BaseModel):
    lesson = models.ForeignKey(CourseLesson, related_name="progress_records", on_delete=models.CASCADE)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_lesson_progress",
        on_delete=models.CASCADE,
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["lesson", "student"], name="unique_lesson_student_progress"),
        ]
        indexes = [
            models.Index(fields=["student", "lesson"], name="lesson_progress_student_idx"),
        ]

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    def __str__(self):
        return f"{self.lesson_id} - {self.student_id}"


class CourseAnnouncement(BaseModel):
    course = models.ForeignKey(Course, related_name="announcements", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_announcements",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=180)
    message = models.TextField()
    published_at = models.DateTimeField(default=now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_pinned", "-published_at"]
        indexes = [
            models.Index(fields=["course", "published_at"], name="course_announcement_pub_idx"),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseQuestion(BaseModel):
    course = models.ForeignKey(Course, related_name="questions", on_delete=models.CASCADE)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_questions",
        on_delete=models.CASCADE,
    )
    subject = models.CharField(max_length=180)
    status = models.CharField(
        max_length=20,
        choices=QuestionStatusEnum.choices(),
        default=QuestionStatusEnum.OPEN.value,
        db_index=True,
    )
    last_message_at = models.DateTimeField(default=now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(fields=["course", "status", "last_message_at"], name="course_question_state_idx"),
            models.Index(fields=["student", "last_message_at"], name="course_question_student_idx"),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.subject}"


class CourseQuestionMessage(BaseModel):
    question = models.ForeignKey(CourseQuestion, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="course_question_messages",
        on_delete=models.CASCADE,
    )
    body = models.TextField()
    attachment = models.FileField(upload_to=course_resource_upload_to, storage=get_private_course_storage, null=True, blank=True)
    sent_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ["sent_at", "created_at"]
        indexes = [
            models.Index(fields=["question", "sent_at"], name="question_message_time_idx"),
        ]

    @property
    def course_id(self):
        return self.question.course_id

    def __str__(self):
        return f"{self.question_id} - {self.sender_id}"
