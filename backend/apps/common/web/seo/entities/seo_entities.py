from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SeoPageDefinitionEntity:
    route_name: str
    title_template: str
    description_template: str
    indexable: bool = True
    open_graph_type: str = "website"


@dataclass(frozen=True, slots=True)
class SeoStructuredDataEntity:
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SeoSitemapUrlEntity:
    location: str
    last_modified: date | datetime | None = None
    change_frequency: str = "weekly"
    priority: float = 0.5
