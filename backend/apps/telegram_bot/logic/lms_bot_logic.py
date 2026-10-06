from __future__ import annotations

import html
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from backend.apps.courses.logic.lms_logic import CourseLMSLogic
from backend.apps.telegram_bot.dtos.lms_bot_dtos import LMSBotScreenDTO
from backend.apps.telegram_bot.vo.lms_bot_vo import (
    LMSBotCallbackVO, LMSBotTextVO, LMSBotVisualVO, LMSBotWebPathVO,
)


class LMSBotLogic:
    def __init__(self, lms_logic: CourseLMSLogic | None = None):
        self.lms = lms_logic or CourseLMSLogic()

    @staticmethod
    def _button(text: str, *, callback_data: str | None = None, url: str | None = None) -> dict:
        button = {"text": text}
        if url:
            button["url"] = url
        else:
            button["callback_data"] = callback_data or ""
        return button

    @staticmethod
    def _app_url(base_url: str, path: str) -> str:
        try:
            parts = urlsplit((base_url or "").strip())
            if parts.scheme == "https" and parts.hostname and not parts.username and not parts.password:
                origin = urlunsplit(("https", parts.netloc, "", "", ""))
                return f"{origin}/{path.lstrip('/')}"
        except ValueError:
            pass
        return ""

    @staticmethod
    def _format_deadline(value: datetime | None, no_deadline: str) -> str:
        if value is None:
            return no_deadline
        return value.astimezone().strftime("%Y-%m-%d %H:%M")

    def _classroom(self, user, course_id):
        return self.lms.classroom(user=user, course_id_or_slug=course_id)

    def classroom_screen(self, *, user, course_id, language: str, app_url: str = "") -> LMSBotScreenDTO:
        classroom = self._classroom(user, course_id)
        t = lambda key, **kwargs: LMSBotTextVO.get(language, key, **kwargs)
        title = html.escape(classroom.course.title)
        if classroom.is_instructor:
            summary = t(
                "instructor_summary",
                students=len(classroom.students), lessons=len(classroom.lessons),
                assignments=len(classroom.assignments), questions=len(classroom.questions),
            )
        else:
            summary = t(
                "classroom_summary",
                progress=classroom.progress_percentage,
                completed=classroom.completed_lessons,
                lessons=classroom.total_lessons,
                assignments=len(classroom.assignments),
                questions=len(classroom.questions),
            )
        course_id = classroom.course.id
        rows = [
            (
                self._button(t("button_lessons"), callback_data=LMSBotCallbackVO.lessons(course_id)),
                self._button(t("button_assignments"), callback_data=LMSBotCallbackVO.assignments(course_id)),
            ),
            (
                self._button(t("button_grades"), callback_data=LMSBotCallbackVO.grades(course_id)),
                self._button(t("button_questions"), callback_data=LMSBotCallbackVO.questions(course_id)),
            ),
        ]
        web_path = LMSBotWebPathVO.INSTRUCTOR if classroom.is_instructor else LMSBotWebPathVO.CLASSROOM
        web_url = self._app_url(app_url, web_path.format(slug=classroom.course.slug))
        if web_url:
            rows.append((self._button(t("button_instructor_web") if classroom.is_instructor else t("button_open_web"), url=web_url),))
        rows.append((self._button(t("button_back_course"), callback_data=LMSBotCallbackVO.course_detail(course_id)),))
        return LMSBotScreenDTO(text=f"{t('classroom_title', title=title)}\n\n{summary}", keyboard=tuple(rows))

    def lessons_screen(self, *, user, course_id, language: str, app_url: str = "") -> LMSBotScreenDTO:
        classroom = self._classroom(user, course_id)
        t = lambda key, **kwargs: LMSBotTextVO.get(language, key, **kwargs)
        lines = [t("lessons_title", title=html.escape(classroom.course.title))]
        if not classroom.lessons:
            lines.append(t("lessons_empty"))
        for lesson in classroom.lessons[:20]:
            completed = lesson.id in classroom.completed_lesson_ids
            state = LMSBotVisualVO.LESSON_COMPLETE if completed else LMSBotVisualVO.LESSON_PENDING
            duration = t("lesson_duration", minutes=lesson.duration_minutes) if lesson.duration_minutes else ""
            lines.append(t("lesson_item", state=state, position=lesson.position, title=html.escape(lesson.title), duration=duration))
        rows = [(self._button(t("button_back_classroom"), callback_data=LMSBotCallbackVO.classroom(classroom.course.id)),)]
        return LMSBotScreenDTO(text="\n".join(lines), keyboard=tuple(rows))

    def assignments_screen(self, *, user, course_id, language: str, app_url: str = "") -> LMSBotScreenDTO:
        classroom = self._classroom(user, course_id)
        t = lambda key, **kwargs: LMSBotTextVO.get(language, key, **kwargs)
        lines = [t("assignments_title", title=html.escape(classroom.course.title))]
        visible = list(classroom.assignments[:12])
        if not visible:
            lines.append(t("assignments_empty"))
        type_keys = {"exercise": "type_exercise", "project": "type_project", "quiz": "type_quiz", "other": "type_other"}
        for assignment in visible:
            submission = classroom.submissions_by_assignment.get(assignment.id)
            if isinstance(submission, list):
                submission_text = t("submission_count", count=len(submission))
            elif submission:
                submission_text = t(f"submission_status_{submission.status}")
            else:
                submission_text = t("not_submitted")
            due = self._format_deadline(assignment.due_at, t("no_deadline"))
            lines.append(t(
                "assignment_item", icon=LMSBotVisualVO.PROJECT if assignment.assignment_type == "project" else LMSBotVisualVO.ASSIGNMENT,
                title=html.escape(assignment.title), kind=t(type_keys.get(assignment.assignment_type, "type_other")),
                due=due, submission=submission_text,
            ))
        web_url = self._app_url(app_url, LMSBotWebPathVO.INSTRUCTOR.format(slug=classroom.course.slug) if classroom.is_instructor else LMSBotWebPathVO.CLASSROOM.format(slug=classroom.course.slug))
        rows = []
        if web_url:
            rows.append((self._button(t("button_instructor_web") if classroom.is_instructor else t("button_open_web"), url=web_url),))
        rows.append((self._button(t("button_back_classroom"), callback_data=LMSBotCallbackVO.classroom(classroom.course.id)),))
        return LMSBotScreenDTO(text="\n\n".join(lines), keyboard=tuple(rows))

    def grades_screen(self, *, user, course_id, language: str, app_url: str = "") -> LMSBotScreenDTO:
        classroom = self._classroom(user, course_id)
        t = lambda key, **kwargs: LMSBotTextVO.get(language, key, **kwargs)
        lines = [t("grades_title", title=html.escape(classroom.course.title))]
        if classroom.is_instructor:
            lines.append(t("instructor_summary", students=len(classroom.students), lessons=len(classroom.lessons), assignments=len(classroom.assignments), questions=len(classroom.questions)))
        else:
            summary = classroom.grade_summary
            percentage = f" — {summary.percentage}%" if summary.percentage is not None else ""
            lines.append(t("grade_summary", earned=summary.earned, possible=summary.possible, percentage=percentage))
            graded_submissions = [item for item in classroom.submissions_by_assignment.values() if not isinstance(item, list) and item.score is not None]
            for submission in graded_submissions[:10]:
                lines.append(t("grade_item", title=html.escape(submission.assignment.title), score=submission.score, max_score=submission.assignment.max_score))
            for item in classroom.grade_items[:10]:
                lines.append(t("grade_item", title=html.escape(item.title), score=item.score, max_score=item.max_score))
            if not graded_submissions and not classroom.grade_items:
                lines.append(t("grades_empty"))
        rows = [(self._button(t("button_back_classroom"), callback_data=LMSBotCallbackVO.classroom(classroom.course.id)),)]
        return LMSBotScreenDTO(text="\n".join(lines), keyboard=tuple(rows))

    def questions_screen(self, *, user, course_id, language: str, app_url: str = "") -> LMSBotScreenDTO:
        classroom = self._classroom(user, course_id)
        t = lambda key, **kwargs: LMSBotTextVO.get(language, key, **kwargs)
        lines = [t("questions_title", title=html.escape(classroom.course.title))]
        if not classroom.questions:
            lines.append(t("questions_empty"))
        status_keys = {"open": "status_open", "answered": "status_answered", "closed": "status_closed"}
        for question in classroom.questions[:12]:
            lines.append(t("question_item", subject=html.escape(question.subject), status=t(status_keys.get(question.status, "status_open"))))
        web_url = self._app_url(app_url, LMSBotWebPathVO.INSTRUCTOR.format(slug=classroom.course.slug) if classroom.is_instructor else LMSBotWebPathVO.CLASSROOM.format(slug=classroom.course.slug))
        rows = []
        if web_url:
            rows.append((self._button(t("button_instructor_web") if classroom.is_instructor else t("button_open_web"), url=web_url),))
        rows.append((self._button(t("button_back_classroom"), callback_data=LMSBotCallbackVO.classroom(classroom.course.id)),))
        return LMSBotScreenDTO(text="\n".join(lines), keyboard=tuple(rows))
