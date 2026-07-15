from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HomeTestimonialDTO:
    comment: str
    student_name: str
    student_role: str


@dataclass(frozen=True)
class HomeFaqDTO:
    question: str
    answer: str


@dataclass(frozen=True)
class ChannelLinkDTO:
    title: str
    description: str
    url: str
    icon_class: str
    badge: str

    @property
    def is_available(self) -> bool:
        normalized_url = (self.url or "").strip()
        return bool(normalized_url and normalized_url != "#")
