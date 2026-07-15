from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now

from backend.apps.billing.enums import CurrencyEnum
from backend.apps.core_models.entities.base.base import BaseModel
from backend.apps.courses.enums import (
    CourseLevelEnum,
    CourseStatusEnum,
    EnrollmentStatusEnum,
    ReviewStatusEnum,
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
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    video_url = models.URLField(blank=True, default="")
    duration_minutes = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)

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
