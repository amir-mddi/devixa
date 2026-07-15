from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class RoadmapStepDTO:
    number: int
    title: str
    description: str
    duration: str
    topics: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class RoadmapSkillDTO:
    title: str
    description: str
    icon_class: str


@dataclass(frozen=True)
class RoadmapProjectDTO:
    title: str
    description: str


@dataclass(frozen=True)
class CourseRoadmapDTO:
    slug: str
    title: str
    category: str
    category_label: str
    description: str
    level: str
    duration_weeks: int
    icon_class: str
    steps: Sequence[RoadmapStepDTO]
    skills: Sequence[RoadmapSkillDTO]
    projects: Sequence[RoadmapProjectDTO]
    related_course_search_terms: Sequence[str] = field(default_factory=tuple)

    @property
    def duration_label(self) -> str:
        return f"{self.duration_weeks} هفته"


@dataclass(frozen=True)
class CourseRoadmapCatalogDTO:
    roadmaps: Sequence[CourseRoadmapDTO]
    selected_category: str
    search: str

    @property
    def total_count(self) -> int:
        return len(self.roadmaps)


@dataclass(frozen=True)
class CourseRoadmapDetailDTO:
    roadmap: CourseRoadmapDTO
    related_courses: Sequence[object]
