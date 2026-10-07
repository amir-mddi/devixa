from __future__ import annotations

import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from rest_framework.exceptions import NotFound

from backend.apps.courses.dtos import (
    CourseAnnouncementCreateDTO,
    CourseAssignmentCreateDTO,
    CourseGradeItemDTO,
    CourseInstructorUpdateDTO,
    CourseLessonManageDTO,
    CourseProgressToggleDTO,
    CourseQuestionCreateDTO,
    CourseQuestionReplyDTO,
    CourseResourceCreateDTO,
    CourseSectionCreateDTO,
    CourseSubmissionDTO,
    CourseSubmissionGradeDTO,
)
from backend.apps.courses.logic import CourseLMSLogic
from backend.apps.courses.vo.lms_vo import CourseLMSMessageVO, CourseLMSTemplateVO
from backend.apps.courses.web.lms_forms import (
    CourseAnnouncementForm,
    CourseAssignmentForm,
    CourseGradeItemForm,
    CourseInstructorSettingsForm,
    CourseLessonManageForm,
    CourseQuestionForm,
    CourseQuestionReplyForm,
    CourseResourceForm,
    CourseSectionForm,
    CourseSubmissionForm,
    CourseSubmissionGradeForm,
)


class CourseLMSWebMixin:
    logic_class = CourseLMSLogic

    @property
    def lms(self):
        if not hasattr(self, "_lms"):
            self._lms = self.logic_class()
        return self._lms

    @staticmethod
    def error_message(exc: Exception) -> str:
        if hasattr(exc, "messages") and exc.messages:
            return str(exc.messages[0])
        if hasattr(exc, "detail"):
            return str(exc.detail)
        return str(exc) or CourseLMSMessageVO.INVALID_FORM.value

    def course_redirect(self, slug: str, *, instructor=False):
        route = "courses_web:instructor_panel" if instructor else "courses_web:classroom"
        return redirect(route, slug=slug)


class CourseClassroomPageView(LoginRequiredMixin, CourseLMSWebMixin, TemplateView):
    template_name = CourseLMSTemplateVO.CLASSROOM.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            classroom = self.lms.classroom(user=self.request.user, course_id_or_slug=kwargs["slug"])
        except (NotFound, PermissionDenied) as exc:
            raise Http404(self.error_message(exc)) from exc
        if classroom.is_instructor and not classroom.is_student:
            return context | {"classroom": classroom, "course": classroom.course, "instructor_link": True}
        context.update(
            {
                "classroom": classroom,
                "course": classroom.course,
                "submission_form": CourseSubmissionForm(),
                "question_form": CourseQuestionForm(),
            }
        )
        return context


class InstructorClassroomPageView(LoginRequiredMixin, CourseLMSWebMixin, TemplateView):
    template_name = CourseLMSTemplateVO.INSTRUCTOR_PANEL.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            classroom = self.lms.classroom(user=self.request.user, course_id_or_slug=kwargs["slug"])
            self.lms.require_instructor(self.request.user, classroom.course)
        except (NotFound, PermissionDenied) as exc:
            raise Http404(self.error_message(exc)) from exc
        context.update(
            {
                "classroom": classroom,
                "course": classroom.course,
                "course_settings_form": CourseInstructorSettingsForm(
                    initial={
                        "title": classroom.course.title,
                        "short_description": classroom.course.short_description,
                        "description": classroom.course.description,
                        "level": classroom.course.level,
                        "duration_minutes": classroom.course.duration_minutes,
                    }
                ),
                "section_form": CourseSectionForm(),
                "lesson_form": CourseLessonManageForm(sections=classroom.sections),
                "resource_form": CourseResourceForm(lessons=classroom.lessons),
                "assignment_form": CourseAssignmentForm(lessons=classroom.lessons),
                "grade_item_form": CourseGradeItemForm(students=classroom.students),
                "announcement_form": CourseAnnouncementForm(),
                "grade_form": CourseSubmissionGradeForm(),
            }
        )
        return context


class CourseInstructorSettingsUpdateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc

        form = CourseInstructorSettingsForm(request.POST)
        if form.is_valid():
            try:
                self.lms.update_course_details(
                    actor=request.user,
                    dto=CourseInstructorUpdateDTO(
                        course_id=classroom.course.id,
                        **form.cleaned_data,
                    ),
                )
                messages.success(request, CourseLMSMessageVO.COURSE_DETAILS_UPDATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(classroom.course.slug, instructor=True)


class CourseSectionCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            try:
                self.lms.create_section(actor=request.user, dto=CourseSectionCreateDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.SECTION_CREATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseLessonSaveView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug, lesson_id=None):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseLessonManageForm(request.POST, sections=classroom.sections)
        if form.is_valid():
            try:
                self.lms.save_lesson(
                    actor=request.user,
                    dto=CourseLessonManageDTO(course_id=course.id, lesson_id=lesson_id, **form.cleaned_data),
                )
                messages.success(request, CourseLMSMessageVO.LESSON_SAVED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseResourceCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseResourceForm(request.POST, request.FILES, lessons=classroom.lessons)
        if form.is_valid():
            try:
                self.lms.create_resource(actor=request.user, dto=CourseResourceCreateDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.RESOURCE_CREATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseAssignmentCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseAssignmentForm(request.POST, request.FILES, lessons=classroom.lessons)
        if form.is_valid():
            try:
                self.lms.create_assignment(actor=request.user, dto=CourseAssignmentCreateDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.ASSIGNMENT_CREATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseSubmissionCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug, assignment_id):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                self.lms.submit_assignment(student=request.user, dto=CourseSubmissionDTO(assignment_id=assignment_id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.SUBMISSION_SAVED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug)


class CourseSubmissionGradeView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug, submission_id):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseSubmissionGradeForm(request.POST)
        if form.is_valid():
            try:
                self.lms.grade_submission(actor=request.user, dto=CourseSubmissionGradeDTO(submission_id=submission_id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.SUBMISSION_GRADED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseGradeCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseGradeItemForm(request.POST, students=classroom.students)
        if form.is_valid():
            try:
                self.lms.create_grade_item(actor=request.user, dto=CourseGradeItemDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.GRADE_CREATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseQuestionCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseQuestionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                question = self.lms.create_question(student=request.user, dto=CourseQuestionCreateDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.QUESTION_CREATED.value)
                return redirect("courses_web:question_detail", slug=course.slug, question_id=question.id)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug)


class CourseQuestionDetailView(LoginRequiredMixin, CourseLMSWebMixin, TemplateView):
    template_name = CourseLMSTemplateVO.QUESTION_DETAIL.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            question = self.lms.question_detail(user=self.request.user, question_id=kwargs["question_id"])
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        context.update({"question": question, "course": question.course, "reply_form": CourseQuestionReplyForm()})
        return context


class CourseQuestionReplyView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug, question_id):
        form = CourseQuestionReplyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                self.lms.reply_question(sender=request.user, dto=CourseQuestionReplyDTO(question_id=question_id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.QUESTION_REPLIED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return redirect("courses_web:question_detail", slug=slug, question_id=question_id)


class CourseAnnouncementCreateView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug):
        try:
            classroom = self.lms.classroom(user=request.user, course_id_or_slug=slug)
            self.lms.require_instructor(request.user, classroom.course)
        except (PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        course = classroom.course
        form = CourseAnnouncementForm(request.POST)
        if form.is_valid():
            try:
                self.lms.create_announcement(actor=request.user, dto=CourseAnnouncementCreateDTO(course_id=course.id, **form.cleaned_data))
                messages.success(request, CourseLMSMessageVO.ANNOUNCEMENT_CREATED.value)
            except (ValidationError, PermissionDenied, NotFound) as exc:
                messages.error(request, self.error_message(exc))
        else:
            messages.error(request, CourseLMSMessageVO.INVALID_FORM.value)
        return self.course_redirect(course.slug, instructor=True)


class CourseLessonProgressView(LoginRequiredMixin, CourseLMSWebMixin, View):
    def post(self, request, slug, lesson_id):
        completed = str(request.POST.get("completed", "1")).lower() not in {"0", "false", "off", "no"}
        try:
            self.lms.set_progress(student=request.user, dto=CourseProgressToggleDTO(lesson_id=lesson_id, completed=completed))
            messages.success(request, CourseLMSMessageVO.PROGRESS_UPDATED.value)
        except (ValidationError, PermissionDenied, NotFound) as exc:
            messages.error(request, self.error_message(exc))
        return self.course_redirect(slug)


class ProtectedFileDownloadView(LoginRequiredMixin, CourseLMSWebMixin, View):
    file_kind = "resource"

    def get(self, request, object_id):
        try:
            if self.file_kind == "assignment":
                field = self.lms.assignment_for_download(user=request.user, assignment_id=object_id)
            elif self.file_kind == "submission":
                field = self.lms.submission_for_download(user=request.user, submission_id=object_id)
            elif self.file_kind == "question":
                field = self.lms.question_attachment_for_download(user=request.user, message_id=object_id)
            else:
                field = self.lms.resource_for_download(user=request.user, resource_id=object_id)
        except (ValidationError, PermissionDenied, NotFound) as exc:
            raise Http404(self.error_message(exc)) from exc
        try:
            field.open("rb")
        except (FileNotFoundError, OSError) as exc:
            raise Http404(CourseLMSMessageVO.FILE_NOT_AVAILABLE.value) from exc
        filename = os.path.basename(field.name)
        return FileResponse(field, as_attachment=True, filename=filename)


class ResourceDownloadView(ProtectedFileDownloadView):
    file_kind = "resource"


class AssignmentDownloadView(ProtectedFileDownloadView):
    file_kind = "assignment"


class SubmissionDownloadView(ProtectedFileDownloadView):
    file_kind = "submission"


class QuestionAttachmentDownloadView(ProtectedFileDownloadView):
    file_kind = "question"
