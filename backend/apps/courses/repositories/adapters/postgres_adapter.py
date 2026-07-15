from decimal import Decimal
from uuid import UUID

from django.db.models import Avg, Count, Q
from django.utils.timezone import now
from django.utils.text import slugify
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.courses.enums import CourseStatusEnum, EnrollmentStatusEnum, ReviewStatusEnum
from backend.apps.courses.models import Course, CourseCategory, CourseEnrollment, CourseLesson, CourseReview
from backend.apps.courses.vo import CourseMessagesVO
from backend.apps.courses.vo.roadmap_vo import CourseQueryParamVO, CourseWebCategoryFilterVO, CourseWebLevelFilterVO


class CoursePostgresAdapter(metaclass=Singleton):

    @staticmethod
    def unique_slug_for_model(model_class, base_value: str, *, instance_id=None, max_length: int = 200) -> str:
        base_slug = slugify(base_value or "course")[:max_length].strip("-") or "course"
        slug = base_slug
        counter = 2
        queryset = model_class.objects.all()
        if instance_id:
            queryset = queryset.exclude(id=instance_id)
        while queryset.filter(slug=slug).exists():
            suffix = f"-{counter}"
            slug = f"{base_slug[:max_length - len(suffix)]}{suffix}"
            counter += 1
        return slug

    @staticmethod
    def list_courses_for_admin(filters: dict):
        queryset = (
            Course.objects.select_related("category", "instructor")
            .filter(is_deleted=False)
            .order_by("-created_at")
        )
        status = filters.get("status") if filters else None
        search = filters.get("search") if filters else None
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
            )
        return queryset

    @staticmethod
    def get_course_for_admin(course_id_or_slug):
        queryset = Course.objects.select_related("category", "instructor").prefetch_related("lessons").filter(is_deleted=False)
        lookup = str(course_id_or_slug)
        try:
            UUID(lookup)
            query = Q(id=lookup)
        except (TypeError, ValueError):
            query = Q(slug=lookup)
        course = queryset.filter(query).first()
        if not course:
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        return course

    def create_course(self, admin_user, dto):
        if dto.status not in {CourseStatusEnum.DRAFT.value, CourseStatusEnum.PUBLISHED.value, CourseStatusEnum.ARCHIVED.value}:
            raise ValidationError("Invalid course status.")
        if dto.level not in {"beginner", "intermediate", "advanced", "all_levels"}:
            raise ValidationError("Invalid course level.")
        if Decimal(str(dto.price)) < Decimal("0"):
            raise ValidationError("Course price can not be negative.")
        category = None
        if dto.category_id:
            category = CourseCategory.objects.filter(id=dto.category_id, is_deleted=False).first()
            if not category:
                raise NotFound("Course category not found.")
        course = Course.objects.create(
            category=category,
            instructor=admin_user,
            title=dto.title.strip(),
            slug=self.unique_slug_for_model(Course, dto.title, max_length=200),
            short_description=(dto.short_description or "").strip(),
            description=(dto.description or "").strip(),
            price=Decimal(str(dto.price)),
            currency=(dto.currency or "irr").lower(),
            level=dto.level,
            status=dto.status,
            duration_minutes=max(int(dto.duration_minutes or 0), 0),
            is_featured=bool(dto.is_featured),
            user_created_object=admin_user,
            user_updated_object=admin_user,
        )
        return course

    def update_course(self, admin_user, dto):
        course = self.get_course_for_admin(dto.course_id)
        updates = {}
        for field in [
            "title",
            "short_description",
            "description",
            "currency",
            "level",
            "duration_minutes",
            "is_featured",
        ]:
            value = getattr(dto, field, None)
            if value is not None:
                updates[field] = value
        if dto.price is not None:
            if Decimal(str(dto.price)) < Decimal("0"):
                raise ValidationError("Course price can not be negative.")
            updates["price"] = Decimal(str(dto.price))
        if "category_id" in getattr(dto, "model_fields_set", set()):
            category = None
            if dto.category_id is not None:
                category = CourseCategory.objects.filter(id=dto.category_id, is_deleted=False).first()
                if not category:
                    raise NotFound("Course category not found.")
            updates["category"] = category
        if "title" in updates and updates["title"] != course.title:
            updates["slug"] = self.unique_slug_for_model(Course, updates["title"], instance_id=course.id, max_length=200)
        for field, value in updates.items():
            setattr(course, field, value)
        course.user_updated_object = admin_user
        course.save()
        return course

    def update_course_status(self, admin_user, course_id, status: str):
        if status not in {CourseStatusEnum.DRAFT.value, CourseStatusEnum.PUBLISHED.value, CourseStatusEnum.ARCHIVED.value}:
            raise ValidationError("Invalid course status.")
        course = self.get_course_for_admin(course_id)
        course.status = status
        course.user_updated_object = admin_user
        if status == CourseStatusEnum.PUBLISHED.value and not course.published_at:
            course.published_at = now()
        course.save(update_fields=["status", "published_at", "user_updated_object", "updated_at"])
        return course

    def delete_course(self, admin_user, course_id):
        course = self.get_course_for_admin(course_id)
        course.user_updated_object = admin_user
        course.is_active = False
        course.is_deleted = True
        course.deleted_at = now()
        course.save(update_fields=["is_active", "is_deleted", "deleted_at", "user_updated_object", "updated_at"])
        return course

    def create_lesson(self, admin_user, dto):
        course = self.get_course_for_admin(dto.course_id)
        position = dto.position
        if position is None or int(position) <= 0:
            latest_position = (
                CourseLesson.objects.filter(course=course, is_deleted=False)
                .order_by("-position")
                .values_list("position", flat=True)
                .first()
            ) or 0
            position = latest_position + 1
        if CourseLesson.objects.filter(course=course, position=position, is_deleted=False).exists():
            raise ValidationError("A lesson with this position already exists for this course.")
        lesson = CourseLesson.objects.create(
            course=course,
            title=dto.title.strip(),
            slug=self.unique_lesson_slug(course, dto.title),
            description=(dto.description or "").strip(),
            content=(dto.content or "").strip(),
            video_url=(dto.video_url or "").strip(),
            duration_minutes=max(int(dto.duration_minutes or 0), 0),
            position=int(position),
            is_preview=bool(dto.is_preview),
            user_created_object=admin_user,
            user_updated_object=admin_user,
        )
        return lesson

    @staticmethod
    def unique_lesson_slug(course, title: str, lesson_id=None) -> str:
        base_slug = slugify(title or "lesson")[:220].strip("-") or "lesson"
        slug = base_slug
        counter = 2
        queryset = CourseLesson.objects.filter(course=course)
        if lesson_id:
            queryset = queryset.exclude(id=lesson_id)
        while queryset.filter(slug=slug).exists():
            suffix = f"-{counter}"
            slug = f"{base_slug[:220 - len(suffix)]}{suffix}"
            counter += 1
        return slug

    @staticmethod
    def published_courses_queryset():
        return (
            Course.objects.select_related("category", "instructor")
            .filter(
                status=CourseStatusEnum.PUBLISHED.value,
                is_active=True,
                is_deleted=False,
            )
            .annotate(
                average_rating=Avg(
                    "reviews__rating",
                    filter=Q(reviews__status=ReviewStatusEnum.APPROVED.value, reviews__is_deleted=False),
                ),
                reviews_count=Count(
                    "reviews",
                    filter=Q(reviews__status=ReviewStatusEnum.APPROVED.value, reviews__is_deleted=False),
                ),
            )
        )

    def list_published_courses(self, filters: dict):
        queryset = self.published_courses_queryset()
        search = filters.get(CourseQueryParamVO.SEARCH.value)
        category = filters.get(CourseQueryParamVO.CATEGORY.value)
        level = filters.get(CourseQueryParamVO.LEVEL.value)
        featured = filters.get(CourseQueryParamVO.FEATURED.value)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
            )
        if category and category != CourseWebCategoryFilterVO.ALL_VALUE.value:
            try:
                UUID(str(category))
                queryset = queryset.filter(Q(category__slug=category) | Q(category_id=category))
            except (TypeError, ValueError):
                queryset = queryset.filter(category__slug=category)
        if level and level != CourseWebLevelFilterVO.ALL_VALUE.value:
            queryset = queryset.filter(level=level)
        if featured in {"1", "true", "True", True}:
            queryset = queryset.filter(is_featured=True)

        return queryset.order_by("-is_featured", "-published_at", "-created_at")


    @staticmethod
    def list_published_course_categories():
        return (
            CourseCategory.objects.filter(
                is_active=True,
                is_deleted=False,
                courses__status=CourseStatusEnum.PUBLISHED.value,
                courses__is_active=True,
                courses__is_deleted=False,
            )
            .distinct()
            .order_by("position", "title")
        )

    def list_featured_courses(self, limit: int):
        return self.list_published_courses({CourseQueryParamVO.FEATURED.value: True})[:limit]

    def list_related_courses(self, course, limit: int):
        queryset = self.published_courses_queryset().exclude(id=course.id)
        if getattr(course, "category_id", None):
            queryset = queryset.filter(category_id=course.category_id)
        return queryset.order_by("-is_featured", "-published_at", "-created_at")[:limit]

    def get_published_course(self, course_id_or_slug):
        queryset = self.published_courses_queryset().prefetch_related("lessons")
        lookup = str(course_id_or_slug)
        try:
            UUID(lookup)
            query = Q(id=lookup)
        except (TypeError, ValueError):
            query = Q(slug=lookup)
        course = queryset.filter(query).first()
        if not course:
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        return course

    @staticmethod
    def get_course(course_id):
        course = Course.objects.filter(id=course_id, is_deleted=False).first()
        if not course:
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        return course

    @staticmethod
    def user_has_active_enrollment(user, course) -> bool:
        return CourseEnrollment.objects.filter(
            user=user,
            course=course,
            status=EnrollmentStatusEnum.ACTIVE.value,
            is_deleted=False,
        ).exists()

    def create_enrollment(self, user, course, source_order_number: str = ""):
        enrollment, _ = CourseEnrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                "status": EnrollmentStatusEnum.ACTIVE.value,
                "source_order_number": source_order_number,
                "user_created_object": user,
                "user_updated_object": user,
            },
        )
        if enrollment.status != EnrollmentStatusEnum.ACTIVE.value:
            enrollment.status = EnrollmentStatusEnum.ACTIVE.value
            enrollment.source_order_number = source_order_number or enrollment.source_order_number
            enrollment.user_updated_object = user
            enrollment.save(update_fields=["status", "source_order_number", "user_updated_object", "updated_at"])
        return enrollment

    @staticmethod
    def list_user_enrollments(user):
        return (
            CourseEnrollment.objects.select_related("course", "course__category", "course__instructor")
            .filter(user=user, is_deleted=False)
            .order_by("-enrolled_at")
        )

    @staticmethod
    def list_user_reviews(user):
        return (
            CourseReview.objects.select_related("course")
            .filter(user=user, is_deleted=False)
            .order_by("-created_at")
        )

    def create_or_update_review(self, user, dto):
        course = self.get_course(dto.course_id)
        if not course.is_published:
            raise NotFound(CourseMessagesVO.COURSE_NOT_FOUND)
        if not self.user_has_active_enrollment(user, course):
            raise PermissionDenied(CourseMessagesVO.COURSE_NOT_PURCHASED)

        review, _ = CourseReview.objects.update_or_create(
            course=course,
            user=user,
            defaults={
                "rating": dto.rating,
                "title": dto.title,
                "comment": dto.comment,
                "status": ReviewStatusEnum.PENDING.value,
                "reviewed_by": None,
                "reviewed_at": None,
                "admin_note": "",
                "user_created_object": user,
                "user_updated_object": user,
            },
        )
        return review

    @staticmethod
    def list_approved_reviews(course_id_or_slug):
        course = CoursePostgresAdapter().get_published_course(course_id_or_slug)
        return (
            CourseReview.objects.select_related("user")
            .filter(
                course=course,
                status=ReviewStatusEnum.APPROVED.value,
                is_active=True,
                is_deleted=False,
            )
            .order_by("-created_at")
        )

    @staticmethod
    def list_reviews_for_admin(status: str | None = None):
        queryset = CourseReview.objects.select_related("course", "user", "reviewed_by").filter(is_deleted=False)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    @staticmethod
    def moderate_review(review_id, admin_user, status: str, admin_note: str = ""):
        if status not in {ReviewStatusEnum.APPROVED.value, ReviewStatusEnum.REJECTED.value}:
            raise ValidationError("Invalid review moderation status.")
        review = CourseReview.objects.select_related("course", "user").filter(id=review_id, is_deleted=False).first()
        if not review:
            raise NotFound(CourseMessagesVO.REVIEW_NOT_FOUND)
        review.status = status
        review.reviewed_by = admin_user
        review.reviewed_at = now()
        review.admin_note = admin_note
        review.user_updated_object = admin_user
        review.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_note", "user_updated_object", "updated_at"])
        return review
