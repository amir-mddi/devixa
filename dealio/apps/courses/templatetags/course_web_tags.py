from __future__ import annotations

from django import template

from dealio.apps.courses.web.presenters import CourseWebPresenter

register = template.Library()


@register.filter
def course_level_label(value: str) -> str:
    return CourseWebPresenter.level_label(value)


@register.filter
def course_duration_label(value: int | None) -> str:
    return CourseWebPresenter.duration_label(value)


@register.filter
def course_price_label(course) -> str:
    return CourseWebPresenter.price_label(
        getattr(course, "price", 0),
        getattr(course, "currency", ""),
    )


@register.filter
def course_instructor_label(course) -> str:
    return CourseWebPresenter.instructor_label(course)
