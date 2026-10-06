from __future__ import annotations


class LMSBotCallbackVO:
    PREFIX = "lms:"
    CLASSROOM = "lms:c:{course_id}"
    LESSONS = "lms:l:{course_id}"
    ASSIGNMENTS = "lms:a:{course_id}"
    GRADES = "lms:g:{course_id}"
    QUESTIONS = "lms:q:{course_id}"
    COURSE_DETAIL = "c:d:{course_id}"
    SECTION_CLASSROOM = "classroom"
    SECTION_LESSONS = "lessons"
    SECTION_ASSIGNMENTS = "assignments"
    SECTION_GRADES = "grades"
    SECTION_QUESTIONS = "questions"
    SECTION_BY_CODE = {
        "c": SECTION_CLASSROOM,
        "l": SECTION_LESSONS,
        "a": SECTION_ASSIGNMENTS,
        "g": SECTION_GRADES,
        "q": SECTION_QUESTIONS,
    }

    @classmethod
    def classroom(cls, course_id) -> str:
        return cls.CLASSROOM.format(course_id=course_id)

    @classmethod
    def lessons(cls, course_id) -> str:
        return cls.LESSONS.format(course_id=course_id)

    @classmethod
    def assignments(cls, course_id) -> str:
        return cls.ASSIGNMENTS.format(course_id=course_id)

    @classmethod
    def grades(cls, course_id) -> str:
        return cls.GRADES.format(course_id=course_id)

    @classmethod
    def questions(cls, course_id) -> str:
        return cls.QUESTIONS.format(course_id=course_id)

    @classmethod
    def course_detail(cls, course_id) -> str:
        return cls.COURSE_DETAIL.format(course_id=course_id)

    @classmethod
    def parse(cls, data: str) -> tuple[str, str] | None:
        if not data.startswith(cls.PREFIX):
            return None
        parts = data.split(":", 2)
        if len(parts) != 3:
            return None
        section = cls.SECTION_BY_CODE.get(parts[1])
        if not section or not parts[2]:
            return None
        return section, parts[2]


class LMSBotTextVO:
    TEXTS = {
        "fa": {
            "login_required": "🔐 برای مشاهده کلاس، ابتدا حساب سایت را به بات متصل کنید.",
            "access_denied": "⛔ این کلاس فقط برای مدرس و هنرجویان ثبت‌نام‌شده قابل دسترسی است.",
            "classroom_title": "🏫 <b>کلاس {title}</b>",
            "classroom_summary": "پیشرفت: <b>{progress}%</b>\nدرس‌ها: <b>{completed}/{lessons}</b>\nتکالیف و پروژه‌ها: <b>{assignments}</b>\nپرسش‌ها: <b>{questions}</b>",
            "instructor_summary": "هنرجویان: <b>{students}</b>\nدرس‌ها: <b>{lessons}</b>\nتکالیف/پروژه‌ها: <b>{assignments}</b>\nپرسش‌های باز: <b>{questions}</b>",
            "lessons_title": "📚 <b>فهرست درس‌های {title}</b>",
            "lesson_item": "{state} <b>{position}. {title}</b>{duration}",
            "lesson_duration": " — {minutes} دقیقه",
            "lessons_empty": "هنوز درسی برای این کلاس منتشر نشده است.",
            "assignments_title": "📝 <b>تمرین‌ها و پروژه‌های {title}</b>",
            "assignment_item": "{icon} <b>{title}</b>\nنوع: {kind}\nمهلت: {due}\nوضعیت تحویل: <b>{submission}</b>",
            "assignments_empty": "در حال حاضر تمرین یا پروژه‌ای منتشر نشده است.",
            "no_deadline": "بدون مهلت",
            "not_submitted": "ارسال نشده",
            "submission_count": "{count} تحویل",
            "submission_status_draft": "پیش‌نویس",
            "submission_status_submitted": "تحویل‌شده",
            "submission_status_late": "تحویل با تأخیر",
            "submission_status_graded": "نمره‌گذاری‌شده",
            "submission_status_returned": "بازگردانده‌شده",
            "grades_title": "🏅 <b>نمرات {title}</b>",
            "grade_summary": "مجموع نمره: <b>{earned}/{possible}</b>{percentage}",
            "grade_item": "• {title}: <b>{score}/{max_score}</b>",
            "grades_empty": "هنوز نمره‌ای برای شما منتشر نشده است.",
            "questions_title": "💬 <b>پرسش‌ها و گفت‌وگوهای {title}</b>",
            "question_item": "• <b>{subject}</b> — {status}",
            "questions_empty": "هنوز گفت‌وگویی در این کلاس ثبت نشده است.",
            "button_classroom": "🏫 کلاس دوره",
            "button_lessons": "📚 درس‌ها",
            "button_assignments": "📝 تمرین و پروژه",
            "button_grades": "🏅 نمرات",
            "button_questions": "💬 پرسش از مدرس",
            "button_open_web": "🌐 باز کردن کلاس",
            "button_instructor_web": "🧑‍🏫 مدیریت کلاس",
            "button_back_course": "⬅️ صفحه دوره",
            "button_back_classroom": "⬅️ کلاس",
            "status_open": "باز",
            "status_answered": "پاسخ داده‌شده",
            "status_closed": "بسته",
            "type_exercise": "تمرین",
            "type_project": "پروژه",
            "type_quiz": "آزمون",
            "type_other": "فعالیت",
        },
        "en": {
            "login_required": "🔐 Link your website account before opening the classroom.",
            "access_denied": "⛔ This classroom is available only to the instructor and enrolled students.",
            "classroom_title": "🏫 <b>{title} classroom</b>",
            "classroom_summary": "Progress: <b>{progress}%</b>\nLessons: <b>{completed}/{lessons}</b>\nAssignments/projects: <b>{assignments}</b>\nQuestions: <b>{questions}</b>",
            "instructor_summary": "Students: <b>{students}</b>\nLessons: <b>{lessons}</b>\nAssignments/projects: <b>{assignments}</b>\nQuestions: <b>{questions}</b>",
            "lessons_title": "📚 <b>{title} lessons</b>",
            "lesson_item": "{state} <b>{position}. {title}</b>{duration}",
            "lesson_duration": " — {minutes} min",
            "lessons_empty": "No lesson has been published for this class yet.",
            "assignments_title": "📝 <b>{title} assignments & projects</b>",
            "assignment_item": "{icon} <b>{title}</b>\nType: {kind}\nDue: {due}\nSubmission: <b>{submission}</b>",
            "assignments_empty": "There are no published assignments or projects right now.",
            "no_deadline": "No deadline",
            "not_submitted": "Not submitted",
            "submission_count": "{count} submissions",
            "submission_status_draft": "Draft",
            "submission_status_submitted": "Submitted",
            "submission_status_late": "Submitted late",
            "submission_status_graded": "Graded",
            "submission_status_returned": "Returned",
            "grades_title": "🏅 <b>{title} grades</b>",
            "grade_summary": "Total: <b>{earned}/{possible}</b>{percentage}",
            "grade_item": "• {title}: <b>{score}/{max_score}</b>",
            "grades_empty": "No grade has been published yet.",
            "questions_title": "💬 <b>{title} questions</b>",
            "question_item": "• <b>{subject}</b> — {status}",
            "questions_empty": "No classroom conversation has been created yet.",
            "button_classroom": "🏫 Classroom",
            "button_lessons": "📚 Lessons",
            "button_assignments": "📝 Assignments",
            "button_grades": "🏅 Grades",
            "button_questions": "💬 Ask instructor",
            "button_open_web": "🌐 Open classroom",
            "button_instructor_web": "🧑‍🏫 Manage classroom",
            "button_back_course": "⬅️ Course",
            "button_back_classroom": "⬅️ Classroom",
            "status_open": "Open",
            "status_answered": "Answered",
            "status_closed": "Closed",
            "type_exercise": "Exercise",
            "type_project": "Project",
            "type_quiz": "Quiz",
            "type_other": "Activity",
        },
    }

    @classmethod
    def get(cls, language: str, key: str, **kwargs) -> str:
        language = language if language in cls.TEXTS else "en"
        value = cls.TEXTS[language].get(key, cls.TEXTS["en"].get(key, key))
        return value.format(**kwargs) if kwargs else value


class LMSBotVisualVO:
    LESSON_COMPLETE = "✅"
    LESSON_PENDING = "▫️"
    PROJECT = "🧩"
    ASSIGNMENT = "📝"


class LMSBotWebPathVO:
    CLASSROOM = "/courses/{slug}/classroom/"
    INSTRUCTOR = "/courses/{slug}/classroom/instructor/"
