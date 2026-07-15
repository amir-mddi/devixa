from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleTypeFilterEntity:
    value: str
    label: str
    icon: str
    reverse_name: str
