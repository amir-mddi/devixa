from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence


@dataclass(frozen=True)
class CourseGradeSummaryEntity:
    assignment_earned: Decimal = Decimal("0")
    assignment_possible: Decimal = Decimal("0")
    manual_earned: Decimal = Decimal("0")
    manual_possible: Decimal = Decimal("0")

    @property
    def earned(self) -> Decimal:
        return self.assignment_earned + self.manual_earned

    @property
    def possible(self) -> Decimal:
        return self.assignment_possible + self.manual_possible

    @property
    def percentage(self) -> Decimal | None:
        if self.possible <= 0:
            return None
        return (self.earned / self.possible * Decimal("100")).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class CourseClassroomEntity:
    course: object
    is_instructor: bool
    is_student: bool
    sections: Sequence[object] = field(default_factory=tuple)
    lessons: Sequence[object] = field(default_factory=tuple)
    resources: Sequence[object] = field(default_factory=tuple)
    assignments: Sequence[object] = field(default_factory=tuple)
    submissions_by_assignment: dict = field(default_factory=dict)
    completed_lesson_ids: frozenset = field(default_factory=frozenset)
    announcements: Sequence[object] = field(default_factory=tuple)
    questions: Sequence[object] = field(default_factory=tuple)
    grade_items: Sequence[object] = field(default_factory=tuple)
    grade_summary: CourseGradeSummaryEntity = field(default_factory=CourseGradeSummaryEntity)
    students: Sequence[object] = field(default_factory=tuple)

    @property
    def total_lessons(self) -> int:
        return len(self.lessons)

    @property
    def completed_lessons(self) -> int:
        return len(self.completed_lesson_ids)

    @property
    def progress_percentage(self) -> int:
        if not self.total_lessons:
            return 0
        return round((self.completed_lessons / self.total_lessons) * 100)
