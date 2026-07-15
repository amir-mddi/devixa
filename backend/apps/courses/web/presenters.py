from __future__ import annotations

from decimal import Decimal, InvalidOperation

from backend.apps.billing.enums import CurrencyEnum
from backend.apps.common.project_config import get_project_name
from backend.apps.courses.enums import CourseLevelEnum
from backend.apps.courses.vo.roadmap_vo import (
    CourseWebCurrencyLabelVO,
    CourseWebLevelLabelVO,
    CourseWebPriceLabelVO,
    CourseWebTimeLabelVO,
    CourseWebTimeTextVO,
)


class CourseWebPresenter:
    @classmethod
    def level_label(cls, level: str) -> str:
        labels = {
            CourseLevelEnum.BEGINNER.value: CourseWebLevelLabelVO.BEGINNER.value,
            CourseLevelEnum.INTERMEDIATE.value: CourseWebLevelLabelVO.INTERMEDIATE.value,
            CourseLevelEnum.ADVANCED.value: CourseWebLevelLabelVO.ADVANCED.value,
            CourseLevelEnum.ALL_LEVELS.value: CourseWebLevelLabelVO.ALL_LEVELS.value,
        }
        return labels.get(level, CourseWebLevelLabelVO.ALL_LEVELS.value)

    @classmethod
    def duration_label(cls, duration_minutes: int | None) -> str:
        total_minutes = int(duration_minutes or 0)
        if total_minutes <= 0:
            return CourseWebTimeTextVO.NO_DURATION.value

        hours = total_minutes // CourseWebTimeLabelVO.MINUTES_IN_HOUR.value
        minutes = total_minutes % CourseWebTimeLabelVO.MINUTES_IN_HOUR.value

        if hours and minutes:
            return CourseWebTimeTextVO.HOUR_AND_MINUTE.value.format(hours=hours, minutes=minutes)
        if hours:
            return CourseWebTimeTextVO.HOUR.value.format(hours=hours)
        return CourseWebTimeTextVO.MINUTE.value.format(minutes=minutes)

    @classmethod
    def price_label(cls, price, currency: str) -> str:
        try:
            amount = Decimal(str(price or 0))
        except (InvalidOperation, TypeError, ValueError):
            amount = Decimal("0")

        if amount <= 0:
            return CourseWebPriceLabelVO.FREE.value

        normalized_currency = (currency or CurrencyEnum.IRR.value).lower()
        currency_label = (
            CourseWebCurrencyLabelVO.IRR.value
            if normalized_currency == CurrencyEnum.IRR.value
            else normalized_currency.upper()
        )
        return CourseWebPriceLabelVO.PAID.value.format(
            amount=f"{int(amount):,}",
            currency=currency_label,
        )

    @classmethod
    def instructor_label(cls, course) -> str:
        first_name = getattr(getattr(course, "instructor", None), "first_name", "") or ""
        last_name = getattr(getattr(course, "instructor", None), "last_name", "") or ""
        full_name = f"{first_name} {last_name}".strip()
        return full_name or getattr(getattr(course, "instructor", None), "username", "") or f"{CourseWebLevelLabelVO.DEFAULT_INSTRUCTOR.value} {get_project_name()}"
