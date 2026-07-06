from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class CourseCategoryFilterDTO:
    value: str
    label: str


@dataclass(frozen=True)
class CourseCatalogDTO:
    courses: Sequence[object]
    categories: Sequence[CourseCategoryFilterDTO]
    selected_category: str
    selected_level: str
    search: str

    @property
    def total_count(self) -> int:
        return len(self.courses)


@dataclass(frozen=True)
class CourseDetailPageDTO:
    course: object
    reviews: Sequence[object] = field(default_factory=tuple)
    related_courses: Sequence[object] = field(default_factory=tuple)
