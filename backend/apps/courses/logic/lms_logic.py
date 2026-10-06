from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.timezone import now

from backend.apps.courses.dtos import (
    CourseAnnouncementCreateDTO,
    CourseAssignmentCreateDTO,
    CourseGradeItemDTO,
    CourseLessonManageDTO,
    CourseProgressToggleDTO,
    CourseQuestionCreateDTO,
    CourseQuestionReplyDTO,
    CourseResourceCreateDTO,
    CourseSectionCreateDTO,
    CourseSubmissionDTO,
    CourseSubmissionGradeDTO,
)
from backend.apps.courses.entities.lms_entities import CourseClassroomEntity, CourseGradeSummaryEntity
from backend.apps.courses.enums import (
    AssignmentStatusEnum, AssignmentSubmissionTypeEnum, CourseResourceTypeEnum,
    QuestionStatusEnum, SubmissionStatusEnum,
)
from backend.apps.courses.repositories.lms_repository import CourseLMSRepository
from backend.apps.courses.vo.lms_vo import CourseLMSFileVO, CourseLMSLimitVO, CourseLMSMessageVO


class CourseLMSLogic:
    def __init__(self, repository: CourseLMSRepository | None = None):
        self.repository = repository or CourseLMSRepository()

    def access_state(self, user, course) -> tuple[bool, bool]:
        return self.repository.is_instructor(user, course), self.repository.has_active_enrollment(user, course)

    def require_instructor(self, user, course) -> None:
        if not self.repository.is_instructor(user, course):
            raise PermissionDenied(CourseLMSMessageVO.INSTRUCTOR_ACCESS_REQUIRED.value)

    def require_student(self, user, course) -> None:
        if not self.repository.has_active_enrollment(user, course):
            raise PermissionDenied(CourseLMSMessageVO.STUDENT_ACCESS_REQUIRED.value)

    def require_classroom_access(self, user, course) -> tuple[bool, bool]:
        is_instructor, is_student = self.access_state(user, course)
        if not (is_instructor or is_student):
            raise PermissionDenied(CourseLMSMessageVO.CLASSROOM_ACCESS_REQUIRED.value)
        return is_instructor, is_student

    def classroom(self, *, user, course_id_or_slug) -> CourseClassroomEntity:
        course = self.repository.get_course(course_id_or_slug)
        is_instructor, is_student = self.require_classroom_access(user, course)
        include_unreleased = is_instructor
        sections = tuple(self.repository.sections(course, include_unreleased=include_unreleased))
        lessons = tuple(self.repository.lessons(course, include_unreleased=include_unreleased))
        resources = tuple(self.repository.resources(course, include_unreleased=include_unreleased))
        assignments = tuple(self.repository.assignments(course, include_drafts=is_instructor))
        announcements = tuple(self.repository.announcements(course)[: CourseLMSLimitVO.ANNOUNCEMENTS])

        submissions_by_assignment = {}
        completed_ids = frozenset()
        questions = ()
        grade_items = ()
        students = ()
        grade_summary = CourseGradeSummaryEntity()

        if is_student and not is_instructor:
            submissions = tuple(self.repository.submissions_for_student(course, user))
            submissions_by_assignment = {item.assignment_id: item for item in submissions}
            completed_ids = frozenset(item.lesson_id for item in self.repository.progress_for_student(course, user))
            questions = tuple(self.repository.questions_for_student(course, user)[: CourseLMSLimitVO.QUESTIONS])
            grade_items = tuple(self.repository.grade_items_for_student(course, user, published_only=True))
            grade_summary = self._grade_summary(submissions, grade_items)
        if is_instructor:
            students = tuple(self.repository.students(course))
            questions = tuple(self.repository.questions_for_course(course)[: CourseLMSLimitVO.QUESTIONS])
            all_submissions = tuple(self.repository.submissions_for_course(course))
            submissions_by_assignment = {}
            for item in all_submissions:
                submissions_by_assignment.setdefault(item.assignment_id, []).append(item)

        return CourseClassroomEntity(
            course=course, is_instructor=is_instructor, is_student=is_student,
            sections=sections, lessons=lessons, resources=resources, assignments=assignments,
            submissions_by_assignment=submissions_by_assignment, completed_lesson_ids=completed_ids,
            announcements=announcements, questions=questions, grade_items=grade_items,
            grade_summary=grade_summary, students=students,
        )

    @staticmethod
    def _grade_summary(submissions, grade_items) -> CourseGradeSummaryEntity:
        assignment_earned = Decimal("0")
        assignment_possible = Decimal("0")
        for submission in submissions:
            if submission.score is not None:
                assignment_earned += Decimal(submission.score)
                assignment_possible += Decimal(submission.assignment.max_score)
        manual_earned = sum((Decimal(item.score) for item in grade_items), Decimal("0"))
        manual_possible = sum((Decimal(item.max_score) for item in grade_items), Decimal("0"))
        return CourseGradeSummaryEntity(assignment_earned, assignment_possible, manual_earned, manual_possible)

    @transaction.atomic
    def create_section(self, *, actor, dto: CourseSectionCreateDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        return self.repository.create_section(actor=actor, course=course, dto=dto)

    @transaction.atomic
    def save_lesson(self, *, actor, dto: CourseLessonManageDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        return self.repository.save_lesson(actor=actor, course=course, dto=dto)

    @staticmethod
    def _validate_upload(file) -> None:
        if not file:
            return
        size = int(getattr(file, "size", 0) or 0)
        if size > CourseLMSFileVO.MAX_FILE_SIZE_BYTES:
            raise ValidationError(CourseLMSMessageVO.FILE_TOO_LARGE.value)
        suffix = Path(str(getattr(file, "name", ""))).suffix.casefold()
        if suffix not in CourseLMSFileVO.ALLOWED_EXTENSIONS:
            raise ValidationError(CourseLMSMessageVO.FILE_TYPE_NOT_ALLOWED.value)

    @transaction.atomic
    def create_resource(self, *, actor, dto: CourseResourceCreateDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        if dto.resource_type == CourseResourceTypeEnum.FILE.value and not dto.file:
            raise ValidationError(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        self._validate_upload(dto.file)
        if dto.resource_type == CourseResourceTypeEnum.LINK.value and not dto.external_url:
            raise ValidationError(CourseLMSMessageVO.RESOURCE_LINK_REQUIRED.value)
        if dto.resource_type == CourseResourceTypeEnum.NOTE.value and not dto.text_content.strip():
            raise ValidationError(CourseLMSMessageVO.RESOURCE_TEXT_REQUIRED.value)
        return self.repository.create_resource(actor=actor, course=course, dto=dto)

    @transaction.atomic
    def create_assignment(self, *, actor, dto: CourseAssignmentCreateDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        if dto.due_at and dto.starts_at and dto.due_at <= dto.starts_at:
            raise ValidationError(CourseLMSMessageVO.INVALID_DEADLINE.value)
        self._validate_upload(dto.attachment)
        if dto.max_score <= 0:
            raise ValidationError(CourseLMSMessageVO.INVALID_MAX_SCORE.value)
        return self.repository.create_assignment(actor=actor, course=course, dto=dto)

    @transaction.atomic
    def submit_assignment(self, *, student, dto: CourseSubmissionDTO):
        assignment = self.repository.get_assignment(dto.assignment_id)
        self.require_student(student, assignment.course)
        current = now()
        if assignment.status != AssignmentStatusEnum.PUBLISHED.value:
            raise ValidationError(CourseLMSMessageVO.ASSIGNMENT_CLOSED.value)
        if assignment.starts_at and current < assignment.starts_at:
            raise ValidationError(CourseLMSMessageVO.ASSIGNMENT_NOT_STARTED.value)
        is_late = bool(assignment.due_at and current > assignment.due_at)
        if is_late and not assignment.allow_late_submission:
            raise ValidationError(CourseLMSMessageVO.ASSIGNMENT_DEADLINE_PASSED.value)
        self._validate_submission_payload(assignment.submission_type, dto)
        self._validate_upload(dto.file)
        status = SubmissionStatusEnum.LATE.value if is_late else SubmissionStatusEnum.SUBMITTED.value
        return self.repository.upsert_submission(student=student, assignment=assignment, dto=dto, status=status)

    @staticmethod
    def _validate_submission_payload(submission_type: str, dto: CourseSubmissionDTO):
        has_file = bool(dto.file)
        has_text = bool(dto.text_answer.strip())
        has_link = bool(dto.link_url.strip())
        if not (has_file or has_text or has_link):
            raise ValidationError(CourseLMSMessageVO.SUBMISSION_EMPTY.value)
        expected = submission_type
        invalid = (
            expected == AssignmentSubmissionTypeEnum.FILE.value and not has_file
            or expected == AssignmentSubmissionTypeEnum.TEXT.value and not has_text
            or expected == AssignmentSubmissionTypeEnum.LINK.value and not has_link
        )
        if invalid:
            raise ValidationError(CourseLMSMessageVO.SUBMISSION_TYPE_INVALID.value)

    @transaction.atomic
    def grade_submission(self, *, actor, dto: CourseSubmissionGradeDTO):
        submission = self.repository.get_submission(dto.submission_id)
        self.require_instructor(actor, submission.assignment.course)
        score = Decimal(dto.score)
        if score < 0 or score > Decimal(submission.assignment.max_score):
            raise ValidationError(CourseLMSMessageVO.SCORE_OUT_OF_RANGE.value)
        return self.repository.grade_submission(actor=actor, submission=submission, score=score, feedback=dto.feedback)

    @transaction.atomic
    def create_grade_item(self, *, actor, dto: CourseGradeItemDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        enrollment = next((item for item in self.repository.students(course) if item.user_id == dto.student_id), None)
        if enrollment is None:
            raise ValidationError(CourseLMSMessageVO.STUDENT_NOT_ENROLLED.value)
        if dto.max_score <= 0 or dto.score < 0 or dto.score > dto.max_score:
            raise ValidationError(CourseLMSMessageVO.SCORE_OUT_OF_RANGE.value)
        return self.repository.create_grade_item(actor=actor, course=course, student=enrollment.user, dto=dto)

    @transaction.atomic
    def create_question(self, *, student, dto: CourseQuestionCreateDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_student(student, course)
        if not dto.body.strip():
            raise ValidationError(CourseLMSMessageVO.QUESTION_BODY_REQUIRED.value)
        self._validate_upload(dto.attachment)
        return self.repository.create_question(student=student, course=course, dto=dto)

    def question_detail(self, *, user, question_id):
        question = self.repository.get_question(question_id)
        if not (self.repository.is_instructor(user, question.course) or question.student_id == user.id):
            raise PermissionDenied(CourseLMSMessageVO.CLASSROOM_ACCESS_REQUIRED.value)
        return question

    @transaction.atomic
    def reply_question(self, *, sender, dto: CourseQuestionReplyDTO):
        question = self.question_detail(user=sender, question_id=dto.question_id)
        if question.status == QuestionStatusEnum.CLOSED.value:
            raise ValidationError(CourseLMSMessageVO.QUESTION_CLOSED.value)
        if not dto.body.strip():
            raise ValidationError(CourseLMSMessageVO.QUESTION_BODY_REQUIRED.value)
        self._validate_upload(dto.attachment)
        return self.repository.add_question_message(sender=sender, question=question, dto=dto)

    @transaction.atomic
    def create_announcement(self, *, actor, dto: CourseAnnouncementCreateDTO):
        course = self.repository.get_course(dto.course_id)
        self.require_instructor(actor, course)
        return self.repository.create_announcement(actor=actor, course=course, dto=dto)

    @transaction.atomic
    def set_progress(self, *, student, dto: CourseProgressToggleDTO):
        lesson = self.repository.get_lesson(dto.lesson_id)
        self.require_student(student, lesson.course)
        return self.repository.set_lesson_progress(student=student, lesson=lesson, completed=dto.completed)

    def resource_for_download(self, *, user, resource_id):
        resource = self.repository.get_resource(resource_id)
        self.require_classroom_access(user, resource.course)
        if not resource.file:
            raise ValidationError(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        return resource.file

    def assignment_for_download(self, *, user, assignment_id):
        assignment = self.repository.get_assignment(assignment_id)
        self.require_classroom_access(user, assignment.course)
        if not assignment.attachment:
            raise ValidationError(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        return assignment.attachment

    def submission_for_download(self, *, user, submission_id):
        submission = self.repository.get_submission(submission_id)
        if not (self.repository.is_instructor(user, submission.assignment.course) or submission.student_id == user.id):
            raise PermissionDenied(CourseLMSMessageVO.CLASSROOM_ACCESS_REQUIRED.value)
        if not submission.file:
            raise ValidationError(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        return submission.file

    def question_attachment_for_download(self, *, user, message_id):
        message = self.repository.get_question_message(message_id)
        question = message.question
        if not (self.repository.is_instructor(user, question.course) or question.student_id == user.id):
            raise PermissionDenied(CourseLMSMessageVO.CLASSROOM_ACCESS_REQUIRED.value)
        if not message.attachment:
            raise ValidationError(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value)
        return message.attachment
