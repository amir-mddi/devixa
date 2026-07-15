from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class SeoMetadataOverrideDTO:
    title: str | None = None
    description: str | None = None
    canonical_path: str | None = None
    image_path_or_url: str | None = None
    open_graph_type: str | None = None
    robots: str | None = None
    structured_data: Sequence[Mapping[str, Any]] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SeoMetadataDTO:
    title: str
    description: str
    canonical_url: str
    robots: str
    site_name: str
    locale: str
    open_graph_type: str
    image_url: str
    twitter_card: str
    structured_data_json: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SeoProjectDTO:
    display_name: str
    name: str
    description: str
    tagline: str
    email_domain: str
    contact_email: str
    support_email: str
    phone: str
    address: str
    working_hours: str
    github_url: str
    linkedin_url: str
    telegram_url: str
    instagram_url: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SeoProjectDTO":
        display_name = str(value.get("display_name") or value.get("name") or "").strip()
        name = str(value.get("name") or display_name).strip()

        return cls(
            display_name=display_name,
            name=name,
            description=str(value.get("description") or ""),
            tagline=str(value.get("tagline") or ""),
            email_domain=str(value.get("email_domain") or ""),
            contact_email=str(value.get("contact_email") or ""),
            support_email=str(value.get("support_email") or ""),
            phone=str(value.get("phone") or ""),
            address=str(value.get("address") or ""),
            working_hours=str(value.get("working_hours") or ""),
            github_url=str(value.get("github_url") or ""),
            linkedin_url=str(value.get("linkedin_url") or ""),
            telegram_url=str(value.get("telegram_url") or ""),
            instagram_url=str(value.get("instagram_url") or ""),
        )
