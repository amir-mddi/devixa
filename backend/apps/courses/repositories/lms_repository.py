from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db.models import Q
from django.utils.timezone import now
from rest_framework.exceptions import NotFound

from backend.apps.core_models.vo.common_vo import UserRoleVO

from backend.apps.courses.enums import (
    AssignmentStatusEnum, EnrollmentStatusEnum, QuestionStatusEnum, SubmissionStatusEnum,
)
from backend.apps.courses.models import (
    Course,
    CourseAnnouncement,
    CourseAssignment,
    CourseEnrollment,
    CourseGradeItem,
    CourseLesson,
    CourseLessonProgress,
    CourseQuestion,
    CourseQuestionMessage,
    CourseResource,
    CourseSection,
    CourseSubmission,
)
from backend.apps.courses.vo.lms_vo import CourseLMSMessageVO


class CourseLMSRepository:
    @staticmethod
    def get_course(course_id_or_slug):
        lookup = str(course_id_or_slug)
        query = Q(slug=lookup)
        try:
            UUID(lookup)
            query = Q(id=lookup)
        except (TypeError, ValueError):
            pass
        course = (
            Course.objects.select_related("instructor", "category")
            .filter(query, is_deleted=False, is_active=True)
            .first()
        )
        if not course:
            raise NotFound(CourseLMSMessageVO.COURSE_NOT_FOUND.value)
        return course

    @staticmethod
    def is_instructor(user, course) -> bool:
        if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
            return False

        role_symbol = str(
            getattr(getattr(user, "role", None), "symbol", "") or ""
        ).strip().lower()

        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_staff", False)
            or role_symbol == UserRoleVO.ADMIN
        ):
            return True

        return bool(
            role_symbol == UserRoleVO.INSTRUCTOR
            and user.id == course.instructor_id
        )

    @staticmethod
    def update_course_details(*, actor, course, dto):
        course.title = dto.title.strip()
        course.short_description = (dto.short_description or "").strip()
        course.description = (dto.description or "").strip()
        course.level = dto.level
        course.duration_minutes = max(int(dto.duration_minutes or 0), 0)
        course.user_updated_object = actor
        course.save(
            update_fields=[
                "title",
                "short_description",
                "description",
                "level",
                "duration_minutes",
                "user_updated_object",
                "updated_at",
            ]
        )
        return course

    @staticmethod
    def has_active_enrollment(user, course) -> bool:
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return CourseEnrollment.objects.filter(
            user=user,
            course=course,
            status=EnrollmentStatusEnum.ACTIVE.value,
            is_active=True,
            is_deleted=False,
        ).exists()

    @staticmethod
    def sections(course, *, include_unreleased=False):
        qs = CourseSection.objects.filter(course=course, is_active=True, is_deleted=False)
        if not include_unreleased:
            qs = qs.filter(Q(release_at__isnull=True) | Q(release_at__lte=now()))
        return qs.order_by("position", "created_at")

    @staticmethod
    def lessons(course, *, include_unreleased=False):
        qs = CourseLesson.objects.select_related("section").filter(course=course, is_active=True, is_deleted=False)
        if not include_unreleased:
            qs = qs.filter(Q(release_at__isnull=True) | Q(release_at__lte=now()))
        return qs.order_by("position", "created_at")

    @staticmethod
    def resources(course, *, include_unreleased=False):
        qs = CourseResource.objects.select_related("lesson").filter(course=course, is_active=True, is_deleted=False)
        if not include_unreleased:
            qs = qs.filter(Q(release_at__isnull=True) | Q(release_at__lte=now()))
        return qs.order_by("position", "created_at")

    @staticmethod
    def assignments(course, *, include_drafts=False):
        qs = CourseAssignment.objects.select_related("lesson").filter(course=course, is_active=True, is_deleted=False)
        if not include_drafts:
            qs = qs.filter(status=AssignmentStatusEnum.PUBLISHED.value).filter(
                Q(starts_at__isnull=True) | Q(starts_at__lte=now())
            )
        return qs.order_by("position", "due_at", "created_at")

    @staticmethod
    def submissions_for_student(course, student):
        return CourseSubmission.objects.select_related("assignment", "graded_by").filter(
            assignment__course=course,
            student=student,
            is_deleted=False,
        )

    @staticmethod
    def submissions_for_course(course):
        return CourseSubmission.objects.select_related("assignment", "student", "graded_by").filter(
            assignment__course=course,
            is_deleted=False,
        ).order_by("-submitted_at")

    @staticmethod
    def progress_for_student(course, student):
        return CourseLessonProgress.objects.filter(
            lesson__course=course,
            student=student,
            completed_at__isnull=False,
            is_deleted=False,
        )

    @staticmethod
    def announcements(course):
        return CourseAnnouncement.objects.select_related("author").filter(
            course=course,
            is_active=True,
            is_deleted=False,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now())).order_by("-is_pinned", "-published_at")

    @staticmethod
    def questions_for_student(course, student):
        return CourseQuestion.objects.filter(course=course, student=student, is_deleted=False).order_by("-last_message_at")

    @staticmethod
    def questions_for_course(course):
        return CourseQuestion.objects.select_related("student").filter(course=course, is_deleted=False).order_by("-last_message_at")

    @staticmethod
    def grade_items_for_student(course, student, *, published_only=True):
        qs = CourseGradeItem.objects.filter(course=course, student=student, is_deleted=False)
        if published_only:
            qs = qs.filter(is_published_to_student=True)
        return qs.order_by("created_at")

    @staticmethod
    def students(course):
        return CourseEnrollment.objects.select_related("user").filter(
            course=course,
            status=EnrollmentStatusEnum.ACTIVE.value,
            is_active=True,
            is_deleted=False,
        ).order_by("user__first_name", "user__last_name", "user__username")

    @staticmethod
    def _next_position(model, *, course, extra_filters=None) -> int:
        filters = {"course": course, "is_deleted": False}
        filters.update(extra_filters or {})
        latest = model.objects.filter(**filters).order_by("-position").values_list("position", flat=True).first() or 0
        return int(latest) + 1

    def create_section(self, *, actor, course, dto):
        position = dto.position or self._next_position(CourseSection, course=course)
        return CourseSection.objects.create(
            course=course, title=dto.title.strip(), description=dto.description.strip(),
            position=position, release_at=dto.release_at,
            user_created_object=actor, user_updated_object=actor,
        )

    def save_lesson(self, *, actor, course, dto):
        lesson = None
        if dto.lesson_id:
            lesson = CourseLesson.objects.filter(id=dto.lesson_id, course=course, is_deleted=False).first()
            if not lesson:
                raise NotFound(CourseLMSMessageVO.LESSON_NOT_FOUND.value)
        section = None
        if dto.section_id:
            section = CourseSection.objects.filter(id=dto.section_id, course=course, is_deleted=False).first()
            if section is None:
                raise NotFound(CourseLMSMessageVO.SECTION_NOT_FOUND.value)
        if lesson is None:
            from backend.apps.courses.repositories.adapters.postgres_adapter import CoursePostgresAdapter
            position = dto.position or self._next_position(CourseLesson, course=course)
            lesson = CourseLesson(
                course=course,
                slug=CoursePostgresAdapter.unique_lesson_slug(course, dto.title),
                user_created_object=actor,
            )
        else:
            position = dto.position or lesson.position
        lesson.section = section
        lesson.title = dto.title.strip()
        lesson.description = dto.description.strip()
        lesson.content = dto.content.strip()
        lesson.video_url = dto.video_url.strip()
        lesson.duration_minutes = max(int(dto.duration_minutes or 0), 0)
        lesson.position = position
        lesson.is_preview = bool(dto.is_preview)
        lesson.release_at = dto.release_at
        lesson.require_completion = bool(dto.require_completion)
        lesson.user_updated_object = actor
        lesson.save()
        return lesson

    def create_resource(self, *, actor, course, dto):
        lesson = None
        if dto.lesson_id:
            lesson = CourseLesson.objects.filter(id=dto.lesson_id, course=course, is_deleted=False).first()
            if lesson is None:
                raise NotFound(CourseLMSMessageVO.LESSON_NOT_FOUND.value)
        position = dto.position or self._next_position(CourseResource, course=course)
        return CourseResource.objects.create(
            course=course, lesson=lesson, title=dto.title.strip(), description=dto.description.strip(),
            resource_type=dto.resource_type, file=dto.file, external_url=dto.external_url.strip(),
            text_content=dto.text_content.strip(), position=position, release_at=dto.release_at,
            user_created_object=actor, user_updated_object=actor,
        )

    def create_assignment(self, *, actor, course, dto):
        lesson = None
        if dto.lesson_id:
            lesson = CourseLesson.objects.filter(id=dto.lesson_id, course=course, is_deleted=False).first()
            if lesson is None:
                raise NotFound(CourseLMSMessageVO.LESSON_NOT_FOUND.value)
        position = dto.position or self._next_position(CourseAssignment, course=course)
        return CourseAssignment.objects.create(
            course=course, lesson=lesson, title=dto.title.strip(), assignment_type=dto.assignment_type,
            submission_type=dto.submission_type, instructions=dto.instructions.strip(), attachment=dto.attachment,
            starts_at=dto.starts_at, due_at=dto.due_at, allow_late_submission=dto.allow_late_submission,
            max_score=dto.max_score, position=position, status=dto.status,
            user_created_object=actor, user_updated_object=actor,
        )

    @staticmethod
    def get_assignment(assignment_id):
        assignment = CourseAssignment.objects.select_related("course", "lesson", "course__instructor").filter(
            id=assignment_id, is_deleted=False
        ).first()
        if not assignment:
            raise NotFound(CourseLMSMessageVO.ASSIGNMENT_NOT_FOUND.value)
        return assignment

    @staticmethod
    def get_submission(submission_id):
        submission = CourseSubmission.objects.select_related("assignment__course", "student").filter(id=submission_id, is_deleted=False).first()
        if not submission:
            raise NotFound(CourseLMSMessageVO.SUBMISSION_NOT_FOUND.value)
        return submission

    @staticmethod
    def upsert_submission(*, student, assignment, dto, status):
        submission, _ = CourseSubmission.objects.update_or_create(
            assignment=assignment,
            student=student,
            defaults={
                "text_answer": dto.text_answer.strip(),
                "link_url": dto.link_url.strip(),
                "status": status,
                "submitted_at": now(),
                "score": None,
                "feedback": "",
                "graded_by": None,
                "graded_at": None,
                "user_created_object": student,
                "user_updated_object": student,
            },
        )
        if dto.file:
            submission.file = dto.file
            submission.save(update_fields=["file", "updated_at"])
        return submission

    @staticmethod
    def grade_submission(*, actor, submission, score: Decimal, feedback: str):
        submission.score = score
        submission.feedback = feedback.strip()
        submission.graded_by = actor
        submission.graded_at = now()
        submission.status = SubmissionStatusEnum.GRADED.value
        submission.user_updated_object = actor
        submission.save()
        return submission

    @staticmethod
    def create_grade_item(*, actor, course, student, dto):
        return CourseGradeItem.objects.create(
            course=course, student=student, title=dto.title.strip(), category=dto.category,
            score=dto.score, max_score=dto.max_score, note=dto.note.strip(),
            is_published_to_student=dto.is_published_to_student,
            user_created_object=actor, user_updated_object=actor,
        )

    @staticmethod
    def create_question(*, student, course, dto):
        question = CourseQuestion.objects.create(
            course=course, student=student, subject=dto.subject.strip(), last_message_at=now(),
            user_created_object=student, user_updated_object=student,
        )
        CourseQuestionMessage.objects.create(
            question=question, sender=student, body=dto.body.strip(), attachment=dto.attachment,
            user_created_object=student, user_updated_object=student,
        )
        return question

    @staticmethod
    def get_question(question_id):
        question = CourseQuestion.objects.select_related("course__instructor", "student").prefetch_related("messages__sender").filter(
            id=question_id, is_deleted=False
        ).first()
        if not question:
            raise NotFound(CourseLMSMessageVO.QUESTION_NOT_FOUND.value)
        return question

    @staticmethod
    def add_question_message(*, sender, question, dto):
        message = CourseQuestionMessage.objects.create(
            question=question, sender=sender, body=dto.body.strip(), attachment=dto.attachment,
            user_created_object=sender, user_updated_object=sender,
        )
        question.last_message_at = now()
        if sender.id == question.course.instructor_id or getattr(sender, "is_staff", False):
            question.status = QuestionStatusEnum.ANSWERED.value
        else:
            question.status = QuestionStatusEnum.OPEN.value
        question.user_updated_object = sender
        question.save(update_fields=["last_message_at", "status", "user_updated_object", "updated_at"])
        return message

    @staticmethod
    def create_announcement(*, actor, course, dto):
        return CourseAnnouncement.objects.create(
            course=course, author=actor, title=dto.title.strip(), message=dto.message.strip(),
            expires_at=dto.expires_at, is_pinned=dto.is_pinned,
            user_created_object=actor, user_updated_object=actor,
        )

    @staticmethod
    def set_lesson_progress(*, student, lesson, completed: bool):
        progress, _ = CourseLessonProgress.objects.get_or_create(
            lesson=lesson, student=student,
            defaults={"user_created_object": student, "user_updated_object": student},
        )
        progress.completed_at = now() if completed else None
        progress.user_updated_object = student
        progress.save(update_fields=["completed_at", "user_updated_object", "updated_at"])
        return progress

    @staticmethod
    def get_lesson(lesson_id):
        lesson = CourseLesson.objects.select_related("course__instructor").filter(id=lesson_id, is_deleted=False).first()
        if not lesson:
            raise NotFound(CourseLMSMessageVO.LESSON_NOT_FOUND.value)
        return lesson

    @staticmethod
    def get_resource(resource_id):
        resource = CourseResource.objects.select_related("course__instructor").filter(id=resource_id, is_deleted=False).first()
        if not resource:
            raise NotFound(CourseLMSMessageVO.RESOURCE_NOT_FOUND.value)
        return resource

    @staticmethod
    def get_question_message(message_id):
        message = CourseQuestionMessage.objects.select_related("question__course__instructor", "question__student").filter(id=message_id, is_deleted=False).first()
        if not message:
            raise NotFound(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        return message
