from __future__ import annotations

from typing import Protocol, Sequence

from backend.apps.common.web.seo.entities.seo_entities import SeoPageDefinitionEntity


class SeoPageDefinitionRepository(Protocol):
    def get_by_route_name(self, route_name: str | None) -> SeoPageDefinitionEntity | None: ...


class SeoContentRepository(Protocol):
    def list_public_courses(self) -> Sequence[object]: ...

    def list_public_articles(self) -> Sequence[object]: ...

    def list_learning_roadmaps(self) -> Sequence[object]: ...
