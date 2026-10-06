from __future__ import annotations

from django import template
from django.utils.timezone import now

register = template.Library()


@register.filter
def lms_dict_get(mapping, key):
    if not mapping:
        return None
    return mapping.get(key)


@register.filter
def lms_assignment_type(value):
    return {
        "exercise": "تمرین",
        "project": "پروژه",
        "quiz": "آزمون",
        "other": "فعالیت",
    }.get(str(value), "فعالیت")


@register.filter
def lms_submission_status(value):
    return {
        "draft": "پیش‌نویس",
        "submitted": "تحویل‌شده",
        "late": "تحویل دیرهنگام",
        "graded": "نمره‌گذاری‌شده",
        "returned": "نیازمند اصلاح",
    }.get(str(value), str(value or "—"))


@register.filter
def lms_question_status(value):
    return {"open": "باز", "answered": "پاسخ داده‌شده", "closed": "بسته"}.get(str(value), str(value or "—"))


@register.filter
def lms_is_overdue(assignment):
    return bool(getattr(assignment, "due_at", None) and now() > assignment.due_at)


@register.filter
def lms_can_submit(assignment):
    current = now()
    if getattr(assignment, "status", "") != "published":
        return False
    starts_at = getattr(assignment, "starts_at", None)
    due_at = getattr(assignment, "due_at", None)
    if starts_at and current < starts_at:
        return False
    if due_at and current > due_at and not getattr(assignment, "allow_late_submission", False):
        return False
    return True
